#!/bin/bash

sudo tcpdump -i eth1 -w $1 &
pid1=$!
sudo tcpdump -i eth2 -w $2 &
pid2=$! 
sleep $3
sudo kill $pid1
sudo kill $pid2
