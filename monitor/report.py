#!/usr/bin/python

# Prints summary with information relevant to the ECOC 2018 demo setup
# Usage:
# $> ./report.py before.xml after.xml
#1. Period:
#+------------+---------------------+---------------------+--------------+
#|    node    |       start         |         stop        |     period   |
#+------------+---------------------+---------------------+--------------+
#| middle     | 2018-09-20T09:21:08 | 2018-09-20T09:22:30 |       82.000 |
#| local      | 2018-09-20T09:21:08 | 2018-09-20T09:22:30 |       82.000 |
#| remote     | 2018-09-20T09:21:08 | 2018-09-20T09:22:30 |       82.000 |
#+------------+---------------------+---------------------+--------------+
#2. Data transfer rate:
#+------------+--------------+-------+
#|  if name   |       MB/s   |   %   |
#+------------+--------------+-------+
#| middle.xe0 |       2875   |   24  |
#| remote.xe0 |       5699   |   48  |
#+------------+--------------+-------+
#
#3. Timing:
#+-----------+--------------+-------------+--------------+---------------+
#|  if name  |  delay-min   |  delay-max  |      PDV     |     samples   |
#+-----------+--------------+-------------+--------------+---------------+
#| local.ge1 |      7392 ns |      7449 ns|        57 ns |     54796785  |
#| local.ge2 |      7392 ns |      7456 ns|        64 ns |     54781968  |
#| local.ge3 |      7398 ns |      7456 ns|        58 ns |     54769249  |
#| local.ge4 |         0 ns |         0 ns|         0 ns |            0  |
#+-----------+--------------+-------------+--------------+---------------+

import lxml
from lxml import etree
import time
import sys, os
import argparse
from datetime import datetime
import tntapi

period_default=20

namespaces={"nc":"urn:ietf:params:xml:ns:netconf:base:1.0",
	"nd":"urn:ietf:params:xml:ns:yang:ietf-network"}
def main():

	before_config=etree.parse(sys.argv[1])
	before_networks = before_config.xpath('/nc:config/nd:networks',namespaces=namespaces)[0]
	before_network = before_networks.xpath('nd:network',namespaces=namespaces)[0]

	after_config=etree.parse(sys.argv[2])
	after_networks = after_config.xpath('/nc:config/nd:networks',namespaces=namespaces)[0]
	after_network = after_networks.xpath('nd:network',namespaces=namespaces)[0]


	t1 = tntapi.parse_network_nodes(before_network)
	t2 = tntapi.parse_network_nodes(after_network)
	delta = tntapi.get_network_counters_delta(before_network,after_network)

	before=tntapi.strip_namespaces(before_network)
	after=tntapi.strip_namespaces(after_network)

	print("1. Period:")
	print("+------------+---------------------+---------------------+--------------+")
	print("|    node    |       start         |         stop        |     period   |")
	print("+------------+---------------------+---------------------+--------------+")
	node_period={}
	nodes = after.xpath('node')
	for node in nodes:
		node_id = node.xpath('node-id')[0].text

		datetime_before=before.xpath("node[node-id='%s']/data/system-state/clock/current-datetime"%(node_id))
		datetime_after=  after.xpath("node[node-id='%s']/data/system-state/clock/current-datetime"%(node_id))
		if(len(datetime_before)==1 and len(datetime_after)==1):
			dt_before = datetime.strptime(datetime_before[0].text[:19], '%Y-%m-%dT%H:%M:%S')
			dt_after = datetime.strptime(datetime_after[0].text[:19],   '%Y-%m-%dT%H:%M:%S')
			node_period[node_id] = (dt_after-dt_before).total_seconds()
			#print("node:%s supports /system-state/clock/current-datetime calculated %f sec as period"%(node_id,node_period[node_id]))
			print("| %-10s | %s | %s | %+12s |"%(node_id,datetime_before[0].text[:19],datetime_after[0].text[:19],"%.3f"%node_period[node_id]))
		else:
			node_period[node_id]=period_default
			#print("node:%s does not support /system-state/clock/current-datetime using %f sec as period"%(node_id,node_period[node_id]))

	print("+------------+---------------------+---------------------+--------------+")

	print("2. Data transfer rate:")
	print("+------------+--------------+-------+")
	print("|  if name   |       MB/s   |   %   |")
	print("+------------+--------------+-------+")
	rate=float(delta["middle"]["xe0"].in_octets)/(node_period["middle"])
	print("| %s.%s |  %9.0f   |  %3.0f  |"%("middle","xe0",rate/(1024*1024),100*rate/(100000000000/8)))
	rate=float(delta["remote"]["xe0"].in_octets)/(node_period["remote"])
	print("| %s.%s |  %9.0f   |  %3.0f  |"%("remote","xe0",rate/(1024*1024),100*rate/(100000000000/8)))
	print("+------------+--------------+-------+")

	print("")
	print("3. Timing:")
	print("+-----------+--------------+-------------+--------------+---------------+")
	print("|  if name  |  delay-min   |  delay-max  |      PDV     |     samples   |")
	print("+-----------+--------------+-------------+--------------+---------------+")
	analyzer_enabled_ifs = ["ge1", "ge2", "ge3", "ge4"]
	for analyzer_enabled_if in analyzer_enabled_ifs:
		latency_max=int(after.xpath("node[node-id='local']/data/interfaces-state/interface[name='%s']/traffic-analyzer/testframe-stats/latency/max"%(analyzer_enabled_if))[0].text)
		latency_min=int(after.xpath("node[node-id='local']/data/interfaces-state/interface[name='%s']/traffic-analyzer/testframe-stats/latency/min"%(analyzer_enabled_if))[0].text)
		samples=int(after.xpath("node[node-id='local']/data/interfaces-state/interface[name='%s']/traffic-analyzer/testframe-stats/latency/samples"%(analyzer_enabled_if))[0].text)
		print("| local.%s | %9d ns | %9d ns| %9d ns |   %10d  |"%(analyzer_enabled_if,latency_min,latency_max,latency_max-latency_min, samples))

	print("+-----------+--------------+-------------+--------------+---------------+")

	return 0

sys.exit(main())
