#!/usr/bin/python
import lxml
import time
import datetime
import sys, os
import argparse
from collections import namedtuple

sys.path.append("../../common")
import tntapi

def get_filter():
	return """<filter type="xpath" select="/interfaces-state/interface[name='xe0' or name='xe1' or name='ge0' or name='ge1' or name='ge2' or name='ge3' or name='ge4' or name='ge5' or name='ge6' or name='ge7' or name='ge8' or name='ge9' or name='ge15']/*[local-name()='oper-status' or local-name()='statistics']"/>"""

def print_state(before, after):
	print("Printing state ...")
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

	print("local=1;remote=2")
	print("xe0=1;xe1=2;ge0=3;ge1=4;ge2=5;ge3=6;ge4=7;ge5=8;ge6=9;ge7=10;ge8=11;ge9=12;ge15=18;")

	#print all non-zero deltas

	#print all non-zero deltas
	for node in {"local", "remote"}:
		for if_name in {"xe0", "ge15", "ge0", "ge1", "ge2", "ge3", "ge4", "ge5", "ge1", "ge6", "ge7", "ge8", "ge9"}:
			interface = delta[node][if_name]
			for v in dir(interface):
				if not v[0].startswith('_') and not v=='count' and not v=='index':
					value = getattr(interface,v)
					if(value!=None and value!=0):
						print v + "(" + node + ","+ if_name + ")=" + str(value) + ";"



def validate_pause(before, after):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        print_state(before, after)

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

def pause(network, conns, filter=filter):

	rpc="""<discard-changes/>"""
	for conn_id in conns:
		conns[conn_id].send(rpc)
	for conn_id in conns:
		conns[conn_id].receive()

	state_before = tntapi.network_get_state(network, conns, filter=filter)
	time.sleep(1)
	state_after = tntapi.network_get_state(network, conns, filter=filter)
	validate_pause(state_before, state_after)

