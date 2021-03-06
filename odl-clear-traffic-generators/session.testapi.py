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
	"nt":"urn:ietf:params:xml:ns:yang:ietf-network-topology",
	"if":"urn:ietf:params:xml:ns:yang:ietf-interfaces"}

def main():
	print("""
#Description: Stop traffic generators
#Procedure:
#1 - Delete all traffic generator containers.
""")

	parser = argparse.ArgumentParser()
	parser.add_argument("--config", help="Path to the netconf configuration *.xml file defining the configuration according to ietf-networks, ietf-networks-topology and netconf-node models e.g. ../networks.xml")
	args = parser.parse_args()


	tree=etree.parse(args.config)
	network = tree.xpath('/nc:config/nd:networks/nd:network', namespaces=namespaces)[0]

	mylinks = tntapi.parse_network_links(network)


	print("#1 - Stop all traffic generators.")
	nodes = network.xpath('nd:node', namespaces=namespaces)
	for node in nodes:
		node_id = node.xpath('nd:node-id', namespaces=namespaces)[0].text
		config=""

		termination_points = node.xpath('./nt:termination-point', namespaces=namespaces)
		for termination_point in termination_points:
			tp_id = termination_point.xpath('nt:tp-id', namespaces=namespaces)[0].text
			os.system("""curl -X DELETE -H "Content-Type: application/json" -H "Accept: application/json" --user admin:admin http://localhost:8181/restconf/config/network-topology:network-topology/topology/topology-netconf/node/%s/yang-ext:mount/ietf-interfaces:interfaces/interface/%s/transpacket-traffic-generator:traffic-generator"""%(node_id, tp_id))


sys.exit(main())
