#!/usr/bin/python
import lxml
from lxml import etree
import time
import sys, os
import argparse
from collections import namedtuple
import tntapi
sys.path.append("../common")
import testsuiteapi
import yangrpc
from yangcli import yangcli

namespaces={"nc":"urn:ietf:params:xml:ns:netconf:base:1.0",
	"nd":"urn:ietf:params:xml:ns:yang:ietf-network",
	"if":"urn:ietf:params:xml:ns:yang:ietf-interfaces"}

def yangcli_ok_script(yconn, yangcli_script):
	for line in yangcli_script.splitlines():
		line=line.strip()
		if not line:
			continue
		print("Executing: "+line)
		ok = yangcli(yconn, line).xpath('./ok')
        	assert(len(ok)==1)

def validate_step_common(before, after, step, with_sm, with_gst):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        testsuiteapi.print_state(before, after)
        after=tntapi.strip_namespaces(after)

	print("#1.1 - Asserts for step_%d."%(step))
	if(with_sm):
		assert(delta["analyzer"]['xe0'].testframe_payload_errors==0)
		latency_min=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='xe0']/traffic-analyzer/testframe-stats/latency/min")[0].text
		latency_max=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='xe0']/traffic-analyzer/testframe-stats/latency/max")[0].text

		pdv=int(latency_max)-int(latency_min)
		print("SM LAT_MIN=%d ns"%(int(latency_min)))
		print("SM LAT_MAX=%d ns"%(int(latency_max)))
		print("SM PDV=%d ns"%(pdv))

		assert(delta["analyzer"]['xe0'].out_pkts>=1000000)
		sum=0;
		for interface in {"ge0", "ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9"}:
			sum=sum+delta["local"][interface].fusion_ep_to_np1_sm_buf_overflows
			sum=sum+delta["local"][interface].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows
		print("sum(fusion_ep_to_np1_sm_buf_overflows+fusion_np1_to_ep_sm_drop_reinsert_buf_overflows)=%d"%(sum))
		if(step>=2):
			assert(delta["analyzer"]['xe0'].out_pkts==delta["analyzer"]['xe0'].in_pkts+sum)
			#assert(delta["analyzer"]['xe0'].testframe_sequence_errors==sum)
		else:
			assert(delta["analyzer"]['xe0'].out_pkts==delta["analyzer"]['xe0'].in_pkts)
			assert(sum==0)
			assert(delta["analyzer"]['xe0'].testframe_sequence_errors<=1)

	if(with_gst):
		assert(delta["analyzer"]['ge0'].testframe_payload_errors==0)
		assert(delta["analyzer"]['ge0'].out_pkts>=1000000)
		assert(delta["analyzer"]['ge0'].in_pkts>=1000000)
		assert((delta["analyzer"]['ge0'].in_pkts+delta["local"]['ge15'].fusion_np_tx_gst_multicast_contentions)==delta["analyzer"]['ge0'].out_pkts)
		sum=0;
		for interface in {"ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9"}:
			sum=sum+delta["local"][interface].fusion_ep_to_np0_gst_multicast_contentions

		print("sum(fusion_ep_to_np0_gst_multicast_contentions)=%d"%(sum))
		assert(step==2 or delta["analyzer"]['ge0'].out_pkts==(sum/(step-2)))
		latency_min=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='ge0']/traffic-analyzer/testframe-stats/latency/min")[0].text
		latency_max=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='ge0']/traffic-analyzer/testframe-stats/latency/max")[0].text
		pdv=int(latency_max)-int(latency_min)
		print("GST LAT_MIN=%d ns"%(int(latency_min)))
		print("GST LAT_MAX=%d ns"%(int(latency_max)))
		print("GST PDV=%d ns"%(pdv))
		assert(pdv<400)


	print("OK!")

def validate(network, conns, yconns, filter, step, with_sm, with_gst):

	if(with_sm):
		ok = yangcli(yconns["analyzer"], "create /interfaces/interface[name='xe0']/traffic-analyzer").xpath('./ok')
		assert(len(ok)==1)

	if(with_gst):
		ok = yangcli(yconns["analyzer"], "create /interfaces/interface[name='ge0']/traffic-analyzer").xpath('./ok')
		assert(len(ok)==1)

	tntapi.network_commit(conns)



	if(with_sm):
		ok = yangcli(yconns["analyzer"], "create /interfaces/interface[name='xe0']/traffic-generator -- frame-size=1500 interframe-gap=12 ether-type=8100 frames-per-burst=100 interburst-gap=10000").xpath('./ok')
		assert(len(ok)==1)

	if(with_gst):
		ok = yangcli(yconns["analyzer"], "create /interfaces/interface[name='ge0']/traffic-generator -- frame-size=64 interframe-gap=12 ether-type=88F7 frames-per-burst=100 interburst-gap=10000").xpath('./ok')
		assert(len(ok)==1)

	state_before = tntapi.network_get_state(network, conns, filter=filter)
	tntapi.network_commit(conns)

	print("Start traffic ...")

	time.sleep(10)

	print("Stop traffic ...")

	if(with_sm):
		ok = yangcli(yconns["analyzer"], "delete /interfaces/interface[name='xe0']/traffic-generator").xpath('./ok')
		assert(len(ok)==1)
	if(with_gst):
		ok = yangcli(yconns["analyzer"], "delete /interfaces/interface[name='ge0']/traffic-generator").xpath('./ok')
		assert(len(ok)==1)
	tntapi.network_commit(conns)

	state_after = tntapi.network_get_state(network, conns, filter=filter)

	if(with_sm):
		ok = yangcli(yconns["analyzer"], "delete /interfaces/interface[name='xe0']/traffic-analyzer").xpath('./ok')
		assert(len(ok)==1)
	if(with_gst):
		ok = yangcli(yconns["analyzer"], "delete /interfaces/interface[name='ge0']/traffic-analyzer").xpath('./ok')
		assert(len(ok)==1)
	tntapi.network_commit(conns)

	return validate_step_common(state_before, state_after, step, with_sm, with_gst)

def terminate(network, conns, yconns, filter):
	for name in {"local","remote"}:
		ok = yangcli(yconns[name], "delete /fusion-streams").xpath('./ok')
		ok = yangcli(yconns[name], "delete /interfaces").xpath('./ok')
        	#assert(len(ok)==1)

	tntapi.network_commit(conns)

def init(network, conns, yconns, filter):
	for name in {"local","remote"}:
		ok = yangcli(yconns[name], "delete /fusion-streams").xpath('./ok')
		ok = yangcli(yconns[name], "delete /interfaces").xpath('./ok')
        	#assert(len(ok)==1)

	for interface in {"xe0", "ge0"}:
		yangcli(yconns['analyzer'], "delete /interfaces/interface[name='%s']/traffic-generator"%(interface))
		yangcli(yconns['analyzer'], "delete /interfaces/interface[name='%s']/traffic-analyzer"%(interface))
		yangcli(yconns['analyzer'], "delete /interfaces/interface[name='%s']/loopback"%(interface))

	tntapi.network_commit(conns)

	for interface in {"xe0", "ge0"}:
		yangcli(yconns['analyzer'], "create /interfaces/interface[name='%s']/type value=ethernetCsmacd"%(interface))

	for interface in {"ge0"}:
		ok = yangcli(yconns['local'], "create /interfaces/interface[name='%s']/type value=ethernetCsmacd"%(interface)).xpath('./ok')
		assert(ok)

	for interface in {"ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9", "xe0"}:
		ok = yangcli(yconns['local'], "create /interfaces/interface[name='%s'] -- loopback=near-end"%(interface)).xpath('./ok')
		assert(ok)
		ok = yangcli(yconns['local'], "create /interfaces/interface[name='%s']/type value=ethernetCsmacd"%(interface)).xpath('./ok')
		assert(ok)


	tntapi.network_commit(conns)
	return


def step_1(network, conns, yconns, filter):
#TODO .. there is a hack adding and removing tags in n0 drop and forward ... without the hack packets are corrupted. To fix woth model constrain.
	yangcli_script='''
	create /fusion-streams/aggregation[in-port='e0'] -- out-port=n1 priority=sm push-vlan-tag/vlanid=101 push-vlan-tag/pcp=0 push-vlan-tag/tpid=8100 push-vlan-tag/cfi=1
	create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='101'] -- priority=sm filter/tpid=8100 drop[out-port='e0']/pop-vlan-tag=true
	create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='matched-tpid'] -- priority=gst filter/tpid=88F7 push-vlan-tag/vlanid=10 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 drop[out-port='e1']/pop-vlan-tag=true drop[out-port='e2']/pop-vlan-tag=true drop[out-port='e3']/pop-vlan-tag=true drop[out-port='e4']/pop-vlan-tag=true drop[out-port='e5']/pop-vlan-tag=true drop[out-port='e6']/pop-vlan-tag=true drop[out-port='e7']/pop-vlan-tag=true drop[out-port='e8']/pop-vlan-tag=true drop[out-port='e9']/pop-vlan-tag=true
'''
	yangcli_ok_script(yconns["local"], yangcli_script)
	tntapi.network_commit(conns)
	validate(network, conns, yconns, filter, 1, True, False)

	
def step_common(network, conns, yconns, filter, step):
	ep_index = step-1
	vlan_id=step+100

	yangcli_script='''
	replace /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='%(vlan_id_prev)d'] -- priority=sm filter/tpid=8100 drop[out-port='e%(ep_index)d']/pop-vlan-tag=true
        create /fusion-streams/aggregation[in-port='e%(ep_index)d'] -- sm/out-port=n1 sm/push-vlan-tag/vlanid=%(vlan_id)d sm/push-vlan-tag/pcp=0 sm/push-vlan-tag/tpid=8100 sm/push-vlan-tag/cfi=1 gst/out-port=n0  gst/filter/ether-type=88F7 gst/filter/tpid=8100 gst/filter/vlanid=1234
	create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='%(vlan_id)d'] -- priority=sm filter/tpid=8100 drop[out-port='e0']/pop-vlan-tag=true
'''%{'vlan_id_prev':vlan_id-1,'ep_index':ep_index,'vlan_id':vlan_id}
	yangcli_ok_script(yconns["local"], yangcli_script)
	tntapi.network_commit(conns)
	validate(network, conns, yconns, filter, step, True, True)


def main():
	print("""
<test-spec>
===Objective===
In iterrative steps reproduce the configuration example presented as part of the User Guide Complex Loopback Example
===Procedure===
Only the analyzer.ge0 (1G) and analyzer.xe0 (10G) generators are used. Note there is significant difference from the original userguide example. The 1G traffic is GST and the 10G generator is SM.
In itterative steps loopbacks are created so that the SM traffic forms a serpentine going through a loopback on each of the ge1-ge9 interfaces and the xe0 (n1) while GST is multicasted to all ge1-ge9 interfaces and after contention returned to the origin.
After each iterrative step the traffic generated should return with the corresponding traffic class properties.
===DUT configuration===
This testcase is enhancing the [[H100_r.1.6_NETCONF/YANG_usecase_examples_using_the_low_level_Fusion_core_model#Complex_loopback_example]] configuration by adding identical data paths for ge4-9 interfaces.

====Steps====
# Create near-end loopbacks on xe0 and ge0-9.
# Configure the DUT to aggregte ingress SM traffic from ep0 to np1 with vlan tag vlan-id=vlan_id_base(=100)+1 and forward ingress from np1 with vlan tag to ep0 after removing the tag.
## Generate traffic on ep0 and validate traffic returns without losses.
# Change the configuration so that ingress traffic on np1 with vlan tag is forwarded to ep1 instead of ep0. Create near-end loopback on ep1. Configure multiplexed sm/gst mode and forward ingress SM traffic to np1 with vlan-id=vlan_id_base+1 and forward the returning ingress traffic back to ep0.
##assert(delta["analyzer"]['xe0'].testframe_payload_errors==0)
##assert(delta["analyzer"]['xe0'].out_pkts>=1000000)
##assert(delta["analyzer"]['xe0'].out_pkts==delta["analyzer"]['xe0'].in_pkts+sum)
##assert(delta["analyzer"]['xe0'].out_pkts==delta["analyzer"]['xe0'].in_pkts)
##assert(delta["analyzer"]['xe0'].testframe_sequence_errors<=1)
##assert(delta["analyzer"]['ge0'].testframe_payload_errors==0)
##assert(delta["analyzer"]['ge0'].out_pkts>=1000000)
##assert(delta["analyzer"]['ge0'].in_pkts>=1000000)
##assert((delta["analyzer"]['ge0'].in_pkts+delta["local"]['ge15'].fusion_np_tx_gst_multicast_contentions)==delta["analyzer"]['ge0'].out_pkts)
##assert(step==2 or delta["analyzer"]['ge0'].out_pkts==(sum(delta["local"][interface].fusion_ep_to_np0_gst_multicast_contentions))/(step-2)))
##assert(gst_pdv<400)
# Repeat the previous step for all remaining ge2-9 ports.

===Results===
# N.A.
===Acceptance criteria===
# N.A.

</test-spec>
""")

	parser = argparse.ArgumentParser()
	parser.add_argument("--config", help="Path to the netconf configuration *.xml file defining the configuration according to ietf-networks, ietf-networks-topology and netconf-node models e.g. ../networks.xml")
	args = parser.parse_args()


	tree=etree.parse(args.config)
	network = tree.xpath('/nc:config/nd:networks/nd:network', namespaces=namespaces)[0]

	conns = tntapi.network_connect(network)
	yconns = tntapi.network_connect_yangrpc(network)
	mylinks = tntapi.parse_network_links(network)

	filter = testsuiteapi.get_filter()

	init(network, conns, yconns, filter)
	step_1(network, conns, yconns, filter)
	for step in range(1,10):
		step_common(network, conns, yconns, filter, step+1)
	terminate(network, conns, yconns, filter)
        #Test report
	#Acceptance criteria
sys.exit(main())
