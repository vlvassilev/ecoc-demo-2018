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

def validate_step_common(before, after, step):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        testsuiteapi.print_state(before, after)
	after = tntapi.strip_namespaces(after)

	print("#1.1 - Asserts for step_%d."%(step))
	if(step==2):
		interfaces_off={"ge5", "ge6", "ge7", "ge8", "ge9"}
		interfaces_on={"ge0", "ge1", "ge2", "ge3", "ge4"}
	else:
		interfaces_off={}
		interfaces_on={"ge0", "ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9"}

	total_expected_xe0=0
	for if_name in interfaces_on:

		print("Checking on: " + if_name)
		assert(delta["remote"][if_name].out_pkts>=1000000)
		assert(delta["remote"][if_name].out_pkts==delta["remote"][if_name].in_pkts)
		assert((delta["remote"][if_name].in_pkts-delta["local"][if_name].out_pkts)==(delta["remote"][if_name].fusion_ep_to_np1_sm_buf_overflows+delta["local"][if_name].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows))
                if(step==2):
                    assert(delta["remote"][if_name].fusion_ep_to_np1_sm_buf_overflows>0)
                else:
                    assert(delta["remote"][if_name].fusion_ep_to_np1_sm_buf_overflows==0)

		total_expected_xe0=total_expected_xe0+delta["local"][if_name].out_pkts

	#assert(total_expected_xe0==delta["local"]["xe0"].out_pkts)

	for if_name in interfaces_off:
		print("Checking off: " + if_name)
		assert(delta["local"][if_name].out_pkts==0)

	print("Reults!")
	time.sleep(10)
def step_common(network, conns, filter, step):
	state_before = tntapi.network_get_state(network, conns, filter=filter)

#        print("Enable analyzers ...")
#	analyzer_config="""
#<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
#  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
#    <interface>
#      <name>ge0</name>
#      <traffic-analyzer xmlns="http://transpacket.com/ns/traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create"></traffic-analyzer>
#    </interface>
#  </interfaces>
#</config>
#"""
#	tntapi.edit_config(conns["analyzer"],analyzer_config)
#	tntapi.network_commit(conns)

        print("Create loopbacks ...")
	config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
"""

	for if_name in {"ge0", "ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9"}:
		config=config+"""
    <interface>
      <name>%(name)s</name>
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      <loopback xmlns="http://transpacket.com/ns/transpacket-loopback" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">near-end</loopback>
    </interface>
"""%{'name':if_name}

	config=config+"""
  </interfaces>
</config>
"""

	tntapi.edit_config(conns["remote"],config)
	tntapi.network_commit(conns)
	time.sleep(1)

        print("Start traffic ...")

	config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
"""

	if(step==2):
		sm_traffic_interfaces={"ge0","ge1","ge2","ge3","ge4"}
		gst_traffic_interfaces={"ge5","ge6","ge7","ge8","ge9"}
	else:
		sm_traffic_interfaces={"ge0", "ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9"}
		gst_traffic_interfaces={}

	for if_name in sm_traffic_interfaces:
		config=config+"""
    <interface>
      <name>%(name)s</name>
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
        <frame-size>1500</frame-size>
        <interframe-gap>12</interframe-gap>
        <total-frames>1000000</total-frames>
        <ether-type xmlns="http://transpacket.com/ns/transpacket-traffic-generator-ethernet">ABCD</ether-type>
      </traffic-generator>
    </interface>
"""%{'name':if_name}

	for if_name in gst_traffic_interfaces:
		config=config+"""
    <interface>
      <name>%(name)s</name>
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
        <frame-size>64</frame-size>
        <interframe-gap>12</interframe-gap>
        <total-frames>1000000</total-frames>
        <ether-type xmlns="http://transpacket.com/ns/transpacket-traffic-generator-ethernet">88F7</ether-type>
      </traffic-generator>
    </interface>
"""%{'name':if_name}

	config=config+"""
  </interfaces>
</config>
"""

	tntapi.edit_config(conns["remote"],config)
	tntapi.network_commit(conns)
	if(step==2):
		time.sleep(100)
	else:
		time.sleep(10)

        print("Stop traffic ...")
	config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
"""
	for if_name in sm_traffic_interfaces.union(gst_traffic_interfaces):
		config=config+"""
    <interface>
      <name>%(name)s</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"/>
    </interface>
"""%{'name':if_name}
	config=config+"""
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["remote"],config)
	tntapi.network_commit(conns)

	time.sleep(1)
        print("Remove loopbacks ...")
	config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
"""
	for if_name in {"ge0", "ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9"}:
		config=config+"""
    <interface>
      <name>%(name)s</name>
      <loopback xmlns="http://transpacket.com/ns/transpacket-loopback" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"/>
    </interface>
"""%{'name':if_name}
	config=config+"""
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["remote"],config)
	tntapi.network_commit(conns)

#        print("Disable analyzers ...")
#	analyzer_config="""
#<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
#  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
#    <interface>
#      <name>ge0</name>
#      <traffic-analyzer xmlns="http://transpacket.com/ns/traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
#    </interface>
#  </interfaces>
#</config>
#"""
#	tntapi.edit_config(conns["analyzer"],analyzer_config)
#	tntapi.network_commit(conns)

	state_after = tntapi.network_get_state(network, conns, filter=filter)
	return validate_step_common(state_before, state_after, step)

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

	tntapi.network_commit(conns)

	yangcli_script_local='''
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='matched-tpid'] -- priority=gst filter/tpid=88F7 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false drop[out-port='e0']/pop-vlan-tag=true drop[out-port='e1']/pop-vlan-tag=true drop[out-port='e2']/pop-vlan-tag=true drop[out-port='e3']/pop-vlan-tag=true drop[out-port='e4']/pop-vlan-tag=true drop[out-port='e5']/pop-vlan-tag=true drop[out-port='e6']/pop-vlan-tag=true drop[out-port='e7']/pop-vlan-tag=true drop[out-port='e8']/pop-vlan-tag=true drop[out-port='e9']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='unmatched'] -- priority=sm push-vlan-tag/vlanid=200 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='100'] -- priority=gst filter/tpid=9100 forward/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='200'] -- priority=sm filter/tpid=9100 forward/pop-vlan-tag=true
'''
	for i in range(10):
		yangcli_script_local=yangcli_script_local+'''
create /fusion-streams/aggregation[in-port='e%d']/sm -- out-port=n1 push-vlan-tag/vlanid=1%d push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e%d']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='1%d'] -- priority=sm filter/tpid=9100 drop[out-port='e%d']/pop-vlan-tag=true
'''%(i,i,i,i,i)


	yangcli_script_remote='''
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='matched-tpid'] -- priority=gst filter/tpid=88F7 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='unmatched'] -- priority=sm push-vlan-tag/vlanid=200 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='100'] -- priority=gst filter/tpid=9100 drop[out-port='e0']/pop-vlan-tag=true drop[out-port='e1']/pop-vlan-tag=true drop[out-port='e2']/pop-vlan-tag=true drop[out-port='e3']/pop-vlan-tag=true drop[out-port='e4']/pop-vlan-tag=true drop[out-port='e5']/pop-vlan-tag=true drop[out-port='e6']/pop-vlan-tag=true drop[out-port='e7']/pop-vlan-tag=true drop[out-port='e8']/pop-vlan-tag=true drop[out-port='e9']/pop-vlan-tag=true forward/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='200'] -- priority=sm filter/tpid=9100 forward/pop-vlan-tag=true
'''
	for i in range(10):

		yangcli_script_remote=yangcli_script_remote+'''
create /fusion-streams/aggregation[in-port='e%d']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e%d']/sm -- out-port=n1 push-vlan-tag/vlanid=1%d push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='1%d'] -- filter/tpid=9100 priority=sm drop[out-port='e%d']/pop-vlan-tag=true
''' % (i,i,i,i,i)

	yangcli_ok_script(yconns["local"], yangcli_script_local)
	yangcli_ok_script(yconns["remote"], yangcli_script_remote)
	tntapi.network_commit(conns)

def step_1(network, conns, filter):
	step_common(network, conns, filter, 1)

def step_2(network, conns, yconns, filter):
	step_common(network, conns, filter, 2)

def step_3(network, conns, filter):
	step_common(network, conns, filter, 3)

def main():
	print("""
<test-spec>
===Objective===
Test validating fusion-ep-to-np1-sm-buf-overflows counter registers all SM packets lost due to buffer overflows.
===Procedure===
Generate point-to-point packet streams with TPID=ABCD from remote.ep0-9 to local.ep0-9. Each stream should be as close as possible to the 100% throughput limit so that packet loss due to buf overflow is guaranteed to happen when GST stream with minimal length packets are enabled on remote.ge5-9.
===DUT configuration===
This testcase is enhancing the [[VCU-110_Prototype_r1.6#FPGA_Setup]] configuration by adding identical data paths for ge5-9 interfaces.

====Steps====
# Create near-end loopbacks and generate SM streams of 1500 octet packets and 12 octet interframe gaps from remote.ge0-4 and GST streams of 64 octet frames with 12 octet interframe gaps form remote remote.ge5-ge9
## Assert for name:ge0-4  delta["remot"][name].out_pkts==delta["remote"][name].in_pkts>=1000000
## Assert for name:ge0-4  delta["local"][name].out_pkts==delta["remote"][name].in_pkts
## Assert delta["remote"][name].fusion_ep_to_np1_sm_buf_overflows==0
# Identical to Step 2 but generate SM traffic on all interfaces
## Assert for name:ge0-4  delta["remot"][name].out_pkts==delta["remote"][name].in_pkts>=1000000
## Assert for name:ge0-4  delta["local"][name].out_pkts==delta["remote"][name].in_pkts-delta["remote"][name].fusion_ep_to_np1_sm_buf_overflows
# Repeat the first step.
===Results===
# N.A.
===Acceptance criteria===
# assert((local_pkts_received-remote_pkts_sent==sm_buf_overflows)

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

	init(network, conns, yconns, filter=filter)
	step_1(network, conns, filter=filter)
	step_2(network, conns, yconns, filter=filter)
	step_3(network, conns, filter=filter)
	terminate(network, conns, yconns, filter=filter)
        #Test report
	#Acceptance criteria
sys.exit(main())
fusion-ep-to-np1-sm-buf-overflowsfusion-ep-to-np1-sm-buf-overflowsfusion-ep-to-np1-sm-buf-overflows
