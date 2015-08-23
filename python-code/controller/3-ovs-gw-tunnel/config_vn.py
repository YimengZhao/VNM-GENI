#!/usr/bin/python
# Copyright 2015 Yimeng Zhao


# standard includes
import os
import time

import threading
import remote_cmd


ovs2_tcpdump_duration = "60s"
ovs1_dpid = 1
ovs2_dpid = 2
ovs3_dpid = 3
ovs4_dpid = 4
ovs5_dpid = 5
ovs6_dpid = 6
g1_dpid = 7
g2_dpid = 8
g3_dpid = 9
t4_dpid = 16
host1_IP = '172.17.5.15'
host2_IP = '172.17.5.17'
host3_IP = '172.17.5.18'
g1_IP = '128.163.232.65'
g2_IP = '128.163.232.67'
g3_IP = '128.163.232.68'
host1 = '10.10.1.1'
host2 = '10.10.1.4'
host3 = '10.10.1.6'
ovs1_IP = '128.163.232.77'
ovs2_IP = '128.163.232.82'
ovs3_IP = '128.163.232.84'
ovs4_IP = '128.163.232.95'
ovs5_IP = '128.163.232.104'
ovs6_IP = '128.163.232.105'
t4_IP = '128.163.232.106'


      
def _config_sw_interface():
      print 'bring down interfaces to tunnel switch on vn-1'
      remote_cmd.ssh_run_cmd(ovs1_IP, 'sudo ifconfig eth1 down;sudo ifconfig eth2 up;sudo ifconfig eth3 up')
      remote_cmd.ssh_run_cmd(ovs2_IP, 'sudo ifconfig eth1 down;sudo ifconfig eth2 up')
      remote_cmd.ssh_run_cmd(ovs3_IP, 'sudo ifconfig eth2 down;sudo ifconfig eth1 up')

      print 'bring down interfaces to tunnel switch on vn-2'
      remote_cmd.ssh_run_cmd(ovs4_IP, 'sudo ifconfig eth1 down')
      remote_cmd.ssh_run_cmd(ovs5_IP, 'sudo ifconfig eth1 down')
      remote_cmd.ssh_run_cmd(ovs6_IP, 'sudo ifconfig eth2 down')


_config_sw_interface()
