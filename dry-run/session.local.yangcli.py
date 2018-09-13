#!/usr/bin/env python

import time
import sys, os
import argparse
from yangcli import yangcli
from lxml import etree
import yangrpc

def yangcli_ok_script(conn, yangcli_script):
	for line in yangcli_script.splitlines():
		line=line.strip()
		if not line:
			continue
		print("Executing: "+line)
		ok = yangcli(conn, line).xpath('./ok')
        	assert(len(ok)==1)

def main():
	print("""
#Description: Configure the H100 with example configuration from the userguide.
#Procedure:
#1 - Create the configuration described in the user guide.
#2 - Commit.
""")

	parser = argparse.ArgumentParser()
	parser.add_argument("--server", help="server name e.g. 127.0.0.1 or server.com (127.0.0.1 if not specified)")
	parser.add_argument("--user", help="username e.g. admin ($USER if not specified)")
	parser.add_argument("--port", help="port e.g. 830 (830 if not specified)")
	parser.add_argument("--password", help="password e.g. mypass123 (passwordless if not specified)")

	args = parser.parse_args()

	if(args.server==None or args.server==""):
		server="127.0.0.1"
	else:
		server=args.server

	if(args.port==None or args.port==""):
		port=830
	else:
		port=int(args.port)

	if(args.user==None or args.user==""):
		user=os.getenv('USER')
	else:
		user=args.user

	if(args.password==None or args.password==""):
		password=None
	else:
		password=args.password

	conn = yangrpc.connect(server, port, user, password, os.getenv('HOME')+"/.ssh/id_rsa.pub", os.getenv('HOME')+"/.ssh/id_rsa", "--dump-session=nc-session-")
	if(conn==None):
		print("Error: yangrpc failed to connect!")
		return(-1)

	time.sleep(1)


	#cleanup
	yangcli(conn, '''delete /fusion-streams''')
	ok = yangcli(conn, '''commit''').xpath('./ok')
	assert(len(ok)==1)

	yangcli_script='''
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='matched-tpid'] -- priority=gst filter/tpid=88F7 push-vlan-tag/vlanid=100 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false drop[out-port='e0']/pop-vlan-tag=true drop[out-port='e1']/pop-vlan-tag=true drop[out-port='e2']/pop-vlan-tag=true drop[out-port='e3']/pop-vlan-tag=true drop[out-port='e4']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n0'][filter-rule='unmatched'] -- priority=sm push-vlan-tag/vlanid=200 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1 forward/pop-vlan-tag=false

create /fusion-streams/aggregation[in-port='e0']/sm -- out-port=n1 push-vlan-tag/vlanid=10 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e1']/sm -- out-port=n1 push-vlan-tag/vlanid=11 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e2']/sm -- out-port=n1 push-vlan-tag/vlanid=12 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e3']/sm -- out-port=n1 push-vlan-tag/vlanid=13 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1
create /fusion-streams/aggregation[in-port='e4']/sm -- out-port=n1 push-vlan-tag/vlanid=14 push-vlan-tag/pcp=0 push-vlan-tag/tpid=9100 push-vlan-tag/cfi=1

create /fusion-streams/aggregation[in-port='e0']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e1']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e2']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e3']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1
create /fusion-streams/aggregation[in-port='e4']/gst -- out-port=n0 filter/ether-type=88F7 filter/tpid=88F7 filter/vlanid=1

create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='100'] -- priority=gst filter/tpid=9100 forward/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='200'] -- priority=sm filter/tpid=9100 forward/pop-vlan-tag=true

create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='10'] -- priority=sm filter/tpid=9100 drop[out-port='e0']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='11'] -- priority=sm filter/tpid=9100 drop[out-port='e1']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='12'] -- priority=sm filter/tpid=9100 drop[out-port='e2']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='13'] -- priority=sm filter/tpid=9100 drop[out-port='e3']/pop-vlan-tag=true
create /fusion-streams/drop-and-forward[in-port='n1'][filter-rule='14'] -- priority=sm filter/tpid=9100 drop[out-port='e4']/pop-vlan-tag=true

commit
'''
	yangcli_ok_script(conn, yangcli_script)


	return(0)
sys.exit(main())
