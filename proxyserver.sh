#!/usr/bin/env bash

addr=$1
port=$2
mgmt_ip_mac=127.0.0.1
#mgmt_ip_linux=`ip -f inet addr show dev ens160 |sed -n 's/^[ ]*inet \([^/]\{1,\}\).*$/\1/p'`
echo "If running on macOS machine https://$mgmt_ip_mac:1088"
echo "If running on VM linux machine https://$mgmt_ip_linux:1088"
echo "Press Ctrl-C to quit"
socat tcp-listen:1088,reuseaddr,fork tcp:$addr:$port

