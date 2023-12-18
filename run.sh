#!/bin/bash

FIRST_INTERFACE=$(ip link show | grep -v 'lo:' | awk '/^[0-9]+:/{print substr($2, 1, length($2)-1)}' | head -n 1)

if [ -z "$FIRST_INTERFACE" ]; then
    echo "No network interface found."
    exit 1
fi

#echo $FIRST_INTERFACE
cd ebpf-xdp/src
sudo ./xdp_prog_user -d $FIRST_INTERFACE --filename xdp_prog_kern.o --progname xdp_prog_main -S

