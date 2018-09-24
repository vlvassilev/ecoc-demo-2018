#!/bin/sh -e
. ./start-ssh-server-func
instance=10
start_ssh_server $instance
#export HADMREG_INIT_ARG="verbose:ethernet:br0 0x1515 00:0A:35:03:43:41"
export HADMREG_INIT_ARG="verbose:netconf:ssh2:client 185.35.202.50 830 pi ecocdemo"
rm /tmp/ncxserver.${instance}830.sock || true ; export SYSTEM_ID="H100-1DOT6" ; export HADMREG_PRINT_ALL="1" ; gdb -ex run --args /usr/sbin/netconfd --module=hwmodel --module=fusion-h100-1dot6 --module=interfaces-state-h100 --module=interfaces-stats-pg165 --module=traffic-analyzer-h100 --module=traffic-generator --module=loopback-h100-1dot6  --module=hardware-fusion --module=network-bridge-h100-2dot0 --module=/usr/share/yuma/modules/transpacket/transpacket-h100-1dot6.yang --module=ietf-system --superuser=${USER}  --no-startup  --port=${instance}830 --ncxserver-sockname=/tmp/ncxserver.${instance}830.sock
