#!/bin/bash

for i in $(ls /sys/class/net/) ; do
    if [[ $i == "tap"* ]] ; then 
        echo "Bringing down TAP device...";
        sudo ip link set $i down;
        echo "Removing VLAN...";
        sudo ip link delete $i;
        echo "Deleting TAP device $i...";
        sudo tunctl -d $i;
        echo "Bringing down TAP device...";
        sudo ip link set $i down;
        echo "Removing VLAN...";
        sudo ip link delete $i;
        echo "Deleting TAP device $i...";
        sudo tunctl -d $i;
    fi;
done; 
