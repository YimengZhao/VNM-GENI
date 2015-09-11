
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
from gw_config import *

# include as part of the betta branch
from pox.openflow.of_json import *


ovs1_dpid = 1
ovs2_dpid = 2
ovs3_dpid = 3
ovs4_dpid = 4
ovs5_dpid = 5
ovs6_dpid = 6
host1_IP = '172.17.2.11'
host2_IP = '172.17.5.4'
host3_IP = '172.17.5.5'
g1_IP = '128.163.232.71'
g2_IP = '128.163.232.72'
g3_IP = '128.163.232.73'
copy_barrier_id = 0x80000000

log = core.getLogger()

def _exp_prepare():
      threading.Timer(15, _config_gateway, args=(1, )).start()
      
# migrate virtual network
def _migrate_vn ():
      global first_time
      if first_time:
            print 'start iperf'
            client_cmd = 'iperf -c 10.10.1.1 -u -b 40m -t 610'
            _iperf(host2_IP, client_cmd)
            #_iperf(host2_IP, client_cmd)
            first_time = False

      global barrier_count
      barrier_count = 0

      _config_gateway(1)

      # start migration after 1 minute
      print "start migration after 30s"
      #threading.Timer(30, start_migration).start()


def _config_gateway(vn_id):
      gw_config = ConfigGWRequest()
      gw_config._config_gw(vn_id)

            
def _iperf(IP, cmd):
  t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd, ))
  t.start()

# start migration: copy the rules from old switches to new switches
def start_migration():
  
  log.info('start copying flow tables...')

  for connection in core.openflow._connections.values():
    if connection.dpid == ovs1_dpid or connection.dpid == ovs2_dpid or connection.dpid == ovs3_dpid:
      connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
      log.debug("Sent %i flow/port stats request(s)", len(core.openflow._connections))

      # send barrier message to ensure all flows has been installed
      connection.send(of.ofp_barrier_request(xid=copy_barrier_id))
      connection.addListenerByName("BarrierIn", _handle_flow_ready)
      
      global barrier_count
      barrier_count += 1


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
  port_dict = {}
  insert_switch_id = 0
  if event.connection.dpid == ovs1_dpid:
        port_dict = {1:2,2:1,3:3}
        insert_switch_id = ovs4_dpid
  elif event.connection.dpid == ovs2_dpid:
        port_dict = {1:2,2:1}
        insert_switch_id = ovs5_dpid
  elif event.connection.dpid == ovs3_dpid:
        port_dict = {1:1,2:2}
        insert_switch_id = ovs6_dpid
  _insert_flow_into_switch(stats, insert_switch_id,port_dict)


def _insert_flow_into_switch(flows, switch_dpid, port_dict):
  for connection in core.openflow._connections.values():
    if connection.dpid == switch_dpid:
      log.info("install rule on switch %s", connection.dpid)
      for flow in flows:
        #log.info("flow: %s", flow)
        msg = _flow_stats_to_flow_mod(flow, port_dict)
        #log.info("msg: %s", msg)
        connection.send(msg)

      
# handler to bring down the interfaces in new VNs after all flows are installed
def _handle_flow_ready(event):
  if event.ofp.xid == copy_barrier_id:
        log.info("barrier msg received from %s: ", event.connection.dpid)
  
        global barrier_count
        if barrier_count <= 0:
              return

        barrier_count -= 1

        if barrier_count <= 0:
              log.info("Start migration...")

              log.info('install rules on gw to redirect traffic')
              _config_gateway(2)

              barrier_count = 0

def _flow_stats_to_flow_mod (flow, port_dict):
  actions = flow.get('actions', [])
  if not isinstance(actions, list): actions = [actions]
  actions = [_dict_to_action(a, port_dict) for a in actions]
  if 'output' in flow:   
    a = of.ofp_action_output(port=_fix_of_int(flow['output']))
    po.actions.append(a)

  fm = of.ofp_flow_mod()
  match_list = flow.get('match')


  in_port = match_list.get('in_port')
  fm.match.in_port = port_dict[in_port]

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

def _dict_to_action (d, port_dict) :
  d = d.copy()
  
  if 'port' in d:
        d['port'] = port_dict[d['port']]
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
  global first_time
  first_time = True
  _exp_prepare()
  Timer(60, _migrate_vn, recurring=True)

