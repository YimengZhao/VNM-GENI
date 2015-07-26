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
newswitch_dpid = 2
oldswitch_dpid = 1
ovs1_IP = '128.163.232.70'
ovs2_IP = '128.163.232.84'
host1_IP = '172.17.5.26'
host2_IP = '172.17.1.4'

log = core.getLogger()

# handler for timer function that sends the requests to all the
# switches connected to the controller.
def _timer_func ():
  for connection in core.openflow._connections.values():
    if connection.dpid == oldswitch_dpid:
      connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
      # connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
      log.debug("Sent %i flow/port stats request(s)", len(core.openflow._connections))

# migrate virtual network
def _migrate_vn ():
  #read configuration file                                                      
  print "Reading configuration file..."
  with open('./pox/forwarding/configuration.txt', 'r') as in_file:
    expDict = json.load(in_file)

    for exp in expDict:
      print "Prepare stage: ", exp['prepare_time'], 's:'


      client_cmd = 'iperf -c 192.168.10.10 -u -t 100'
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

  # bring down the interfaces at ovs-1                                         
  print 'bring down the interfaces in ovs-1'
  remote_cmd.ssh_run_cmd(ovs1_IP,'sudo sh interface-down.sh')

  for connection in core.openflow._connections.values():
    if connection.dpid == oldswitch_dpid:
      connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
      log.debug("Sent %i flow/port stats request(s)", len(core.openflow._connections))


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
  for connection in core.openflow._connections.values():
    log.debug("connection dpid: %s", connection.dpid)
    if connection.dpid == newswitch_dpid:
      log.debug("install rule on switch %s", connection.dpid)
      for flow in stats:
        #log.debug("flow: %s", flow)
        msg = _flow_stats_to_flow_mod(flow)
        connection.send(msg)

      # send barrier message to ensure all flows has been installed
      connection.send(of.ofp_barrier_request(xid=0x80000000))
      connection.addListenerByName("BarrierIn", _handle_flow_ready)

# handler to bring down the interfaces in new VNs after all flows are installed
def _handle_flow_ready(event):
  if event.ofp.xid != 0x80000000:
    return
  log.debug("barrier msg received from %s: ", event.connection.dpid)

  log.info("install drop rule for 1s")
  _drop(1, event.connection, 1)
  _drop(1, event.connection, 2)
  # bring up the interfaces at ovs-2                                           
  print 'bring up the interfaces in ovs-2'
  remote_cmd.ssh_run_cmd(ovs2_IP,'sudo sh interface-up.sh')
  
  #cmd = "sudo sh interface-up.sh;sudo python VNM-dump.py " + ovs2_tcpdump_duration
  #t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(ovs2_IP, cmd, ))
  #t.start()

def _drop(duration, connection, inport):
  if duration is not None:
    if not isinstance(duration, tuple):
      duration = (duration, duration)
    msg = of.ofp_flow_mod()
    msg.in_port = inport
    msg.idle_timeout = duration[0]
    msg.hard_timeout = duration[1]
    connection.send(msg)

def _flow_stats_to_flow_mod (flow):
  actions = flow.get('actions', [])
  print "actions: ", actions
  if not isinstance(actions, list): actions = [actions]
  actions = [_dict_to_action(a) for a in actions]
  if 'output' in flow:   
    a = of.ofp_action_output(port=_fix_of_int(flow['output']))
    po.actions.append(a)

  fm = of.ofp_flow_mod()
  match_list = flow.get('match')

  in_port = 0
  port = match_list.get('in_port')
  if port == 1:
    in_port = 2
  elif port == 2:
    in_port = 1
  fm.match.in_port = in_port

  fm.match.dl_src = EthAddr(match_list.get('dl_src'))
  fm.match.dl_dst = EthAddr(match_list.get('dl_dst'))
  fm.match.dl_vlan = match_list.get('dl_vlan')
  if match_list.get('dl_type') == 'IP':
    fm.match.dl_type = 0x800
    print 'IP'
  elif match_list.get('dl_type') == 'ARP':
    fm.match.dl_type = 0x806
    print 'ARP'
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

def _dict_to_action (d) :
  d = d.copy()
  if 'port' in d:
    if d['port'] == 1:
      d['port']=2
    elif d['port'] == 2:
      d['port']=1

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
