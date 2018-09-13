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
		result = yangcli(yconn, line)
		ok=result.xpath('./ok')
		if(len(ok)!=1):
			print lxml.etree.tostring(result)
			assert(0)

def validate_step_1(before, after):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

	testsuiteapi.print_state(before, after)

	print("#1.1 - Validate no counters are being incremented.")
	#validate no counters were incremented
	for node in {"local", "middle"}:
		for if_name in {"ge0", "ge1", "ge2", "ge3", "ge4", "ge5", "ge6", "ge7", "ge8", "ge9"}:
			interface = delta[node][if_name]
			for v in dir(interface):
				if not v[0].startswith('_') and not v=='count' and not v=='index':
					value = getattr(interface,v)
					if(value!=None and value!=0):
						print node + ":" + if_name + "." + v + "=" + str(value)
						assert(0)
 

def step_1(network, conns, yconns, filter=filter):


	yangcli_script_common='''
remove /interfaces/interface[name='ge0']/traffic-generator
remove /interfaces/interface[name='ge1']/traffic-generator
remove /interfaces/interface[name='ge2']/traffic-generator
remove /interfaces/interface[name='ge3']/traffic-generator
remove /interfaces/interface[name='ge4']/traffic-generator
remove /interfaces/interface[name='ge5']/traffic-generator
remove /interfaces/interface[name='ge6']/traffic-generator
remove /interfaces/interface[name='ge7']/traffic-generator
remove /interfaces/interface[name='ge8']/traffic-generator
remove /interfaces/interface[name='ge9']/traffic-generator
commit
'''

	yangcli_ok_script(yconns["local"], yangcli_script_common)
	yangcli_ok_script(yconns["middle"], yangcli_script_common)

	tntapi.network_commit(conns)
	state_before = tntapi.network_get_state(network, conns, filter=filter)
	time.sleep(5)
	state_after = tntapi.network_get_state(network, conns, filter=filter)
	validate_step_1(state_before, state_after)

def main():
	print("""
#Description: Stop traffic
#Procedure:
#1 - Stop traffic generators
#1.1 - Validate counters are not being incremented.
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


	print("#Running ...")
	print("#1 - Stop traffic generators")
	step_1(network, conns, yconns, filter=filter)
 
sys.exit(main())
