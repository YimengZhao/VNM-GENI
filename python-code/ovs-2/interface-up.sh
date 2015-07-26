#!/bin/bash
ifconfig eth1 up
ifconfig eth2 up
sudo tcpdump -i eth2 -w eth2.pcap
