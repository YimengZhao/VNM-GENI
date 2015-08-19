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
t4_dpid = 10
host1_IP = '172.17.5.15'
host2_IP = '172.17.5.17'
host3_IP = '172.17.5.18'
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
barrier_count = 0

log = core.getLogger()


# migrate virtual network
def _migrate_vn ():
      threading.Timer(15, _initial_config).start()
      
      client_cmd = 'iperf -c 10.10.1.6 -u -t 100'
      #threading.Timer(20, _iperf, args=(host2_IP, client_cmd, )).start()

      # start migration after 1 minute
      print "start timer"
      threading.Timer(60, start_migration).start()

def _initial_config():
      print "initial configuration starts"
      _config_gateway(1)
      _config_tunnel_sw()
      _initialize_sw()
      
def _config_tunnel_sw():
      print 'bring down interfaces'
      remote_cmd.ssh_run_cmd(ovs1_IP, 'sudo ifconfig eth1 down')
      remote_cmd.ssh_run_cmd(ovs2_IP, 'sudo ifconfig eth1 down')
      remote_cmd.ssh_run_cmd(ovs3_IP, 'sudo ifconfig eth2 down')
      
def _initialize_sw():
      for connection in core.openflow.connections.values():
            if connection.dpid == ovs4_dpid:
                  _install_path_by_port(connection, 2, 1)
                  _install_path_by_port(connection, 3, 1)
                  _install_path_by_port(connection, 4, 1)
            elif connection.dpid == ovs5_dpid:
                  _install_path_by_port(connection, 2, 1)
                  _install_path_by_port(connection, 3, 1)
            elif connection.dpid == ovs6_dpid:
                  _install_path_by_port(connection, 1, 2)
                  _install_path_by_port(connection, 3, 2)
            elif connection.dpid == t4_dpid:
                  _install_path_by_port(connection, 4, 2)
                  _install_path_by_port(connection, 2, 4)
                  _install_path_by_port(connection, 1, 6)
                  _install_path_by_port(connection, 6, 1)
                  _install_path_by_port(connection, 5, 3)
                  _install_path_by_port(connection, 3, 5)
                  
def _install_path_by_port(connection, in_port, out_port):
      msg1 = of.ofp_flow_mod()
      msg1.match.in_port = in_port
      action = of.ofp_action_output(port = out_port)
      msg1.acctions.append(action)
      connection.send(msg1)

      

def _config_gateway(vn_id):
      log.info('config interface in gateways')
      remote_cmd.ssh_run_cmd(g1_IP,'sudo ifconfig eth2 up')
      remote_cmd.ssh_run_cmd(g1_IP,'sudo ifconfig eth3 down')
      remote_cmd.ssh_run_cmd(g2_IP,'sudo ifconfig eth2 up')
      remote_cmd.ssh_run_cmd(g2_IP,'sudo ifconfig eth3 down')
      remote_cmd.ssh_run_cmd(g3_IP,'sudo ifconfig eth2 up')
      remote_cmd.ssh_run_cmd(g3_IP,'sudo ifconfig eth3 down')
      
      log.info('install initial rules on gateways')
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
                        in_port = 1
                        out_port = 2
                        drop_port = 3
                  elif connection.dpid == g3_dpid:
                        in_port = 1
                        out_port = 2
                        drop_port = 3
            elif vn_id == 2:
                  if connection.dpid == g1_dpid:
                        in_port = 3
                        out_port = 1
                        drop_port = 2
                  elif connection.dpid == g2_dpid:
                        in_port = 1
                        out_port = 3
                        drop_port = 2
                  elif connection.dpid == g3_dpid:
                        in_port = 1
                        out_port = 3
                        drop_port = 2


            log.info('delete all flows at %s', connection.dpid)
            #delete all flows                                                   
            clear_msg = of.ofp_flow_mod(command = of.OFPFC_DELETE)
            connection.send(clear_msg)

            #add new flows                                                      
            log.info('add new flow')
            _gw_to_vn(connection, in_port, out_port, drop_port)



def _gw_to_vn(connection, in_port, out_port, drop_port):
      clear_msg = of.ofp_flow_mod(command = of.OFPFC_DELETE)
      connection.send(clear_msg)

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

def _iperf(IP, cmd):
  t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd, ))
  _config_gateway(1)
  time.sleep(5)
  t.start()

# start migration: copy the rules from old switches to new switches
def start_migration():
  print "Start migration..."

  log.info('move g1')
  # bring down the interfaces at gateways 
  print 'bring down the interfaces in gateways 1 and 2'
  remote_cmd.ssh_run_cmd(g1_IP,'sudo ifconfig eth2 down')
  remote_cmd.ssh_run_cmd(g2_IP,'sudo ifconfig eth2 down')

  for connection in core.openflow._connections.values():
    # move ovs-1
    if connection.dpid == ovs1_dpid:
          _request_flow_info(connection)

def _request_flow_info(connection):
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

 # send barrier message to ensure all flows has been installed             
  event.connection.send(of.ofp_barrier_request(xid=0x80000000))
  event.connection.addListenerByName("BarrierIn", _handle_flow_ready)


# insert rules to new switch
def _insert_flow_entries(event):
  stats = flow_stats_to_list(event.stats)
  port_dict={}
  if event.connection.dpid == ovs1_dpid:
        port_dict={2:2,3:3,4:4,1:1}
  elif event.connection.dpid == ovs2_dpid:
        port_dict={2:2,3:3,1:1}
  elif event.connection.dpid == ovs3_dpid:
        port_dict={1:2,3:1,2:3}
  _insert_flow_into_switch(stats, event.connection.dpid, port_dict)

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
  if event.ofp.xid != 0x80000000:
    return
  log.debug("barrier msg received from %s: ", event.connection.dpid)
  
  if event.connection.dpid == ovs1_dpid:
        log.info('redirect at gateway 1 and 2 to vn2')
        for connection in core.openflow._connections.values():
              if connection.dpid == g1_dpid:
                    _gw_to_vn(connection, 1, 3, 2)
              elif connection.dpid == g2_dpid:
                    _gw_to_vn(connection, 1, 3, 2)
        
        log.info('bring up interface in gateway 1 and 2 to vn2')
        remote_cmd.ssh_run_cmd(g1_IP,'sudo ifconfig eth3 up')
        remote_cmd.ssh_run_cmd(g2_IP,'sudo ifconfig eth3 up')
        
        log.info('move ovs2')
        for connection in core.openflow._connections.values():
              if connection.dpid == ovs2_dpid:
                    _request_flow_info(connection)
  elif event.connection.dpid == ovs2_dpid:
        log.info('bring down interfaces in gateway 3')
        remote_cmd.ssh_run_cmd(g3_IP,'sudo ifconfig eth2 down')

        log.info('move ovs3')
        for connection in core.openflow._connections.values():
              if connection.dpid == ovs3_dpid:
                    _request_flow_info(connection)
  elif event.connection.dpid == ovs3_dpid:
        log.info('redirect at gateway 3 to vn2')
        remote_cmd.ssh_run_cmd(g3_IP,'sudo ifconfig eth3 up')

  if barrier_count == 3:     
        _config_gateway(2)

        #bring down & up interface at gateways                                 
        print "bring down & up interfaces at gateways"
        remote_cmd.ssh_run_cmd(g1_IP, 'sudo ifconfig eth2 up')
        remote_cmd.ssh_run_cmd(g2_IP, 'sudo ifconfig eth3 up')
        remote_cmd.ssh_run_cmd(g3_IP, 'sudo ifconfig eth3 up')
  
  
def _drop(duration, connection, inport):
  if duration is not None:
    if not isinstance(duration, tuple):
      duration = (duration, duration)
    msg = of.ofp_flow_mod()
    msg.in_port = inport
    msg.idle_timeout = duration[0]
    msg.hard_timeout = duration[1]
    connection.send(msg)

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
  #if swap_inport:
    #if in_port == 1:
      #in_port = 2
    #elif in_port == 2:
      #in_port = 1
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
  _migrate_vn()

  # timer set to execute every five seconds
  #Timer(5, _timer_func, recurring=True)
