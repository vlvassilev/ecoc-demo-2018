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

def step_1(network, conns, yconns, filter=filter):

#!
	yangcli_script_clear='''
merge /interfaces/interface[name='ge0'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge1'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge2'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge3'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge4'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge5'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge6'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge7'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge8'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge9'] -- type='ethernetCsmacd'
remove /interfaces/interface[name='ge0']/traffic-analyzer
remove /interfaces/interface[name='ge1']/traffic-analyzer
remove /interfaces/interface[name='ge2']/traffic-analyzer
remove /interfaces/interface[name='ge3']/traffic-analyzer
remove /interfaces/interface[name='ge4']/traffic-analyzer
remove /interfaces/interface[name='ge5']/traffic-analyzer
remove /interfaces/interface[name='ge6']/traffic-analyzer
remove /interfaces/interface[name='ge7']/traffic-analyzer
remove /interfaces/interface[name='ge8']/traffic-analyzer
remove /interfaces/interface[name='ge9']/traffic-analyzer
commit
'''

	yangcli_script_local='''
merge /interfaces/interface[name='ge0'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge1'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge2'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge3'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge4'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge5'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge6'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge7'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge8'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge9'] -- type='ethernetCsmacd'

replace /interfaces/interface[name='ge0']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge1']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge2']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge3']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge4']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge5']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge6']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge7']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge8']/traffic-analyzer -- direction=egress
replace /interfaces/interface[name='ge9']/traffic-analyzer -- direction=egress

merge /interfaces/interface[name='ge0']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge1']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge2']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge3']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge4']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge5']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge6']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge7']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge8']/traffic-analyzer/filter -- type=ethernet ether-type=1234
merge /interfaces/interface[name='ge9']/traffic-analyzer/filter -- type=ethernet ether-type=1234
'''

	yangcli_script_middle='''
merge /interfaces/interface[name='ge0'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge1'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge2'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge3'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge4'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge5'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge6'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge7'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge8'] -- type='ethernetCsmacd'
merge /interfaces/interface[name='ge9'] -- type='ethernetCsmacd'

replace /interfaces/interface[name='ge0']/traffic-analyzer
replace /interfaces/interface[name='ge1']/traffic-analyzer
replace /interfaces/interface[name='ge2']/traffic-analyzer
replace /interfaces/interface[name='ge3']/traffic-analyzer
replace /interfaces/interface[name='ge4']/traffic-analyzer
replace /interfaces/interface[name='ge5']/traffic-analyzer
replace /interfaces/interface[name='ge6']/traffic-analyzer
replace /interfaces/interface[name='ge7']/traffic-analyzer
replace /interfaces/interface[name='ge8']/traffic-analyzer
replace /interfaces/interface[name='ge9']/traffic-analyzer
'''
	yangcli_ok_script(yconns["local"], yangcli_script_clear)
	yangcli_ok_script(yconns["middle"], yangcli_script_clear)
	tntapi.network_commit(conns)

	yangcli_ok_script(yconns["local"], yangcli_script_local)
	yangcli_ok_script(yconns["middle"], yangcli_script_middle)
	tntapi.network_commit(conns)

def main():
	print("""
#Description: Stat traffic analyzers
#Procedure:
#1 - Start traffic analyzers on the local and middle h100 ge0-9 interfaces.
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
	print("#1 - Start traffic analyzers on the local and middle h100 ge0-9 interfaces.")
	step_1(network, conns, yconns, filter=filter)
 
sys.exit(main())
