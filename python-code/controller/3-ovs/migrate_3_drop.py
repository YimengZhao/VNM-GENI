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
barrier_count = 0

log = core.getLogger()


# migrate virtual network
def _migrate_vn ():
  
      #threading.Timer(15, _exp_prep).start()
      client_cmd = 'iperf -c 192.168.10.3 -t 30'
      threading.Timer(20, _iperf, args=(host1_IP, client_cmd,)).start()

      # start migration after 1 minute
      print "start timer"
      threading.Timer(30, start_migration).start()

def _exp_prep():
      # bring up the interfaces at ovs-1 and ovs-3 
      print 'bring up the interfaces in ovs-1 and ovs-3'
      remote_cmd.ssh_run_cmd(ovs1_IP,'sudo sh interface-up.sh')
      remote_cmd.ssh_run_cmd(ovs3_IP,'sudo sh interface-up.sh')

      # bring down the interfaces at ovs-4 and ovs-6 
      print 'bring down the interfaces in ovs-4 and ovs-6'
      remote_cmd.ssh_run_cmd(ovs4_IP,'sudo sh interface-down.sh')
      remote_cmd.ssh_run_cmd(ovs6_IP,'sudo sh interface-down.sh')
  
def _threading_run_cmd(IP, cmd):
      t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd,))
      t.start()

def _iperf(IP, cmd):
      print 'start iperf'
      remote_cmd.ssh_run_cmd(IP, cmd)

# start migration: copy the rules from old switches to new switches
def start_migration():
  print "Start migration..."

  # bring down the interfaces at ovs-1 and ovs-3 
  '''print 'bring down the interfaces in ovs-1'
  remote_cmd.ssh_run_cmd(ovs1_IP,'sudo sh interface-down.sh')
  remote_cmd.ssh_run_cmd(ovs3_IP,'sudo sh interface-down.sh')'''
  
  
  for connection in core.openflow._connections.values():
    if connection.dpid == ovs1_dpid or connection.dpid == ovs2_dpid or connection.dpid == ovs3_dpid:
      connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
      log.debug("Sent %i flow/port stats request(s)", len(core.openflow._connections))

      # send barrier message to ensure all flows has been installed
      connection.send(of.ofp_barrier_request(xid=0x80000000))
      connection.addListenerByName("BarrierIn", _handle_flow_ready)



# handler to display flow statistics received in JSON format
# structure of event.stats is defined by ofp_flow_stats()
def _handle_flowstats_received (event):
  stats = flow_stats_to_list(event.stats)
  log.debug("FlowStatsReceived from %s: %s", 
   dpidToStr(event.connection.dpid), stats)
  
  #insert the flow enries into the new switches
  _insert_flow_entries(event)

  

# handler to display port statistics received in JSON format
def _handle_portstats_received (event):
  stats = flow_stats_to_list(event.stats)
  log.debug("PortStatsReceived from %s: %s", 
    dpidToStr(event.connection.dpid), stats)


# insert rules to new switch
def _insert_flow_entries(event):
  stats = flow_stats_to_list(event.stats)
  if event.connection.dpid == ovs1_dpid:
    for flow in stats:
          log.info("flow %s:", flow)
          _insert_flow_into_switch(stats, ovs4_dpid, True)
  elif event.connection.dpid == ovs2_dpid:
    _insert_flow_into_switch(stats, ovs5_dpid, False)
  elif event.connection.dpid == ovs3_dpid:
    _insert_flow_into_switch(stats, ovs6_dpid, False)

def _insert_flow_into_switch(flows, switch_dpid, swap_inport=False):
  for connection in core.openflow._connections.values():
    if connection.dpid == switch_dpid:
      log.info("install rule on switch %s", connection.dpid)
      for flow in flows:
        #log.info("flow: %s", flow)
        msg = _flow_stats_to_flow_mod(flow, swap_inport)
        #log.info("msg: %s", msg)
        connection.send(msg)

      
# handler to bring down the interfaces in new VNs after all flows are installed
def _handle_flow_ready(event):
  if event.ofp.xid != 0x80000000:
    return
  log.debug("barrier msg received from %s: ", event.connection.dpid)
  global barrier_count
  barrier_count = barrier_count+1

  if barrier_count == 3:
        
        log.info("install drop rule for 1s")
        for connection in core.openflow._connections.values():
              if connection.dpid == ovs4_dpid or connection.dpid == ovs6_dpid:
                    _drop(4, connection, 1)
                    _drop(4, connection, 2)
        
        # bring down the interfaces at ovs-1 and ovs-3 
        print 'bring down the interfaces in ovs-1'
        remote_cmd.ssh_run_cmd(ovs1_IP,'sudo sh interface-down.sh')
        remote_cmd.ssh_run_cmd(ovs3_IP,'sudo sh interface-down.sh')
  
        # bring up the interfaces at ovs-4 and ovs-6                                
        print 'bring up the interfaces in ovs-4 and ovs-6'
        _threading_run_cmd(ovs4_IP,'sudo sh interface-up.sh')
        _threading_run_cmd(ovs6_IP,'sudo sh interface-up.sh')
  
  
def _drop(duration, connection, inport):
  if duration is not None:
    if not isinstance(duration, tuple):
      duration = (duration, duration)
    msg = of.ofp_flow_mod()
    msg.in_port = inport
    msg.idle_timeout = duration[0]
    msg.hard_timeout = duration[1]
    connection.send(msg)

def _flow_stats_to_flow_mod (flow, swap_inport=False):
  actions = flow.get('actions', [])
  if not isinstance(actions, list): actions = [actions]
  actions = [_dict_to_action(a, swap_inport) for a in actions]
  if 'output' in flow:   
    a = of.ofp_action_output(port=_fix_of_int(flow['output']))
    po.actions.append(a)

  fm = of.ofp_flow_mod()
  match_list = flow.get('match')


  in_port = match_list.get('in_port')
  #if swap_inport:
    #if in_port == 1:
      #in_port = 2
    #elif in_port == 2:
      #in_port = 1
  fm.match.in_port = in_port

  fm.match.dl_src = EthAddr(match_list.get('dl_src'))
  fm.match.dl_dst = EthAddr(match_list.get('dl_dst'))
  fm.match.dl_vlan = match_list.get('dl_vlan')
  if match_list.get('dl_type') == 'IP':
    fm.match.dl_type = 0x800
  elif match_list.get('dl_type') == 'ARP':
    fm.match.dl_type = 0x806
  fm.match.new_tos = match_list.get('nw_tos')
  fm.match.nw_proto = match_list.get('nw_proto')

  fm.match.nw_src = match_list.get('nw_src')
  fm.match.nw_dst = match_list.get('nw_dst')
  fm.match.tp_src = match_list.get('tp_src')
  fm.match.tp_dst = match_list.get('tp_dst')

 
  fm.actions = actions

  for k in ['cookie', 'idle_timeout', 'hard_timeout', 'priority']:
    if k in flow:
      setattr(fm, k, flow[k])
      #i = 0
  return fm

def _dict_to_action (d, swap_port) :
  d = d.copy()
  #if swap_port:
        #if 'port' in d:
              #if d['port'] == 1:
                    #d['port']=2
              #elif d['port'] == 2:
                    #d['port']=1

  t = d['type'].upper()
  del d['type']
  if not t.startswith("OFPAT_"): t = "OFPAT_" + t
  t = of.ofp_action_type_rev_map[t]
  cls = of._action_type_to_class[t]
  a = cls(**d)
  return a

    
# main functiont to launch the module
def launch ():
  from pox.lib.recoco import Timer

  # attach handsers to listners
  core.openflow.addListenerByName("FlowStatsReceived", 
    _handle_flowstats_received) 
  core.openflow.addListenerByName("PortStatsReceived", 
    _handle_portstats_received) 

  # migrate virtual network
  _migrate_vn()

  # timer set to execute every five seconds
  #Timer(5, _timer_func, recurring=True)
