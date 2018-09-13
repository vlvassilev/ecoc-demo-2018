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
	"if":"urn:ietf:params:xml:ns:yang:ietf-interfaces"}

def validate_step_1(before, after):
	mylinks = tntapi.parse_network_links(before)
	t1 = tntapi.parse_network_nodes(before)
	t2 = tntapi.parse_network_nodes(after)
	delta = tntapi.get_network_counters_delta(before,after)

        testsuiteapi.print_state(before, after)
	after=tntapi.strip_namespaces(after)

	print("#1.1 - Validate all analyzer interfaces have oper-status=up.")
	for node in {"analyzer"}:
		for if_name in {"ge0", "ge1", "xe0", "xe1"}:
			print "Checking %(node)s[%(if_name)s]"%{'node':node, 'if_name':if_name}
			oper_status=after.xpath("node[node-id='%(node)s']/data/interfaces-state/interface[name='%(if_name)s']/oper-status"%{'node':node, 'if_name':if_name})[0].text
			assert(oper_status=='up')

	print("#1.2 - Validate no counters are being incremented.")
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
 

def step_1(network, conns, filter=filter):
	fusion_streams_config_h100_local = """
  <config>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
      <interface>
        <name>xe0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface>
        <name>ge15</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface>
        <name>ge0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
    </interfaces>
    <fusion-streams xmlns="http://transpacket.com/ns/transpacket-fusion-streams" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
    <aggregation>
      <in-port>e0</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>10</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n0</out-port>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e1</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>11</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n0</out-port>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e2</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>12</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n0</out-port>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e3</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>13</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n0</out-port>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e4</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>14</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n0</out-port>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <drop-and-forward>
      <in-port>n0</in-port>
      <filter-rule>matched-tpid</filter-rule>
      <priority>gst</priority>
      <push-vlan-tag>
        <vlanid>100</vlanid>
        <tpid>9100</tpid>
        <pcp>0</pcp>
        <cfi>1</cfi>
      </push-vlan-tag>
      <filter>
        <tpid>88F7</tpid>
      </filter>
      <drop>
        <out-port>e0</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e1</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e2</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e3</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e4</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <forward>
        <pop-vlan-tag>false</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n0</in-port>
      <filter-rule>unmatched</filter-rule>
      <priority>sm</priority>
      <push-vlan-tag>
        <vlanid>200</vlanid>
        <tpid>9100</tpid>
        <pcp>0</pcp>
        <cfi>1</cfi>
      </push-vlan-tag>
      <forward>
        <pop-vlan-tag>false</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>10</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e0</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>100</filter-rule>
      <priority>gst</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <forward>
        <pop-vlan-tag>true</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>11</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e1</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>12</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e2</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>13</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e3</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>14</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e4</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>200</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <forward>
        <pop-vlan-tag>true</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    </fusion-streams>
  </config>
"""
	fusion_streams_config_h100_remote = """
  <config>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
      <interface>
        <name>xe0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface>
        <name>ge15</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface>
        <name>ge0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
    </interfaces>
    <fusion-streams xmlns="http://transpacket.com/ns/transpacket-fusion-streams" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
    <aggregation>
      <in-port>e0</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>10</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>100</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e1</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>11</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>100</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e2</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>12</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>100</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e3</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>13</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>100</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <aggregation>
      <in-port>e4</in-port>
      <sm>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>14</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
      </sm>
      <gst>
        <out-port>n1</out-port>
        <push-vlan-tag>
          <vlanid>100</vlanid>
          <tpid>9100</tpid>
          <pcp>0</pcp>
          <cfi>1</cfi>
        </push-vlan-tag>
        <filter>
          <ether-type>88F7</ether-type>
          <tpid>88F7</tpid>
          <vlanid>1</vlanid>
        </filter>
      </gst>
    </aggregation>
    <drop-and-forward>
      <in-port>n0</in-port>
      <filter-rule>matched-tpid</filter-rule>
      <priority>gst</priority>
      <push-vlan-tag>
        <vlanid>100</vlanid>
        <tpid>9100</tpid>
        <pcp>0</pcp>
        <cfi>1</cfi>
      </push-vlan-tag>
      <filter>
        <tpid>88F7</tpid>
      </filter>
      <forward>
        <pop-vlan-tag>false</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n0</in-port>
      <filter-rule>unmatched</filter-rule>
      <priority>sm</priority>
      <push-vlan-tag>
        <vlanid>200</vlanid>
        <tpid>9100</tpid>
        <pcp>0</pcp>
        <cfi>1</cfi>
      </push-vlan-tag>
      <forward>
        <pop-vlan-tag>false</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>10</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e0</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>100</filter-rule>
      <priority>gst</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e0</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e1</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e2</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e3</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <drop>
        <out-port>e4</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
      <forward>
        <pop-vlan-tag>true</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>11</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e1</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>12</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e2</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>13</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e3</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>14</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <drop>
        <out-port>e4</out-port>
        <pop-vlan-tag>true</pop-vlan-tag>
      </drop>
    </drop-and-forward>
    <drop-and-forward>
      <in-port>n1</in-port>
      <filter-rule>200</filter-rule>
      <priority>sm</priority>
      <filter>
        <tpid>9100</tpid>
      </filter>
      <forward>
        <pop-vlan-tag>true</pop-vlan-tag>
      </forward>
    </drop-and-forward>
    </fusion-streams>
  </config>
"""
	idle_config_analyzer = """
  <config>
    <hadm xmlns="http://transpacket.com/ns/hadm" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
    </hadm>
    <vlans xmlns="http://transpacket.com/ns/hadm1-vlans" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
    </vlans>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>xe0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>

      </interface>
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>xe1</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
      </interface>
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>ge0</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
	<ethernet xmlns="urn:ieee:params:xml:ns:yang:ethernet">
          <auto-negotiation>
            <status>enabled</status>
          </auto-negotiation>
        </ethernet>
      </interface>
      <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
        <name>ge1</name>
        <type
          xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
	<ethernet xmlns="urn:ieee:params:xml:ns:yang:ethernet">
          <auto-negotiation>
            <status>enabled</status>
          </auto-negotiation>
        </ethernet>
      </interface>
    </interfaces>
  </config>
"""

        tntapi.edit_config(conns["analyzer"],idle_config_analyzer)
        tntapi.edit_config(conns["local"],fusion_streams_config_h100_local)
        tntapi.edit_config(conns["remote"],fusion_streams_config_h100_remote)
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
	mylinks = tntapi.parse_network_links(network)

	filter = testsuiteapi.get_filter()


	print("#Running ...")
	print("#1 - Load the fusion streams configuration on the local and remote h100.")
        step_1(network, conns, filter=filter)
 
sys.exit(main())
