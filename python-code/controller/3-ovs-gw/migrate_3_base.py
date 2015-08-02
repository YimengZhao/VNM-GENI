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
g1_dpid = 7
g2_dpid = 8
g3_dpid = 9
host1_IP = '172.17.2.11'
host2_IP = '172.17.5.4'
host3_IP = '172.17.5.5'
g1_IP = '128.163.232.71'
g2_IP = '128.163.232.72'
g3_IP = '128.163.232.73'

log = core.getLogger()


# migrate virtual network
def _migrate_vn ():
  
      client_cmd = 'iperf -c 10.10.1.4 -t 100'
      threading.Timer(20, _iperf, args=(host1_IP, client_cmd, )).start()

      # start migration after 1 minute
      print "start timer"
      threading.Timer(60, start_migration).start()

def _config_gateway(vn_id):
      print 'config gateways'
      in_port = 0
      out_port = 0
      drop_port = 0
      for connection in core.openflow._connections.values():
            
            if vn_id == 1:
                  if connection.dpid == g1_dpid:
                        in_port = 1
                        out_port = 2
                        drop_port = 3
                  elif connection.dpid == g2_dpid:
                        in_port = 2
                        out_port = 3
                        drop_port = 1
                  elif connection.dpid == g3_dpid:
                        in_port = 1
                        out_port = 2
                        drop_port = 3
                  else:
                        continue
            elif vn_id == 2:
                  if connection.dpid == g1_dpid:
                        in_port = 1
                        out_port = 3
                        drop_port = 2
                  elif connection.dpid == g2_dpid:
                        in_port = 2
                        out_port = 1
                        drop_port = 3
                  elif connection.dpid == g3_dpid:
                        in_port = 3
                        out_port = 2
                        drop_port = 1
                  else:
                        continue
                        

            log.info('delete all flows at %s', connection.dpid)
            #delete all flows
            clear_msg = of.ofp_flow_mod(command = of.OFPFC_DELETE)
            connection.send(clear_msg)

            #add new flows
            log.info('add new flow')
            msg1 = of.ofp_flow_mod()
            msg1.match.in_port = in_port
            action = of.ofp_action_output(port = out_port)
            msg1.actions.append(action)
            connection.send(msg1)

            msg2 = of.ofp_flow_mod()
            msg2.match.in_port = out_port
            action = of.ofp_action_output(port = in_port)
            msg2.actions.append(action)
            connection.send(msg2)

            msg3 = of.ofp_flow_mod()
            msg3.match.in_port = drop_port
            connection.send(msg3)


def _iperf(IP, cmd):
  t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd, ))
  _config_gateway(1)
  time.sleep(5)
  t.start()


# start migration: copy the rules from old switches to new switches
def start_migration():
  print "Start migration..."

  # switch port at gateways 
  print 'switch at the gateway'
  _config_gateway(2)

  #bring down & up interface at gateways                                       
  print "bring down & up interfaces at gateways"
  remote_cmd.ssh_run_cmd(g1_IP, 'sudo sh enable-vn2.sh')
  remote_cmd.ssh_run_cmd(g2_IP, 'sudo sh enable-vn2.sh')
  remote_cmd.ssh_run_cmd(g3_IP, 'sudo sh enable-vn2.sh')



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
