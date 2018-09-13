#!/usr/bin/python

from lxml import etree
import time
import sys, os
import argparse
import tntapi

namespaces={"nc":"urn:ietf:params:xml:ns:netconf:base:1.0",
	"nd":"urn:ietf:params:xml:ns:yang:ietf-network"}

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--config", help="Path to the netconf configuration *.xml file defining the configuration according to ietf-networks, ietf-networks-topology and netconf-node models e.g. ../networks.xml")
	args = parser.parse_args()

	tree=etree.parse(args.config)

	network = tree.xpath('/nc:config/nd:networks/nd:network', namespaces=namespaces)[0]
	conns = tntapi.network_connect(network)

	if(conns != None):
		return(0)
	else:
		print("Problem!")
		return(-1)

sys.exit(main())

