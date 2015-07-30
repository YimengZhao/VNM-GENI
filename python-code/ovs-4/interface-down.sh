#!/bin/bash
ifconfig eth1 down
ifconfig eth2 down
sudo ovs-ofctl del-flows br0

