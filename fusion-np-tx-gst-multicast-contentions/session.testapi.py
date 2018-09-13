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

namespaces={"nc":"urn:ietf:params:xml:ns:netconf:base:1.0",
	"nd":"urn:ietf:params:xml:ns:yang:ietf-network",
	"if":"urn:ietf:params:xml:ns:yang:ietf-interfaces"}

def validate_init(before, after):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        testsuiteapi.print_state(before, after)
	after = tntapi.strip_namespaces(after)

	#validate no counters were incremented
	for node in {"analyzer"}:
		for if_name in {"ge0", "ge1", "xe0", "xe1"}:
			interface = delta[node][if_name]
			for v in dir(interface):
				if not v[0].startswith('_') and not v=='count' and not v=='index':
					value = getattr(interface,v)
					if(value!=None and value!=0):
						print node + ":" + if_name + "." + v + "=" + str(value)
						assert(0)
	for node in {"local", "remote"}:
		for if_name in {"xe0", "ge15", "ge0"}:
			interface = delta[node][if_name]
			for v in dir(interface):
				if not v[0].startswith('_') and not v=='count' and not v=='index':
					value = getattr(interface,v)
					if(value!=None and value!=0):
						print node + ":" + if_name + "." + v + "=" + str(value)
						assert(0)



def validate_step1(before, after):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        testsuiteapi.print_state(before, after)

	print("#1.1 - Asserts for step_1.")

	assert(delta["analyzer"]["xe0"].out_unicast_pkts>=1000000)
	assert(delta["analyzer"]["xe1"].out_unicast_pkts>=1000000)
	assert(delta["analyzer"]["ge0"].in_unicast_pkts>=1000000)
	assert(delta["local"]["ge0"].fusion_ep_to_np0_gst_multicast_contentions==0)
#	assert(delta["analyzer"]["ge0"].in_unicast_pkts==delta["analyzer"]["xe0"].out_unicast_pkts+delta["analyzer"]["xe1"].out_unicast_pkts-delta["local"]["ge15"].fusion_np_tx_gst_multicast_contentions)


	#latency_to_xe0=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='xe0']/traffic-analyzer/testframe-stats/latency/min")[0].text

	local_pkts_sent=delta["analyzer"]["xe0"].out_unicast_pkts
	remote_pkts_sent=delta["analyzer"]["xe1"].out_unicast_pkts
	total_pkts_received=delta["analyzer"]["ge0"].in_unicast_pkts
	contentions=delta["local"]["ge15"].fusion_np_tx_gst_multicast_contentions
	return local_pkts_sent, remote_pkts_sent, total_pkts_received, contentions

def init(network, conns, filter=filter):
	idle_config_analyzer = """
  <config>
    <hadm xmlns="http://transpacket.com/ns/hadm" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
    </hadm>
    <vlans xmlns="http://transpacket.com/ns/hadm1-vlans" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
    </vlans>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>xe0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>

      </interface>
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>xe1</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>ge0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
	<ethernet xmlns="urn:ieee:params:xml:ns:yang:ethernet">
          <auto-negotiation>
            <status>enabled</status>
          </auto-negotiation>
        </ethernet>
      </interface>
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>ge1</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
	<ethernet xmlns="urn:ieee:params:xml:ns:yang:ethernet">
          <auto-negotiation>
            <status>enabled</status>
          </auto-negotiation>
        </ethernet>
      </interface>
    </interfaces>
  </config>
"""

        tntapi.edit_config(conns["analyzer"],idle_config_analyzer)
        #tntapi.edit_config(conns["local"],idle_config_local)
        #tntapi.edit_config(conns["remote"],idle_config_remote)
        tntapi.network_commit(conns)
	state_before = tntapi.network_get_state(network, conns, filter=filter)
	time.sleep(5)
	state_after = tntapi.network_get_state(network, conns, filter=filter)
	validate_init(state_before, state_after)

def step_1(network, conns, filter):
	state_before = tntapi.network_get_state(network, conns, filter=filter)

        print("Enable analyzers ...")
	analyzer_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>ge0</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create"></traffic-analyzer>
    </interface>
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

        print("Start traffic ...")
	generator_if="""
    <interface>
      <name>%(name)s</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
        <frame-size>64</frame-size>
        <interframe-gap>%(interframe_gap)s</interframe-gap>
        <total-frames>1000000</total-frames>
        <ether-type xmlns="http://transpacket.com/ns/transpacket-traffic-generator-ethernet">88F7</ether-type>
      </traffic-generator>
    </interface>
"""

	generator_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  %(xe0)s
  %(xe1)s
  </interfaces>
</config>
"""%{'xe0':generator_if%{'name':"xe0", 'interframe_gap':640}, 'xe1':generator_if%{'name':"xe1", 'interframe_gap':640}}

	tntapi.edit_config(conns["analyzer"],generator_config)
	tntapi.network_commit(conns)

	time.sleep(10)

        print("Stop traffic ...")
	generator_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>xe0</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">
      </traffic-generator>
    </interface>
    <interface>
      <name>xe1</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">
      </traffic-generator>
    </interface>
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],generator_config)
	tntapi.network_commit(conns)

        print("Disable analyzers ...")
	analyzer_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>ge0</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

	state_after = tntapi.network_get_state(network, conns, filter=filter)
	return validate_step1(state_before, state_after)

def main():
	print("""
<test-spec>
===Objective===
Test validating fusion-np-tx-gst-multicast-contentions counter registers all GST packets lost due to contention.
===Procedure===
Generate point-to-point packet streams with TPID=88F7 from both local.ep0 and remote.ep0 to local.n0. Each stream should be above the 50% throughput limit of n0 (1Gb) so that packet loss due to contention is guaranteed to happen.
===DUT configuration===
This testcase is using the [[VCU-110_Prototype_r1.6#FPGA_Setup]] configuration and it is not changed during the test.

====Steps====
# Generate timing critical stream of 1000000 64 octet packets and 640 octet interframe gaps from timing slaves (analyzer.xe0, analyzer.xe1)
## Assert delta["analyzer"]["xe0"].out_unicast_pkts>=1000000
## Assert delta["analyzer"]["xe1"].out_unicast_pkts>=1000000
## Assert delta["analyzer"]["ge0"].in_unicast_pkts>=1000000
## Assert delta["analyzer"]["ge0"].in_unicast_pkts==delta["analyzer"]["xe0"].out_unicast_pkts+delta["analyzer"]["xe1"].out_unicast_pkts-delta["local"]["ge15"].fusion_np_tx_gst_multicast_contentions
## Return local_pkts_sent - delta["analyzer"]["xe0"].out_unicast_pkts
## Return remote_pkts_sent - delta["analyzer"]["xe1"].out_unicast_pkts
## Return total_pkts_received - delta["analyzer"]["ge0"].in_unicast_pkts
## Return contentions - delta["local"]["ge15"].fusion_np_tx_gst_multicast_contentions

===Results===
# N.A.
===Acceptance criteria===
# assert((local_pkts_sent+remote_pkts_sent-total_pkts_received)==contentions)

</test-spec>
""")

	parser = argparse.ArgumentParser()
	parser.add_argument("--config", help="Path to the netconf configuration *.xml file defining the configuration according to ietf-networks, ietf-networks-topology and netconf-node models e.g. ../networks.xml")
	args = parser.parse_args()


	tree=etree.parse(args.config)
	network = tree.xpath('/nc:config/nd:networks/nd:network', namespaces=namespaces)[0]

	conns = tntapi.network_connect(network)
	mylinks = tntapi.parse_network_links(network)

	filter = testsuiteapi.get_filter()


        init(network, conns, filter=filter)
	(local_pkts_sent, remote_pkts_sent, total_pkts_received, contentions)=step_1(network, conns, filter=filter)

        print("# Test report:")
	print("local-pkts-sent=%(local_pkts_sent)d, remote-pkts-sent=%(remote_pkts_sent)d, total-pkts-received=%(total_pkts_received)d, contentions=%(contentions)d"%{'local_pkts_sent':local_pkts_sent, 'remote_pkts_sent':remote_pkts_sent, 'total_pkts_received':total_pkts_received, 'contentions':contentions})

	#Acceptance criteria
	assert((local_pkts_sent+remote_pkts_sent-total_pkts_received)==contentions)
sys.exit(main())
