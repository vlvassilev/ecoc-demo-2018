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

def validate_step_1(before, after):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        testsuiteapi.print_state(before, after)
	after = tntapi.strip_namespaces(after)

	print("#1.1 - Validate all packets are received at their destinations.")

	assert(delta["analyzer"]["ge0"].in_unicast_pkts==0) #total-frames not always implemented
	assert(delta["analyzer"]["ge1"].in_unicast_pkts==0) #total-frames not always implemented
	assert(delta["analyzer"]["xe0"].out_unicast_pkts>=1000000)
	assert(delta["analyzer"]["xe1"].out_unicast_pkts>=1000000)
	assert(delta["analyzer"]["xe1"].out_unicast_pkts-delta["analyzer"]["xe0"].in_unicast_pkts == delta["local"]["ge0"].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows)
	assert(delta["analyzer"]["xe0"].out_unicast_pkts-delta["analyzer"]["xe1"].in_unicast_pkts == delta["remote"]["ge0"].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows)
        pkt_loss_remote_local=100*float(delta["analyzer"]["xe1"].out_unicast_pkts-delta["analyzer"]["xe0"].in_unicast_pkts)/delta["analyzer"]["xe1"].out_unicast_pkts
	print("pkt_loss_remote_local=%f"%(pkt_loss_remote_local))
	assert( pkt_loss_remote_local< 0.5)
        pkt_loss_local_remote=100*float(delta["analyzer"]["xe0"].out_unicast_pkts-delta["analyzer"]["xe1"].in_unicast_pkts)/delta["analyzer"]["xe0"].out_unicast_pkts
	print("pkt_loss_local_remote=%f"%(pkt_loss_local_remote))
	assert( pkt_loss_local_remote< 0.5)

	print("#1.2 - Validate there are no testframe payload errors and testframe sequence errors are <=1.")
	assert(delta["analyzer"]["xe0"].testframe_pkts==delta["analyzer"]["xe0"].in_unicast_pkts)
	assert(delta["analyzer"]["xe0"].testframe_sequence_errors<=(delta["local"]["ge0"].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows+1))
	assert(delta["analyzer"]["xe0"].testframe_payload_errors==0)
	assert(delta["analyzer"]["xe1"].testframe_pkts==delta["analyzer"]["xe1"].in_unicast_pkts)
	assert(delta["analyzer"]["xe1"].testframe_sequence_errors<=(delta["remote"]["ge0"].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows+1))
	assert(delta["analyzer"]["xe1"].testframe_payload_errors==0)

	return (pkt_loss_remote_local, pkt_loss_local_remote)


def step_1(network, conns, filter=filter):
	state_before = tntapi.network_get_state(network, conns, filter=filter)

        print("Enable analyzers ...")
	analyzer_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>xe0</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create"></traffic-analyzer>
    </interface>
    <interface>
      <name>xe1</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create"></traffic-analyzer>
    </interface>
    <interface>
      <name>ge0</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create"></traffic-analyzer>
    </interface>
    <interface>
      <name>ge1</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create"></traffic-analyzer>
    </interface>
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

        print("Start traffic ...")
	analyzer_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>xe0</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
        <frame-size>1500</frame-size>
        <interframe-gap>12</interframe-gap>
        <total-frames>1000000</total-frames>
        <ether-type xmlns="http://transpacket.com/ns/transpacket-traffic-generator-ethernet">ABCD</ether-type>
      </traffic-generator>
    </interface>
    <interface>
      <name>xe1</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
        <frame-size>1500</frame-size>
        <interframe-gap>12</interframe-gap>
        <total-frames>1000000</total-frames>
        <ether-type xmlns="http://transpacket.com/ns/transpacket-traffic-generator-ethernet">ABCD</ether-type>
      </traffic-generator>
    </interface>
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

	time.sleep(10)

        print("Stop traffic ...")
	analyzer_config="""
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
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

        print("Disable analyzers ...")
	analyzer_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>ge0</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
    <interface>
      <name>ge1</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
    <interface>
      <name>xe0</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
    <interface>
      <name>xe1</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

	state_after = tntapi.network_get_state(network, conns, filter=filter)
	return validate_step_1(state_before, state_after)


def main():
	print("""
<test-spec>
#Description: Bulk traffic test
#Procedure:
#1 - Generate bulk traffic stream of 1000000 1500 octet packets and 12 octet interframe gaps to both local.e0 and remote.e0 (analyzer.xe0,xe1)
#1.1 - Validate more that 99.5% of the packets are received at their destinations.
#1.2 - Validate there are no testframe payload errors.
===Objective===
Bulk traffic test. Send bidirectional SM traffic with maximal utilization between the local and remote node. 
===Procedure===
Generate point-to-point packet streams >1000000 frames with TPID=ABCD 1500 octet frames and 12 octets interframe gap. There should be zero packet loss.
===DUT configurations===
This testcase is depending on already loaded [[VCU-110_Prototype_r1.6#FPGA_Setup]] configuration and it is not modified during the test.

====Steps====
# Generate bidirectional bulk traffic stream of 1000000 1500 octet packets and 12 octet interframe gaps TPID=ABCD from-to local.e0 and remote.e0 (analyzer.xe0,xe1)
## Validate more that 99.5% of the packets are received at their destinations.
### Assert delta["analyzer"]["ge0"].in_unicast_pkts==0
### Assert delta["analyzer"]["ge1"].in_unicast_pkts==0
### Assert delta["analyzer"]["xe0"].out_unicast_pkts>=1000000
### Assert delta["analyzer"]["xe1"].out_unicast_pkts>=1000000
### Assert assert(delta["analyzer"]["xe1"].out_unicast_pkts-delta["analyzer"]["xe0"].in_unicast_pkts == delta["local"]["ge0"].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows)
### Assert assert(delta["analyzer"]["xe0"].out_unicast_pkts-delta["analyzer"]["xe1"].in_unicast_pkts == delta["remote"]["ge0"].fusion_np1_to_ep_sm_drop_reinsert_buf_overflows)
### Assert assert(100*float(delta["analyzer"]["xe1"].out_unicast_pkts-delta["analyzer"]["xe0"].in_unicast_pkts)/delta["analyzer"]["xe1"].out_unicast_pkts < 0.5)
## Validate there are no testframe payload errors.
### Assert delta["analyzer"]["xe0"].testframe_pkts==delta["analyzer"]["xe0"].in_unicast_pkts
### Assert delta["analyzer"]["xe0"].testframe_payload_errors==0
### Assert delta["analyzer"]["xe1"].testframe_pkts==delta["analyzer"]["xe1"].in_unicast_pkts
### Assert delta["analyzer"]["xe1"].testframe_payload_errors==0
===Acceptance criteria===
Step validations pass.
===Results===
# Packet loss Local->Remote
# Packet loss Remote->Local
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

	print("Running ...")
	print("#1 - Generate bulk traffic stream of 1000000 1500 octet packets and 12 octet interframe gaps to both local.e0 and remote.e0 (analyzer.xe0,xe1)")
	(pkt_loss_local_remote, pkt_loss_remote_local) = step_1(network, conns, filter=filter)

        print("# Test report:")
        print("# Packet loss: pkt_loss_local_remote=%(pkt_loss_local_remote)f, pkt_loss_remote_local=%(pkt_loss_remote_local)f"%{'pkt_loss_local_remote':pkt_loss_local_remote,'pkt_loss_remote_local':pkt_loss_remote_local})

sys.exit(main())
