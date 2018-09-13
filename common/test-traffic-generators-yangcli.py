#!/usr/bin/python

from lxml import etree
import time
import sys, os
import argparse
import tntapi
import yangrpc
from yangcli import yangcli

namespaces={"nc":"urn:ietf:params:xml:ns:netconf:base:1.0",
	"nd":"urn:ietf:params:xml:ns:yang:ietf-network",
	"nt":"urn:ietf:params:xml:ns:yang:ietf-network-topology"}

test_time=60

def validate_traffic_on(node_name, interface_name, before, after, delta, my_test_time, load_percent, frame_size, interframe_gap, frames_per_burst, interburst_gap):

	global test_time
	after=tntapi.strip_namespaces(after)
	speed_bits_per_sec=long(after.xpath("node[node-id='"+node_name+"']/data/interfaces-state/interface[name='"+interface_name+"']/speed")[0].text)
	print "speed(bits/sec)="+str(speed_bits_per_sec)
	print "speed(bytes/sec)="+str(speed_bits_per_sec/8)
	generated_octets=1.0*delta[node_name][interface_name].out_octets
	assert(generated_octets>0)
	generated_pkts=1.0*delta[node_name][interface_name].out_pkts
	assert(generated_pkts>0)

	assert((generated_pkts*frame_size)==generated_octets)

	generated_octets_expected=(load_percent*test_time*speed_bits_per_sec/(8*100))
	print("Generated octets per sec="+str(generated_octets/test_time))
	print("Expected octets per sec="+str(generated_octets_expected/test_time))
	ratio=generated_octets/generated_octets_expected
	if(ratio>1):
		print("Generated %(r).4f times MORE: generated=%(g)d and expected=%(e)d"%{'r':ratio, 'g':generated_octets,'e':generated_octets_expected})
		if(ratio>(110.0/100)):
			print("Error: >10% precision deviation.")
	elif(ratio<1):
		print("Generated %(r).4f times LESS: generated=%(g)d and expected=%(e)d"%{'r':1/ratio, 'g':generated_octets,'e':generated_octets_expected})
		if(ratio<(90.0/100)):
			print("Error: >10% precision deviation.")
	else:
		print("Generated EXACTLY: generated=%(g)s and expected=%(e)s"%{'g':generated_octets,'e':generated_octets_expected})

	return float(100*generated_octets/(my_test_time*speed_bits_per_sec/8))

def validate_traffic_off(node_name, interface_name, before, after, delta):

	generated_octets=1.0*delta[node_name][interface_name].out_octets
	assert(generated_octets==0)

def validate(network, conns, yconns, inks, load_percent=99, frame_size=1500, interframe_gap=12, frames_per_burst=0, interburst_gap=0):
	filter = """<filter type="xpath" select="/interfaces-state/interface/*[local-name()='traffic-analyzer' or local-name()='oper-status' or local-name()='statistics' or local-name()='speed']"/>"""
#	config_idle="""
#<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
#</config>
#"""
	config_idle={}
        nodes = network.xpath('nd:node', namespaces=namespaces)
	for node in nodes:
		node_id = node.xpath('nd:node-id', namespaces=namespaces)[0].text
		config=""

		termination_points = node.xpath('./nt:termination-point', namespaces=namespaces)
		for termination_point in termination_points:
			tp_id = termination_point.xpath('nt:tp-id', namespaces=namespaces)[0].text
			ok=yangcli(yconns[node_id],"""replace /interfaces/interface[name='%(name)s'] -- type=ethernetCsmacd"""%{'name':tp_id}).xpath('./ok')
			assert(len(ok)==1)

	tntapi.network_commit(conns)

	state_before = tntapi.network_get_state(network, conns, filter=filter)
	print("Waiting " + "5" + " sec. ..." )
	time.sleep(5)
	print("Done.")
	state_after = tntapi.network_get_state(network, conns, filter=filter)

	mylinks = tntapi.parse_network_links(state_before)
	t1 = tntapi.parse_network_nodes(state_before)
	t2 = tntapi.parse_network_nodes(state_after)
	delta = tntapi.get_network_counters_delta(state_before,state_after)

	tntapi.print_state_ietf_interfaces_statistics_delta(network, state_before, state_after)

	for node in nodes:
		node_id = node.xpath('nd:node-id', namespaces=namespaces)[0].text
		termination_points = node.xpath('./nt:termination-point', namespaces=namespaces)
		for termination_point in termination_points:
			tp_id = termination_point.xpath('nt:tp-id', namespaces=namespaces)[0].text
			validate_traffic_off(node_id, tp_id, state_before, state_after, delta)

	load=float(load_percent)/100
	print "ifg="+str(interframe_gap)

	for node in nodes:
		node_id = node.xpath('nd:node-id', namespaces=namespaces)[0].text
		config=""

		termination_points = node.xpath('./nt:termination-point', namespaces=namespaces)
		for termination_point in termination_points:
			tp_id = termination_point.xpath('nt:tp-id', namespaces=namespaces)[0].text
			if(frames_per_burst>0):
				my_burst_config="""frames-per-burst=%(frames-per-burst)d interburst-gap=%(interburst-gap)d""" % {'frames-per-burst':frames_per_burst,'interburst-gap':interburst_gap-8}
			else:
				my_burst_config=""

			ok=yangcli(yconns[node_id],"""create /interfaces/interface[name='%(name)s']/traffic-generator -- frame-size=%(frame-size)d interframe-gap=%(interframe-gap)d %(burst)s""" % {'name':tp_id,'frame-size':frame_size,'interframe-gap':interframe_gap-8, 'burst':my_burst_config}).xpath('./ok')
			assert(len(ok)==1)


	state_before = tntapi.network_get_state(network, conns, filter=filter)
        tntapi.network_commit(conns)

	print("Waiting " + str(test_time) + " sec. ..." )
	time.sleep(test_time)

	print("Stopping generators ...")
	for node in nodes:
		node_id = node.xpath('nd:node-id', namespaces=namespaces)[0].text
		config=""

		termination_points = node.xpath('./nt:termination-point', namespaces=namespaces)
		for termination_point in termination_points:
			tp_id = termination_point.xpath('nt:tp-id', namespaces=namespaces)[0].text
			ok=yangcli(yconns[node_id],"""replace /interfaces/interface[name='%(name)s'] -- type=ethernetCsmacd"""%{'name':tp_id}).xpath('./ok')
			assert(len(ok)==1)

	tntapi.network_commit(conns)
	print("Done.")

	state_after = tntapi.network_get_state(network, conns, filter=filter)

	t1 = tntapi.parse_network_nodes(state_before)
	t2 = tntapi.parse_network_nodes(state_after)
	delta = tntapi.get_network_counters_delta(state_before,state_after)

	tntapi.print_state_ietf_interfaces_statistics_delta(network, state_before, state_after)

	load_generated={}
	for node in nodes:
		node_id = node.xpath('nd:node-id', namespaces=namespaces)[0].text
		termination_points = node.xpath('./nt:termination-point', namespaces=namespaces)
		for termination_point in termination_points:
			tp_id = termination_point.xpath('nt:tp-id', namespaces=namespaces)[0].text
			load_generated[node_id,tp_id]=validate_traffic_on(node_id, tp_id, state_before, state_after, delta, test_time, load_percent, frame_size, interframe_gap, frames_per_burst, interburst_gap)

	return (load_percent, load_generated)

def display_table(bw_expected, bw_generated):
	print(bw_generated)

	header_line="| Port \ Run    "

	for key in bw_generated.keys():
		header_line=header_line+"|  %3d   "%(key)
	header_line=header_line+"|"

	len(header_line)
	outer_border_line="+"+(len(header_line)-2)*"-"+"+"
	border_line="|"+(len(header_line)-2)*"-"+"|"

	print(outer_border_line)
	print(header_line)
	print(outer_border_line)

	line="| NORM          "
	for key in bw_generated.keys():
		line=line+"| %6.2f "%(bw_expected[key])
	line=line+"|"
	print line

	for key in bw_generated[1].keys():
		print(border_line)
		line="| " +key[0]+"."+key[1]
		line=line + " "*(16-len(line))
		for run in bw_generated.keys():
			line=line+"| %6.2f "%(bw_generated[run][key[0],key[1]])
		print(line+ "|")
	print(outer_border_line)
	return 0

def main():
	print("""
#Description: Basic traffic-generator verification test
#Procedure:
#1 - Generate 98.7% maximum traffic load 6+6+2+1500+4 byte packets 7+1+12 byte ifg and verify counters.
#2 - Generate 76.19% maximum traffic load with minimum frame size 6+6+2+46+4 byte packets 7+1+12 byte ifg and verify counters.
#3 - Generate 50.165% traffic load 6+6+2+1500+4 byte packets 7+1+1500 byte ifg and verify counters.
#4 - Generate 4.0452% traffic load 6+6+2+1500+4 byte packets 7+1+36000 byte ifg and verify counters.
#5 - Generate 49.757% traffic load 6+6+2+1500+4 byte packets 7+1+12 byte ifg, frames-per-burst=10, interburst-gap=7+1+15120 and verify counters.
#6 - Generate 3.0344% traffic load 6+6+2+1500+4 byte packets 7+1+12 byte ifg, frames-per-burst=10, interburst-gap=7+1+484880 and verify counters.
#7 - Generate 7.7719% traffic load 6+6+2+1500+4 byte packets 7+1+36000 byte ifg, frames-per-burst=2, interburst-gap=7+1+12 and verify counters.
""")
def main():

	global test_time
	parser = argparse.ArgumentParser()
	parser.add_argument("--config", help="Path to the netconf configuration *.xml file defining the configuration according to ietf-networks, ietf-networks-topology and netconf-node models e.g. ../networks.xml")
	args = parser.parse_args()

	tree=etree.parse(args.config)
	network = tree.xpath('/nc:config/nd:networks/nd:network', namespaces=namespaces)[0]

	conns = tntapi.network_connect(network)
	yconns = tntapi.network_connect_yangrpc(network)
	mylinks = tntapi.parse_network_links(network)

	assert(conns != None)
	assert(yconns != None)

	step=1
	bw_expected={}
	bw_generated={}
	(bw_expected[step],bw_generated[step]) = validate(network, conns, yconns, mylinks, 98.7, frame_size=6+6+2+1500+4, interframe_gap=7+1+12)
	step=step+1

	(bw_expected[step],bw_generated[step]) = validate(network, conns, yconns, mylinks, 76.19, frame_size=6+6+2+46+4, interframe_gap=7+1+12)
	step=step+1

	(bw_expected[step],bw_generated[step]) = validate(network, conns, yconns, mylinks, 50.165, frame_size=6+6+2+1500+4, interframe_gap=7+1+1500)
	step=step+1

	(bw_expected[step],bw_generated[step]) = validate(network, conns, yconns, mylinks, 4.0452,  frame_size=6+6+2+1500+4, interframe_gap=7+1+36000)
	step=step+1

	(bw_expected[step],bw_generated[step]) = validate(network, conns, yconns, mylinks, 49.757, frame_size=6+6+2+1500+4, interframe_gap=7+1+12, frames_per_burst=10, interburst_gap=7+1+15120)
	step=step+1

	(bw_expected[step],bw_generated[step]) = validate(network, conns, yconns, mylinks, 3.0344,  frame_size=6+6+2+1500+4, interframe_gap=7+1+12, frames_per_burst=10, interburst_gap=7+1+484880)
	step=step+1

	(bw_expected[step],bw_generated[step]) = validate(network, conns, yconns, mylinks, 7.7719,  frame_size=6+6+2+1500+4, interframe_gap=7+36000+12, frames_per_burst=2, interburst_gap=7+1+12)
	step=step+1

	display_table(bw_expected,bw_generated)
	return 0

sys.exit(main())
