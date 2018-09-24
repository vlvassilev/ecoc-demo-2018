#!/bin/sh -e
. ./start-ssh-server-func
instance=20
start_ssh_server $instance
#export HADMREG_INIT_ARG="verbose:ethernet:br0 0x1515 00:0A:35:03:78:51"
export HADMREG_INIT_ARG="verbose:netconf:ssh2:client 185.35.202.50 17830 pi ecocdemo"
rm /tmp/ncxserver.${instance}830.sock || true ; export SYSTEM_ID="H100-1DOT0" ; export HADMREG_PRINT_ALL="1" ; gdb -ex run --args /usr/sbin/netconfd --port=${instance}830 --module=hwmodel --module=interfaces-fusion --module=interfaces-state-h100 --module=interfaces-stats-pg165 --module=traffic-analyzer-h100 --module=traffic-generator --module=network-bridge-h100-2dot0 --module=ietf-system --superuser=${USER}  --no-startup --ncxserver-sockname=/tmp/ncxserver.${instance}830.sock
