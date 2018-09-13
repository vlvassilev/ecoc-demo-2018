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


	yangcli_script_remote='''
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

replace /interfaces/interface[name='ge0']/loopback value='near-end'
replace /interfaces/interface[name='ge1']/loopback value='near-end'
replace /interfaces/interface[name='ge2']/loopback value='near-end'
replace /interfaces/interface[name='ge3']/loopback value='near-end'
replace /interfaces/interface[name='ge4']/loopback value='near-end'
replace /interfaces/interface[name='ge5']/loopback value='near-end'
replace /interfaces/interface[name='ge6']/loopback value='near-end'
replace /interfaces/interface[name='ge7']/loopback value='near-end'
replace /interfaces/interface[name='ge8']/loopback value='near-end'
replace /interfaces/interface[name='ge9']/loopback value='near-end'
'''
	yangcli_ok_script(yconns["remote"], yangcli_script_remote)
	tntapi.network_commit(conns)


def main():
	print("""
#Description: Stat loopbacks
#Procedure:
#1 - Start loopbacks on the remote h100 ge0-9 interfaces.
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
	print("#1 - Start loopbacks on the remote h100 ge0-9 interfaces.")
	step_1(network, conns, yconns, filter=filter)
 
sys.exit(main())
