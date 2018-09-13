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
	after=tntapi.strip_namespaces(after)

	print("#1.1 - Verify all packets are forwarded to their destinations.")

	assert(delta["analyzer"]["ge0"].out_unicast_pkts>=1000000) #total-frames not always implemented
	assert(delta["analyzer"]["xe0"].in_unicast_pkts==delta["analyzer"]["ge0"].out_unicast_pkts)
	assert(delta["analyzer"]["xe1"].in_unicast_pkts==delta["analyzer"]["ge0"].out_unicast_pkts)
	assert(delta["analyzer"]["ge1"].in_unicast_pkts==delta["analyzer"]["ge0"].out_unicast_pkts)

	latency_to_xe0=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='xe0']/traffic-analyzer/testframe-stats/latency/min")[0].text
	latency_to_xe1=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='xe1']/traffic-analyzer/testframe-stats/latency/min")[0].text
	latency_to_ge1=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='ge1']/traffic-analyzer/testframe-stats/latency/min")[0].text

	return int(latency_to_xe0), int(latency_to_xe1), int(latency_to_ge1)


def validate_step_2_4(before, after, name):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        testsuiteapi.print_state(before, after)
	after=tntapi.strip_namespaces(after)

	print("#x.1 - Verify all packets are forwarded to their destinations.")

	assert(delta["analyzer"][name].out_unicast_pkts>=1000000) #total-frames not always implemented
	assert(delta["analyzer"]["ge0"].in_unicast_pkts==delta["analyzer"][name].out_unicast_pkts)

	latency_to_ge0=after.xpath("node[node-id='analyzer']/data/interfaces-state/interface[name='ge0']/traffic-analyzer/testframe-stats/latency/min")[0].text

	return int(latency_to_ge0)


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
      <name>ge0</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
        <frame-size>64</frame-size>
        <interframe-gap>1024</interframe-gap>
        <total-frames>1000000</total-frames>
        <ether-type xmlns="http://transpacket.com/ns/transpacket-traffic-generator-ethernet">88F7</ether-type>
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
      <name>ge0</name>
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
      <name>xe0</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
    <interface>
      <name>xe1</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
    <interface>
      <name>ge1</name>
      <traffic-analyzer xmlns="http://transpacket.com/ns/transpacket-traffic-analyzer" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete"></traffic-analyzer>
    </interface>
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

	state_after = tntapi.network_get_state(network, conns, filter=filter)
	return validate_step1(state_before, state_after)

def step_2_4(network, conns, filter, name):
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
	analyzer_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>%(name)s</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
        <frame-size>64</frame-size>
        <interframe-gap>%(interframe_gap)s</interframe-gap>
        <total-frames>1000000</total-frames>
        <ether-type xmlns="http://transpacket.com/ns/transpacket-traffic-generator-ethernet">88F7</ether-type>
      </traffic-generator>
    </interface>
  </interfaces>
</config>
"""%{'name':name, 'interframe_gap':10240 if name!='ge1' else 1024}
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

	time.sleep(10)

        print("Stop traffic ...")
	analyzer_config="""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>%(name)s</name>
      <traffic-generator xmlns="http://transpacket.com/ns/transpacket-traffic-generator" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">
      </traffic-generator>
    </interface>
  </interfaces>
</config>
"""%{'name':name} 
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
  </interfaces>
</config>
"""
	tntapi.edit_config(conns["analyzer"],analyzer_config)
	tntapi.network_commit(conns)

	state_after = tntapi.network_get_state(network, conns, filter=filter)
	return validate_step_2_4(state_before, state_after, name)

def step_2(network, conns, filter=filter):
	return step_2_4(network, conns, filter, "xe0")

def step_3(network, conns, filter=filter):
	return step_2_4(network, conns, filter, "xe1")

def step_4(network, conns, filter=filter):
	return step_2_4(network, conns, filter, "ge1")


def main():
	print("""
<test-spec>
===Objective===
Delay symmetry requirements test. Validate the forward and return paths master-slave are symmetric in terms of delay for all possible master-slave traffic paths.
===Procedure===
Generate point-to-point packet streams with TPID=88F7. There should be enough interframe gap to avoid contention and validate zero packet loss.
===DUT configuration===
This testcase is using the [[VCU-110_Prototype_r1.6#FPGA_Setup]] configuration and it is not changed during the test.

====Steps====
# Generate timing critical stream of 1000000 64 octet packets and 1024 octet interframe gaps from timing master (analyzer.ge0) and measure the min and max latencies at the timing slave ports (analyzer.xe0,xe1,analyzer.ge1)
## Assert delta["analyzer"]["ge0"].out_unicast_pkts>=1000000
## Assert delta["analyzer"]["xe0"].in_unicast_pkts==delta["analyzer"]["ge0"].out_unicast_pkts
## Assert delta["analyzer"]["xe1"].in_unicast_pkts==delta["analyzer"]["ge0"].out_unicast_pkts
## Assert delta["analyzer"]["ge1"].in_unicast_pkts==delta["analyzer"]["ge0"].out_unicast_pkts
## Return lat_ge0_xe[0-1]_min, lat_ge0_ge1_min - Minimum latencies from ge0 to xe0, xe1, ge1.
# Generate timing critical stream of 1000000 64 octet packets and 10240 octet interframe gaps from timing slave (analyzer.xe0) and measure the min and max latencies at the timing master port (analyzer.ge0)
## Assert delta["analyzer"][name].out_unicast_pkts>=1000000.
## Assert delta["analyzer"]["ge0"].in_unicast_pkts==delta["analyzer"]["xe0"].out_unicast_pkts.
## Return lat_xe0_ge0_min - Minimum latency measured from xe0 to ge0
# Same as Step 2 for xe1.
# Same as Step 2 for ge1 and generate interframe gap of 1024 octets instead of 10240.

===Results===
# Local,Remote,Remote NP0  abs-[to/from]-delay - absolute delay for the forward path from timing master to local slave.
# Local,Remote,Remote NP0 asymmetry-delta-delay - difference between the to and from paths.

===Acceptance criteria===
# abs(lat_ge0_xe0_min-lat_xe0_ge0_min)<500)
# abs(lat_ge0_xe1_min-lat_xe1_ge0_min)<500)
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
	(lat_ge0_xe0_min, lat_ge0_xe1_min, lat_ge0_ge1_min)=step_1(network, conns, filter=filter)
	lat_xe0_ge0_min=step_2(network, conns, filter=filter)
	lat_xe1_ge0_min=step_3(network, conns, filter=filter)
	lat_ge1_ge0_min=step_4(network, conns, filter=filter)

        print("# Test report:")
        print("# Local edge port: abs-to-delay=%(to)d ns, abs-from-delay=%(from)d ns, asymmetry-delta-delay=%(delta)d ns"%{'to':lat_ge0_xe0_min,'from':lat_xe0_ge0_min,'delta':abs(lat_ge0_xe0_min-lat_xe0_ge0_min)})
        print("# Remote edge port: abs-to-delay=%(to)d ns, abs-from-delay=%(from)d ns, asymmetry-delta-delay=%(delta)d ns"%{'to':lat_ge0_xe1_min,'from':lat_xe1_ge0_min,'delta':abs(lat_ge0_xe1_min-lat_xe1_ge0_min)})
        print("# Remote network 0: abs-to-delay=%(to)d ns, abs-from-delay=%(from)d ns, asymmetry-delta-delay=%(delta)d ns"%{'to':lat_ge0_ge1_min,'from':lat_ge1_ge0_min,'delta':abs(lat_ge0_ge1_min-lat_ge1_ge0_min)})

	#Acceptance criteria
	assert(abs(lat_ge0_xe0_min-lat_xe0_ge0_min)<500)
	assert(abs(lat_ge0_xe1_min-lat_xe1_ge0_min)<500)

sys.exit(main())
