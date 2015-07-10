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

# include as part of the betta branch
from pox.openflow.of_json import *

newswitch_dpid = 2
oldswitch_dpid = 1
log = core.getLogger()

# handler for timer function that sends the requests to all the
# switches connected to the controller.
def _timer_func ():
  for connection in core.openflow._connections.values():
    if connection.dpid == oldswitch_dpid:
      connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
      # connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
      log.debug("Sent %i flow/port stats request(s)", len(core.openflow._connections))

# handler to display flow statistics received in JSON format
# structure of event.stats is defined by ofp_flow_stats()
def _handle_flowstats_received (event):
  stats = flow_stats_to_list(event.stats)
  #log.debug("FlowStatsReceived from %s: %s", 
   # dpidToStr(event.connection.dpid), stats)
  
  _insert_rule(event)

  # Get number of bytes/packets in flows for web traffic only
  web_bytes = 0
  web_flows = 0
  web_packet = 0
  for f in event.stats:
    if f.match.tp_dst == 80 or f.match.tp_src == 80:
      web_bytes += f.byte_count
      web_packet += f.packet_count
      web_flows += 1
  log.info("Web traffic from %s: %s bytes (%s packets) over %s flows", 
    dpidToStr(event.connection.dpid), web_bytes, web_packet, web_flows)

# handler to display port statistics received in JSON format
def _handle_portstats_received (event):
  stats = flow_stats_to_list(event.stats)
  log.debug("PortStatsReceived from %s: %s", 
    dpidToStr(event.connection.dpid), stats)

# insert rules to new switch
def _insert_rule(event):
  stats = flow_stats_to_list(event.stats)
  for connection in core.openflow._connections.values():
    if connection.dpid == newswitch_dpid:
      for flow in stats:
        msg = _flow_stats_to_flow_mod(flow)
        connection.send(msg)

def _flow_stats_to_flow_mod (flow):
  match = flow.get('match')
  if match is None:
    match = of.ofp_match()
  else:
    match = _dict_to_match(match)

  actions = flow.get('actions', [])
  if not isinstance(actions, list): actions = [actions]
  actions = [dict_to_action(a) for a in actions]
  if 'output' in flow:
    a = of.ofp_action_output(port=_fix_of_int(flow['output']))
    po.actions.append(a)

  #fm = of.ofp_flow_mod(match = match)
  fm = of.ofp_flow_mod()
  fm.actions = actions

  for k in ['cookie','idle_timeout','hard_timeout','priority']:
    if k in flow:
      setattr(fm, k, flow[k])

  return fm


def _dict_to_match (jm):
  m = of.ofp_match()
  m.in_port = jm.get('in_port')
  m.dl_src = jm.get('dl_src')
  m.dl_dst = jm.get('dl_dst')
  if 'dl_vlan'     in jm: m.dl_vlan     = jm['dl_vlan']
  if 'dl_vlan_pcp' in jm: m.dl_vlan_pcp = jm['dl_vlan_pcp']
  m.dl_type = jm.get('dl_type')
  if 'nw_tos'      in jm: m.nw_tos      = jm['nw_tos']
  m.nw_proto = jm.get('nw_proto')
  m.nw_src = jm.get('nw_src')
  m.nw_dst = jm.get('nw_dst')
  m.tp_src = jm.get('tp_src')
  m.tp_dst = jm.get('tp_dst')
  #print jm,"\n",m
  return m


    
# main functiont to launch the module
def launch ():
  from pox.lib.recoco import Timer

  # attach handsers to listners
  core.openflow.addListenerByName("FlowStatsReceived", 
    _handle_flowstats_received) 
  core.openflow.addListenerByName("PortStatsReceived", 
    _handle_portstats_received) 

  # timer set to execute every five seconds
  Timer(5, _timer_func, recurring=True)
