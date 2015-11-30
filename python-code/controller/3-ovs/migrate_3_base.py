#!/usr/bin/python
# Copyright 2015 Yimeng Zhao


# standard includes
from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
import json
import os
import time

import threading
import remote_cmd

# include as part of the betta branch
from pox.openflow.of_json import *

ovs2_tcpdump_duration = "60s"
ovs1_dpid = 1
ovs2_dpid = 2
ovs3_dpid = 3
ovs4_dpid = 4
ovs5_dpid = 5
ovs6_dpid = 6
ovs1_IP = '128.163.232.88'
ovs3_IP = '128.163.232.90'
ovs4_IP = '128.163.232.83'
ovs6_IP = '128.163.232.87'
host1_IP = '172.17.5.25'
host2_IP = '172.17.5.29'
host3_IP = '172.17.5.30'

log = core.getLogger()


# migrate virtual network
def _migrate_vn ():
  
      client_cmd = 'iperf -c 192.168.10.3 -t 100'
      threading.Timer(20, _iperf, args=(host1_IP, client_cmd, )).start()

      # start migration after 1 minute
      print "start timer"
      threading.Timer(60, start_migration).start()

def _iperf(IP, cmd):
  t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd, ))
  t.start()
  #remote_cmd.ssh_run_cmd(IP, cmd)

# start migration: copy the rules from old switches to new switches
def start_migration():
  print "Start migration..."

  # bring down the interfaces at ovs-1 and ovs-3 
  print 'bring down the interfaces in ovs-1'
  remote_cmd.ssh_run_cmd(ovs1_IP,'sudo sh interface-down.sh')
  remote_cmd.ssh_run_cmd(ovs3_IP,'sudo sh interface-down.sh')

  log.info("install drop rule for 1s")
  for connection in core.openflow._connections.values():
        if connection.dpid == ovs4_dpid or connection.dpid == ovs6_dpid:
              print connection.dpid
              _drop(2, connection, 1)
              _drop(2, connection, 2)
              #_drop(2, connection, 3)

  print 'bring up the interfaces in ovs-4 and ovs-6'
  remote_cmd.ssh_run_cmd(ovs4_IP,'sudo sh interface-up.sh')
  remote_cmd.ssh_run_cmd(ovs6_IP,'sudo sh interface-up.sh')


def _drop(duration, connection, inport):
  if duration is not None:
    if not isinstance(duration, tuple):
      duration = (duration, duration)
    msg = of.ofp_flow_mod()
    msg.in_port = inport
    msg.idle_timeout = duration[0]
    msg.hard_timeout = duration[1]
    connection.send(msg)


    
# main functiont to launch the module
def launch ():
  from pox.lib.recoco import Timer


  # migrate virtual network
  _migrate_vn()

  # timer set to execute every five seconds
  #Timer(5, _timer_func, recurring=True)
