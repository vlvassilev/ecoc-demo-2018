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
	"if":"urn:ietf:params:xml:ns:yang:ietf-interfaces",
	"netconf-node":"urn:tntapi:netconf-node"}

def validate_step_1(before, after):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

	testsuiteapi.print_state(before, after)

	print("#1.1 - Validate all analyzer interfaces have oper-status=up.")
	for node in {"local", "remote"}:
		for if_name in {"xe0", "ge15", "ge0"}:
			interface = delta[node][if_name]
			for v in dir(interface):
				if not v[0].startswith('_') and not v=='count' and not v=='index':
					value = getattr(interface,v)
					if(value!=None and value!=0):
						print node + ":" + if_name + "." + v + "=" + str(value)
						assert(0)
	for node in {"middle"}:
		for if_name in {"ge0", "ge1", "xe0", "xe1"}:
			interface = delta[node][if_name]
			for v in dir(interface):
				if not v[0].startswith('_') and not v=='count' and not v=='index':
					value = getattr(interface,v)
					if(value!=None and value!=0):
						print node + ":" + if_name + "." + v + "=" + str(value)
						assert(0)
 

def step_1(network, conns, filter=filter):
	idle_config_h100_1dot6 = """
  <config>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
      <interface>
        <name>xe0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface>
        <name>ge15</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface>
        <name>ge0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
    </interfaces>
    <fusion-streams xmlns="http://transpacket.com/ns/transpacket-fusion-streams" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
    </fusion-streams>
  </config>
"""

	idle_config_h100_1dot0 = """
  <config>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" nc:operation="replace"/>
    <vlans xmlns="http://transpacket.com/ns/hadm1-vlans" nc:operation="replace"/>
    <hadm xmlns="http://transpacket.com/ns/hadm" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace"/>
  </config>
"""

        tntapi.edit_config(conns["local"],idle_config_h100_1dot6)
        tntapi.edit_config(conns["remote"],idle_config_h100_1dot6)
        tntapi.edit_config(conns["middle"],idle_config_h100_1dot0)
        tntapi.network_commit(conns)
	state_before = tntapi.network_get_state(network, conns, filter=filter)
	time.sleep(2)
	state_after = tntapi.network_get_state(network, conns, filter=filter)
	validate_step_1(state_before, state_after)

def main():
	print("""
#Description: Setup idle
#Procedure:
#1 - Make sure there are no fusion streams configured on the local and remote h100 and all interfaces are in idle configuration.
#1.1 - Validate all analyzer interfaces have oper-status=up.
#1.2 - Validate no counters are being incremented.
""")

	parser = argparse.ArgumentParser()
	parser.add_argument("--config", help="Path to the netconf configuration *.xml file defining the configuration according to ietf-networks, ietf-networks-topology and netconf-node models e.g. ../networks.xml")
	args = parser.parse_args()


	tree=etree.parse(args.config)
	network = tree.xpath('/nc:config/nd:networks/nd:network', namespaces=namespaces)[0]

	conns = tntapi.network_connect(network)
	mylinks = tntapi.parse_network_links(network)

	filter = testsuiteapi.get_filter()

	print("#Running ...")
	print("#1 - Make sure there are no fusion streams configured on the local and remote h100 and all interfaces are in idle configuration.")
        step_1(network, conns, filter=filter)
 
sys.exit(main())
