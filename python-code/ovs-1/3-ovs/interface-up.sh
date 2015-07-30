#!/bin/bash
ifconfig eth1 up
ifconfig eth2 up
sudo ovs-ofctl del-flows br0
