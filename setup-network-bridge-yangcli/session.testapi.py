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
	"if":"urn:ietf:params:xml:ns:yang:ietf-interfaces",
	"netconf-node":"urn:tntapi:netconf-node"}

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


	print("#1.2 - Validate no counters are being incremented.")
	for node in {"local", "remote"}:
		for if_name in {"xe0", "ge15", "ge0"}:
			interface = delta[node][if_name]
			for v in dir(interface):
				if not v[0].startswith('_') and not v=='count' and not v=='index':
					value = getattr(interface,v)
					if(value!=None and value!=0):
						print node + ":" + if_name + "." + v + "=" + str(value)
						assert(0)
 

def step_1(network, conns, yconns, filter=filter):

	#Delete all
	result=yangcli(yconns["local"], "discard-changes")
	result=yangcli(yconns["local"], "delete /flows")
	result=yangcli(yconns["local"], "delete /bridge")
	result=yangcli(yconns["remote"], "discard-changes")
	result=yangcli(yconns["remote"], "delete /flows")
	result=yangcli(yconns["remote"], "delete /bridge")
	result=yangcli(yconns["middle"], "discard-changes")
	result=yangcli(yconns["middle"], "delete /flows")
	result=yangcli(yconns["middle"], "delete /bridge")
	tntapi.network_commit(conns)

	yangcli_script_local='''
create /bridge/ports/port -- name=n0
create /bridge/ports/port -- name=gm0
create /bridge/ports/port -- name=e0
create /bridge/ports/port -- name=e1
create /bridge/ports/port -- name=e2
create /bridge/ports/port -- name=e3
create /bridge/ports/port -- name=e4
create /bridge/ports/port -- name=e5
create /bridge/ports/port -- name=e6
create /bridge/ports/port -- name=e7
create /bridge/ports/port -- name=e8
create /bridge/ports/port -- name=e9

merge /interfaces/interface -- name=xe0 type=ethernetCsmacd port-name=n0
merge /interfaces/interface -- name=ge15 type=ethernetCsmacd port-name=gm0
merge /interfaces/interface -- name=ge0 type=ethernetCsmacd port-name=e0
merge /interfaces/interface -- name=ge1 type=ethernetCsmacd port-name=e1
merge /interfaces/interface -- name=ge2 type=ethernetCsmacd port-name=e2
merge /interfaces/interface -- name=ge3 type=ethernetCsmacd port-name=e3
merge /interfaces/interface -- name=ge4 type=ethernetCsmacd port-name=e4
merge /interfaces/interface -- name=ge5 type=ethernetCsmacd port-name=e5
merge /interfaces/interface -- name=ge6 type=ethernetCsmacd port-name=e6
merge /interfaces/interface -- name=ge7 type=ethernetCsmacd port-name=e7
merge /interfaces/interface -- name=ge8 type=ethernetCsmacd port-name=e8
merge /interfaces/interface -- name=ge9 type=ethernetCsmacd port-name=e9

create /flows/flow[id='gm0-to-n0-ptp'] -- match/in-port=gm0 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=e0 actions/action[order='1']/output-action/out-port=e1 actions/action[order='2']/output-action/out-port=e2 actions/action[order='3']/output-action/out-port=e3 actions/action[order='4']/output-action/out-port=e4 actions/action[order='5']/output-action/out-port=e5 actions/action[order='6']/output-action/out-port=e6 actions/action[order='7']/output-action/out-port=e7 actions/action[order='8']/output-action/out-port=e8 actions/action[order='9']/output-action/out-port=e9 actions/action[order='10']/push-vlan-action/vlan-id=100 actions/action[order='10']/push-vlan-action/ethernet-type=37120 actions/action[order='11']/output-action/out-port=n0

create /flows/flow[id='gm0-to-n0-unmatched'] -- match/in-port=gm0 actions/action[order='0']/push-vlan-action/vlan-id=200 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0

create /flows/flow[id='e0-to-n0-unmatched'] -- match/in-port=e0 actions/action[order='0']/push-vlan-action/vlan-id=10 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e1-to-n0-unmatched'] -- match/in-port=e1 actions/action[order='0']/push-vlan-action/vlan-id=11 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e2-to-n0-unmatched'] -- match/in-port=e2 actions/action[order='0']/push-vlan-action/vlan-id=12 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e3-to-n0-unmatched'] -- match/in-port=e3 actions/action[order='0']/push-vlan-action/vlan-id=13 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e4-to-n0-unmatched'] -- match/in-port=e4 actions/action[order='0']/push-vlan-action/vlan-id=14 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e5-to-n0-unmatched'] -- match/in-port=e5 actions/action[order='0']/push-vlan-action/vlan-id=15 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e6-to-n0-unmatched'] -- match/in-port=e6 actions/action[order='0']/push-vlan-action/vlan-id=16 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e7-to-n0-unmatched'] -- match/in-port=e7 actions/action[order='0']/push-vlan-action/vlan-id=17 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e8-to-n0-unmatched'] -- match/in-port=e8 actions/action[order='0']/push-vlan-action/vlan-id=18 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e9-to-n0-unmatched'] -- match/in-port=e9 actions/action[order='0']/push-vlan-action/vlan-id=19 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0

create /flows/flow[id='e0-to-n0-ptp'] -- match/in-port=e0 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e1-to-n0-ptp'] -- match/in-port=e1 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e2-to-n0-ptp'] -- match/in-port=e2 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e3-to-n0-ptp'] -- match/in-port=e3 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e4-to-n0-ptp'] -- match/in-port=e4 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e5-to-n0-ptp'] -- match/in-port=e5 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e6-to-n0-ptp'] -- match/in-port=e6 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e7-to-n0-ptp'] -- match/in-port=e7 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e8-to-n0-ptp'] -- match/in-port=e8 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e9-to-n0-ptp'] -- match/in-port=e9 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0

create /flows/flow[id='n0-to-gm0-ptp'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=100 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action  actions/action[order='1']/output-action/out-port=gm0

create /flows/flow[id='n0-to-gm0-unmatched'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=200 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action  actions/action[order='1']/output-action/out-port=gm0

create /flows/flow[id='n0-to-e0'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=10 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e0
create /flows/flow[id='n0-to-e1'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=11 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e1
create /flows/flow[id='n0-to-e2'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=12 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e2
create /flows/flow[id='n0-to-e3'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=13 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e3
create /flows/flow[id='n0-to-e4'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=14 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e4
create /flows/flow[id='n0-to-e5'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=15 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e5
create /flows/flow[id='n0-to-e6'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=16 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e6
create /flows/flow[id='n0-to-e7'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=17 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e7
create /flows/flow[id='n0-to-e8'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=18 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e8
create /flows/flow[id='n0-to-e9'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=19 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e9
'''

	yangcli_script_remote='''
create /bridge/ports/port -- name=n0
create /bridge/ports/port -- name=gm0
create /bridge/ports/port -- name=e0
create /bridge/ports/port -- name=e1
create /bridge/ports/port -- name=e2
create /bridge/ports/port -- name=e3
create /bridge/ports/port -- name=e4
create /bridge/ports/port -- name=e5
create /bridge/ports/port -- name=e6
create /bridge/ports/port -- name=e7
create /bridge/ports/port -- name=e8
create /bridge/ports/port -- name=e9

merge /interfaces/interface -- name=xe0 type=ethernetCsmacd port-name=n0
merge /interfaces/interface -- name=ge15 type=ethernetCsmacd port-name=gm0
merge /interfaces/interface -- name=ge0 type=ethernetCsmacd port-name=e0
merge /interfaces/interface -- name=ge1 type=ethernetCsmacd port-name=e1
merge /interfaces/interface -- name=ge2 type=ethernetCsmacd port-name=e2
merge /interfaces/interface -- name=ge3 type=ethernetCsmacd port-name=e3
merge /interfaces/interface -- name=ge4 type=ethernetCsmacd port-name=e4
merge /interfaces/interface -- name=ge5 type=ethernetCsmacd port-name=e5
merge /interfaces/interface -- name=ge6 type=ethernetCsmacd port-name=e6
merge /interfaces/interface -- name=ge7 type=ethernetCsmacd port-name=e7
merge /interfaces/interface -- name=ge8 type=ethernetCsmacd port-name=e8
merge /interfaces/interface -- name=ge9 type=ethernetCsmacd port-name=e9

create /flows/flow[id='gm0-to-n0-ptp'] -- match/in-port=gm0 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=e0 actions/action[order='1']/output-action/out-port=e1 actions/action[order='2']/output-action/out-port=e2 actions/action[order='3']/output-action/out-port=e3 actions/action[order='4']/output-action/out-port=e4 actions/action[order='5']/output-action/out-port=e5 actions/action[order='6']/output-action/out-port=e6 actions/action[order='7']/output-action/out-port=e7 actions/action[order='8']/output-action/out-port=e8 actions/action[order='9']/output-action/out-port=e9 actions/action[order='10']/push-vlan-action/vlan-id=100 actions/action[order='10']/push-vlan-action/ethernet-type=37120 actions/action[order='11']/output-action/out-port=n0

create /flows/flow[id='gm0-to-n0-unmatched'] -- match/in-port=gm0 actions/action[order='0']/push-vlan-action/vlan-id=200 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0

create /flows/flow[id='e0-to-n0-unmatched'] -- match/in-port=e0 actions/action[order='0']/push-vlan-action/vlan-id=20 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e1-to-n0-unmatched'] -- match/in-port=e1 actions/action[order='0']/push-vlan-action/vlan-id=21 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e2-to-n0-unmatched'] -- match/in-port=e2 actions/action[order='0']/push-vlan-action/vlan-id=22 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e3-to-n0-unmatched'] -- match/in-port=e3 actions/action[order='0']/push-vlan-action/vlan-id=23 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e4-to-n0-unmatched'] -- match/in-port=e4 actions/action[order='0']/push-vlan-action/vlan-id=24 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e5-to-n0-unmatched'] -- match/in-port=e5 actions/action[order='0']/push-vlan-action/vlan-id=25 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e6-to-n0-unmatched'] -- match/in-port=e6 actions/action[order='0']/push-vlan-action/vlan-id=26 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e7-to-n0-unmatched'] -- match/in-port=e7 actions/action[order='0']/push-vlan-action/vlan-id=27 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e8-to-n0-unmatched'] -- match/in-port=e8 actions/action[order='0']/push-vlan-action/vlan-id=28 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0
create /flows/flow[id='e9-to-n0-unmatched'] -- match/in-port=e9 actions/action[order='0']/push-vlan-action/vlan-id=29 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n0

create /flows/flow[id='e0-to-n0-ptp'] -- match/in-port=e0 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e1-to-n0-ptp'] -- match/in-port=e1 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e2-to-n0-ptp'] -- match/in-port=e2 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e3-to-n0-ptp'] -- match/in-port=e3 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e4-to-n0-ptp'] -- match/in-port=e4 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e5-to-n0-ptp'] -- match/in-port=e5 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e6-to-n0-ptp'] -- match/in-port=e6 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e7-to-n0-ptp'] -- match/in-port=e7 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e8-to-n0-ptp'] -- match/in-port=e8 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0
create /flows/flow[id='e9-to-n0-ptp'] -- match/in-port=e9 match/ethernet-match/ethernet-type/type=35063 actions/action[order='0']/output-action/out-port=n0

create /flows/flow[id='n0-to-gm0-ptp'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=100 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action  actions/action[order='1']/output-action/out-port=gm0

create /flows/flow[id='n0-to-gm0-unmatched'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=200 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action  actions/action[order='1']/output-action/out-port=gm0

create /flows/flow[id='n0-to-e0'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=20 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e0
create /flows/flow[id='n0-to-e1'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=21 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e1
create /flows/flow[id='n0-to-e2'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=22 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e2
create /flows/flow[id='n0-to-e3'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=23 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e3
create /flows/flow[id='n0-to-e4'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=24 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e4
create /flows/flow[id='n0-to-e5'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=25 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e5
create /flows/flow[id='n0-to-e6'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=26 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e6
create /flows/flow[id='n0-to-e7'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=27 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e7
create /flows/flow[id='n0-to-e8'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=28 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e8
create /flows/flow[id='n0-to-e9'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=29 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e9
'''

	yangcli_script_middle='''
create /bridge/ports/port -- name=n0
create /bridge/ports/port -- name=n1
create /bridge/ports/port -- name=e0
create /bridge/ports/port -- name=e1
create /bridge/ports/port -- name=e2
create /bridge/ports/port -- name=e3
create /bridge/ports/port -- name=e4
create /bridge/ports/port -- name=e5
create /bridge/ports/port -- name=e6
create /bridge/ports/port -- name=e7
create /bridge/ports/port -- name=e8
create /bridge/ports/port -- name=e9

merge /interfaces/interface -- name=xe0 type=ethernetCsmacd port-name=n0
merge /interfaces/interface -- name=xe1 type=ethernetCsmacd port-name=n1
merge /interfaces/interface -- name=ge0 type=ethernetCsmacd port-name=e0
merge /interfaces/interface -- name=ge1 type=ethernetCsmacd port-name=e1
merge /interfaces/interface -- name=ge2 type=ethernetCsmacd port-name=e2
merge /interfaces/interface -- name=ge3 type=ethernetCsmacd port-name=e3
merge /interfaces/interface -- name=ge4 type=ethernetCsmacd port-name=e4
merge /interfaces/interface -- name=ge5 type=ethernetCsmacd port-name=e5
merge /interfaces/interface -- name=ge6 type=ethernetCsmacd port-name=e6
merge /interfaces/interface -- name=ge7 type=ethernetCsmacd port-name=e7
merge /interfaces/interface -- name=ge8 type=ethernetCsmacd port-name=e8
merge /interfaces/interface -- name=ge9 type=ethernetCsmacd port-name=e9

create /flows/flow[id='e0-to-n1'] -- match/in-port=e0 actions/action[order='0']/push-vlan-action/vlan-id=20 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e1-to-n1'] -- match/in-port=e1 actions/action[order='0']/push-vlan-action/vlan-id=21 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e2-to-n1'] -- match/in-port=e2 actions/action[order='0']/push-vlan-action/vlan-id=22 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e3-to-n1'] -- match/in-port=e3 actions/action[order='0']/push-vlan-action/vlan-id=23 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e4-to-n1'] -- match/in-port=e4 actions/action[order='0']/push-vlan-action/vlan-id=24 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e5-to-n1'] -- match/in-port=e5 actions/action[order='0']/push-vlan-action/vlan-id=25 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e6-to-n1'] -- match/in-port=e6 actions/action[order='0']/push-vlan-action/vlan-id=26 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e7-to-n1'] -- match/in-port=e7 actions/action[order='0']/push-vlan-action/vlan-id=27 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e8-to-n1'] -- match/in-port=e8 actions/action[order='0']/push-vlan-action/vlan-id=28 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1
create /flows/flow[id='e9-to-n1'] -- match/in-port=e9 actions/action[order='0']/push-vlan-action/vlan-id=29 actions/action[order='0']/push-vlan-action/ethernet-type=37120 actions/action[order='1']/output-action/out-port=n1

create /flows/flow[id='n0-to-e0'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=20 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e0
create /flows/flow[id='n0-to-e1'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=21 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e1
create /flows/flow[id='n0-to-e2'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=22 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e2
create /flows/flow[id='n0-to-e3'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=23 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e3
create /flows/flow[id='n0-to-e4'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=24 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e4
create /flows/flow[id='n0-to-e5'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=25 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e5
create /flows/flow[id='n0-to-e6'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=26 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e6
create /flows/flow[id='n0-to-e7'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=27 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e7
create /flows/flow[id='n0-to-e8'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=28 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e8
create /flows/flow[id='n0-to-e9'] -- match/in-port=n0 match/vlan-match/vlan-id/vlan-id=29 match/ethernet-match/ethernet-type/type=37120 actions/action[order='0']/pop-vlan-action actions/action[order='1']/output-action/out-port=e9

create /flows/flow[id='n0-to-n1'] -- match/in-port=n0 actions/action[order='0']/output-action/out-port=n1
create /flows/flow[id='n1-to-n0'] -- match/in-port=n1 actions/action[order='0']/output-action/out-port=n0
'''
 	yangcli_ok_script(yconns["local"], yangcli_script_local)
 	yangcli_ok_script(yconns["remote"], yangcli_script_remote)
	yangcli_ok_script(yconns["middle"], yangcli_script_middle)

	tntapi.network_commit(conns)
	state_before = tntapi.network_get_state(network, conns, filter=filter)
	time.sleep(5)
	state_after = tntapi.network_get_state(network, conns, filter=filter)
	validate_step_1(state_before, state_after)

def main():
	print("""
#Description: Setup bridge flows
#Procedure:
#1 - Load the bridge flows configuration on the local and remote h100.
#1.1 - Validate all analyzer interfaces have oper-status=up.
#1.2 - Validate no counters are being incremented.
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
	print("#1 - Load the bridge flows configuration on the local and remote h100.")
        step_1(network, conns, yconns, filter=filter)
 
sys.exit(main())
