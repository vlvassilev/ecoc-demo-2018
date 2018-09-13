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
	result=yangcli(yconns["local"], "delete /fusion-streams")
	result=yangcli(yconns["remote"], "delete /fusion-streams")
	tntapi.network_commit(conns)

	yangcli_script_local='''
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='matched-tpid'] -- priority=gst filter/tpid=88F7 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false drop[out-port='e0']/pop-vlan-tag=true drop[out-port='e1']/pop-vlan-tag=true drop[out-port='e2']/pop-vlan-tag=true drop[out-port='e3']/pop-vlan-tag=true drop[out-port='e4']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='unmatched'] -- priority=sm push-vlan-tag/vlanid=200 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false

create /fusion-streams/aggregation[in-port='e0']/sm -- out-port=n1 push-vlan-tag/vlanid=10 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e1']/sm -- out-port=n1 push-vlan-tag/vlanid=11 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e2']/sm -- out-port=n1 push-vlan-tag/vlanid=12 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e3']/sm -- out-port=n1 push-vlan-tag/vlanid=13 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e4']/sm -- out-port=n1 push-vlan-tag/vlanid=14 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e5']/sm -- out-port=n1 push-vlan-tag/vlanid=15 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e6']/sm -- out-port=n1 push-vlan-tag/vlanid=16 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e7']/sm -- out-port=n1 push-vlan-tag/vlanid=17 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e8']/sm -- out-port=n1 push-vlan-tag/vlanid=18 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e9']/sm -- out-port=n1 push-vlan-tag/vlanid=19 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1

create /fusion-streams/aggregation[in-port='e0']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e1']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e2']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e3']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e4']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e5']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e6']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e7']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e8']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e9']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1

create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='100'] -- priority=gst filter/tpid=9100 forward/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='200'] -- priority=sm filter/tpid=9100 forward/pop-vlan-tag=true

create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='10'] -- priority=sm filter/tpid=9100 drop[out-port='e0']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='11'] -- priority=sm filter/tpid=9100 drop[out-port='e1']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='12'] -- priority=sm filter/tpid=9100 drop[out-port='e2']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='13'] -- priority=sm filter/tpid=9100 drop[out-port='e3']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='14'] -- priority=sm filter/tpid=9100 drop[out-port='e4']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='15'] -- priority=sm filter/tpid=9100 drop[out-port='e5']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='16'] -- priority=sm filter/tpid=9100 drop[out-port='e6']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='17'] -- priority=sm filter/tpid=9100 drop[out-port='e7']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='18'] -- priority=sm filter/tpid=9100 drop[out-port='e8']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='19'] -- priority=sm filter/tpid=9100 drop[out-port='e9']/pop-vlan-tag=true
'''

	yangcli_script_remote='''
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='matched-tpid'] -- priority=gst filter/tpid=88F7 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false

create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='unmatched'] -- priority=sm push-vlan-tag/vlanid=200 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false

create /fusion-streams/aggregation[in-port='e0']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e1']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e2']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e3']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e4']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e5']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e6']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e7']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e8']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e9']/gst -- filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1 out-port=n1 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1

create /fusion-streams/aggregation[in-port='e0']/sm -- out-port=n1 push-vlan-tag/vlanid=10 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e1']/sm -- out-port=n1 push-vlan-tag/vlanid=11 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e2']/sm -- out-port=n1 push-vlan-tag/vlanid=12 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e3']/sm -- out-port=n1 push-vlan-tag/vlanid=13 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e4']/sm -- out-port=n1 push-vlan-tag/vlanid=14 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e5']/sm -- out-port=n1 push-vlan-tag/vlanid=25 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e6']/sm -- out-port=n1 push-vlan-tag/vlanid=26 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e7']/sm -- out-port=n1 push-vlan-tag/vlanid=27 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e8']/sm -- out-port=n1 push-vlan-tag/vlanid=28 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e9']/sm -- out-port=n1 push-vlan-tag/vlanid=29 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1

create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='100'] -- priority=gst filter/tpid=9100 drop[out-port='e0']/pop-vlan-tag=true drop[out-port='e1']/pop-vlan-tag=true drop[out-port='e2']/pop-vlan-tag=true drop[out-port='e3']/pop-vlan-tag=true drop[out-port='e4']/pop-vlan-tag=true forward/pop-vlan-tag=true

create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='200'] -- priority=sm filter/tpid=9100 forward/pop-vlan-tag=true

create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='10'] -- filter/tpid=9100 priority=sm drop[out-port='e0']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='11'] -- filter/tpid=9100 priority=sm drop[out-port='e1']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='12'] -- filter/tpid=9100 priority=sm drop[out-port='e2']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='13'] -- filter/tpid=9100 priority=sm drop[out-port='e3']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='14'] -- filter/tpid=9100 priority=sm drop[out-port='e4']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='25'] -- filter/tpid=9100 priority=sm drop[out-port='e5']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='26'] -- filter/tpid=9100 priority=sm drop[out-port='e6']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='27'] -- filter/tpid=9100 priority=sm drop[out-port='e7']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='28'] -- filter/tpid=9100 priority=sm drop[out-port='e8']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='29'] -- filter/tpid=9100 priority=sm drop[out-port='e9']/pop-vlan-tag=true
'''

	yangcli_script_middle='''
replace /vlans/vlan -- name=trunk id=500 tpid=0x9100
replace /interfaces/interface -- name='xe0' type=ethernetCsmacd
replace /interfaces/interface[name='xe0']/ethernet-switching/trunk-interface/vlans/vlan/vlan-name value=trunk
replace /interfaces/interface -- name='xe1' type=ethernetCsmacd
replace /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan/vlan-name value=trunk
replace /hadm/forward-unmatched-packets value=true

replace /vlans/vlan -- name=vlan10 id=10 tpid=0x9100
replace /vlans/vlan -- name=vlan11 id=11 tpid=0x9100
replace /vlans/vlan -- name=vlan12 id=12 tpid=0x9100
replace /vlans/vlan -- name=vlan13 id=13 tpid=0x9100
replace /vlans/vlan -- name=vlan14 id=14 tpid=0x9100
replace /vlans/vlan -- name=vlan15 id=15 tpid=0x9100
replace /vlans/vlan -- name=vlan16 id=16 tpid=0x9100
replace /vlans/vlan -- name=vlan17 id=17 tpid=0x9100
replace /vlans/vlan -- name=vlan18 id=18 tpid=0x9100
replace /vlans/vlan -- name=vlan19 id=19 tpid=0x9100

replace /vlans/vlan -- name=vlan20 id=20 tpid=0x9100
replace /vlans/vlan -- name=vlan21 id=21 tpid=0x9100
replace /vlans/vlan -- name=vlan22 id=22 tpid=0x9100
replace /vlans/vlan -- name=vlan23 id=23 tpid=0x9100
replace /vlans/vlan -- name=vlan24 id=24 tpid=0x9100
replace /vlans/vlan -- name=vlan25 id=25 tpid=0x9100
replace /vlans/vlan -- name=vlan26 id=26 tpid=0x9100
replace /vlans/vlan -- name=vlan27 id=27 tpid=0x9100
replace /vlans/vlan -- name=vlan28 id=28 tpid=0x9100
replace /vlans/vlan -- name=vlan29 id=29 tpid=0x9100

create /interfaces/interface -- name='ge0' type=ethernetCsmacd
create /interfaces/interface -- name='ge1' type=ethernetCsmacd
create /interfaces/interface -- name='ge2' type=ethernetCsmacd
create /interfaces/interface -- name='ge3' type=ethernetCsmacd
create /interfaces/interface -- name='ge4' type=ethernetCsmacd
create /interfaces/interface -- name='ge5' type=ethernetCsmacd
create /interfaces/interface -- name='ge6' type=ethernetCsmacd
create /interfaces/interface -- name='ge7' type=ethernetCsmacd
create /interfaces/interface -- name='ge8' type=ethernetCsmacd
create /interfaces/interface -- name='ge9' type=ethernetCsmacd

create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan20
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan21
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan22
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan23
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan24
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan25
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan26
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan27
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan28
create /interfaces/interface[name='xe1']/ethernet-switching/trunk-interface/vlans/vlan  -- vlan-name=vlan29

create /interfaces/interface[name='ge0']/ethernet-switching/access-interface/vlan -- vlan-name=vlan20
create /interfaces/interface[name='ge1']/ethernet-switching/access-interface/vlan -- vlan-name=vlan21
create /interfaces/interface[name='ge2']/ethernet-switching/access-interface/vlan -- vlan-name=vlan22
create /interfaces/interface[name='ge3']/ethernet-switching/access-interface/vlan -- vlan-name=vlan23
create /interfaces/interface[name='ge4']/ethernet-switching/access-interface/vlan -- vlan-name=vlan24
create /interfaces/interface[name='ge5']/ethernet-switching/access-interface/vlan -- vlan-name=vlan25
create /interfaces/interface[name='ge6']/ethernet-switching/access-interface/vlan -- vlan-name=vlan26
create /interfaces/interface[name='ge7']/ethernet-switching/access-interface/vlan -- vlan-name=vlan27
create /interfaces/interface[name='ge8']/ethernet-switching/access-interface/vlan -- vlan-name=vlan28
create /interfaces/interface[name='ge9']/ethernet-switching/access-interface/vlan -- vlan-name=vlan29
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
#Description: Setup fusion streams
#Procedure:
#1 - Load the fusion streams configuration on the local and remote h100.
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
	print("#1 - Load the fusion streams configuration on the local and remote h100.")
        step_1(network, conns, yconns, filter=filter)
 
sys.exit(main())
