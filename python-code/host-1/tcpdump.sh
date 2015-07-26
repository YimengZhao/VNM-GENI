#!/bin/bash

sudo tcpdump -i eth1 -w $1 &
pid1=$! 
sleep $2
sudo kill $pid1

