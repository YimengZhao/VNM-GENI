#!/usr/bin/python
# Copyright 2012 William Yu
# wyu@ateneo.edu
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX. If not, see <http://www.gnu.org/licenses/>.
#

"""
This is a demonstration file created to show how to obtain flow 
and port statistics from OpenFlow 1.0-enabled switches. The flow
statistics handler contains a summary of web-only traffic.
"""

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

newswitch_dpid = 2
oldswitch_dpid = 1
ovs1_IP = '128.163.232.70'
ovs2_IP = '128.163.232.84'

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

      # bring down interface at ovs-1 after 1 minute
      #remote_cmd.ssh_run_cmd(ovs1_IP,'sudo at -f sh interface-down.sh -v now + 1 minute')
      #remote_cmd.ssh_run_cmd('128.163.232.70','sudo at -f interface-down.sh -v now + 1 minute')
      print 'send remote cmd to bring down interface on ovs-1'
      remote_cmd.ssh_run_cmd('128.163.232.70','sudo at -f interface-down.sh -v now + 1 minute')

      # start migration after 1 minute
      threading.Timer(60, start_migration).start()

def start_migration():
  print "Start migration..."
      
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

  # bring up the interfaces at ovs-2
  print 'bring up the interfaces in ovs-2'
  remote_cmd.ssh_run_cmd(ovs2_IP,'sudo sh interface-up.sh -v')


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

  fm.match.in_port = match_list.get('in_port')

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
