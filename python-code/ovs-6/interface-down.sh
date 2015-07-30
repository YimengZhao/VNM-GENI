#!/bin/bash
ifconfig eth1 down
sudo ovs-ofctl del-flows br0
