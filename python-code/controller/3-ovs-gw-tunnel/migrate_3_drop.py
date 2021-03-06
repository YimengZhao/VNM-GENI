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

flow_table = {}

log = core.getLogger()


# migrate virtual network
def _migrate_vn ():
      threading.Timer(10,_initial_config).start()
      
      client_cmd = 'iperf -c 10.10.1.6 -u -t 100'
      threading.Timer(30, _iperf, args=(host2_IP, client_cmd, )).start()

      # start migration after 1 minute
      log.info("start timer: start migration after 1 minutes")
      threading.Timer(60, start_migration).start()

def _initial_config():
      log.info("initial configuration starts")
      _initialize_sw()
      _config_gateway(1)
      
 
def _initialize_sw():
      log.info('install rules on vn-2 to direct all traffic to tunnel switch')
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
      msg1.actions.append(action)
      connection.send(msg1)


def _config_gateway(vn_id):
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
                  else:
                        continue
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
                  else:
                        continue
 
            _gw_to_vn(connection, in_port, out_port, drop_port)


def _gw_to_vn(connection, in_port, out_port, drop_port):
      _delete_flow_tables(connection)

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
  log.info("Start migration...")
  global start_time
  start_time = time.time()

  log.info('move ovs1')

  log.info('bring down the interfaces in ovs1')
  remote_cmd.ssh_run_cmd(ovs1_IP, 'sudo ifconfig eth2 down;sudo ifconfig eth3 down')

  log.info('request flow tables in ovs-1')
  for connection in core.openflow._connections.values():
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

  #store flow tables in local
  flow_table[event.connection.dpid] = stats

  #insert the flow enries into the new switches
  _insert_flow_entries(event)

  _set_tunnel_rule(event)

 # send barrier message to ensure all flows has been installed             
  event.connection.send(of.ofp_barrier_request(xid=0x80000000))
  event.connection.addListenerByName("BarrierIn", _handle_flow_ready)

def _set_tunnel_rule(event):
      if event.connection.dpid == ovs1_dpid:
            log.info('install rules on ovs-1 to direct traffic from/to tunnel')
            _delete_flow_tables(event.connection)
            _install_path_by_port(event.connection, 1, 4)
            _install_path_by_port(event.connection, 4, 1)
      elif event.connection.dpid == ovs2_dpid:
            log.info('install rules on ovs-2 to direct traffic from/to tunnel')
            _delete_flow_tables(event.connection)
            _install_path_by_port(event.connection, 1, 3)
            _install_path_by_port(event.connection, 3, 1)

            log.info('bring back the original flow tables on ovs-4')
            _bring_ovs_back(ovs1_dpid, flow_table[ovs1_dpid])
      elif event.connection.dpid == ovs3_dpid:
            log.info('bring back the original flow tables on ovs-5')
            _bring_ovs_back(ovs2_dpid, flow_table[ovs2_dpid])



# insert rules to new switch
def _insert_flow_entries(event):
  stats = flow_stats_to_list(event.stats)
  port_dict = {}
  insert_sw_id = 0
  if event.connection.dpid == ovs1_dpid:
        port_dict = {2:2,3:3,4:1}
        insert_sw_id = ovs4_dpid
  elif event.connection.dpid == ovs2_dpid:
        port_dict = {2:2,3:1}
        insert_sw_id = ovs5_dpid
  elif event.connection.dpid == ovs3_dpid:
        port_dict = {1:3,3:1}
        insert_sw_id = ovs6_dpid
  
  _insert_flow_into_switch(stats, insert_sw_id, port_dict)

def _insert_flow_into_switch(flows, switch_dpid, port_dict):
  for connection in core.openflow._connections.values():
    if connection.dpid == switch_dpid:
      log.info("delete existing flow tables on switch %s", connection.dpid)
      _delete_flow_tables(connection)

      log.info("install rule on switch %s", connection.dpid)
      for flow in flows:
        #log.info("flow: %s", flow)
        msg = _flow_stats_to_flow_mod(flow, port_dict)
        #log.info("msg: %s", msg)
        connection.send(msg)

      
def _delete_flow_tables(connection):
      clear_msg = of.ofp_flow_mod(command = of.OFPFC_DELETE)
      connection.send(clear_msg)

# insert rules to new switch                                                    
def _bring_ovs_back(sw_dpid, stats):
  port_dict = {}
  insert_sw_id = 0
  if sw_dpid == ovs1_dpid:
        port_dict = {2:2,3:3,4:4}
        insert_sw_id = ovs4_dpid
  elif sw_dpid == ovs2_dpid:
        port_dict = {2:2,3:3}
        insert_sw_id = ovs5_dpid
  elif sw_dpid == ovs3_dpid:
        port_dict = {1:3,3:1}
        insert_sw_id = ovs6_dpid

  _insert_flow_into_switch(stats, insert_sw_id, port_dict)



# handler to bring down the interfaces in new VNs after all flows are installed
def _handle_flow_ready(event):
  if event.ofp.xid != 0x80000000:
    return
  log.debug("barrier msg received from %s: ", event.connection.dpid)
  
  if event.connection.dpid == ovs1_dpid:
        log.info('bring up tunnel interfaces in ovs-1 and ovs-4')
        remote_cmd.ssh_run_cmd(ovs1_IP, 'sudo ifconfig eth1 up')
        remote_cmd.ssh_run_cmd(ovs4_IP, 'sudo ifconfig eth1 up')

        log.info('redirect at gateway 1 and 2 to vn2')
        for connection in core.openflow._connections.values():
              if connection.dpid == g1_dpid:
                    _gw_to_vn(connection, 1, 3, 2)
              elif connection.dpid == g2_dpid:
                    _gw_to_vn(connection, 1, 3, 2)


        log.info('movs ovs-2')
        log.debug('bring down interface in ovs-2')
        remote_cmd.ssh_run_cmd(ovs2_IP,'sudo ifconfig eth2 down')

        log.info('request flow tables in ovs2')
        for connection in core.openflow._connections.values():
              if connection.dpid == ovs2_dpid:
                    _request_flow_info(connection)

  elif event.connection.dpid == ovs2_dpid:
        log.info('bring up the interfaces in ovs-2 and ovs-5')
        remote_cmd.ssh_run_cmd(ovs2_IP,'sudo ifconfig eth1 up')
        remote_cmd.ssh_run_cmd(ovs5_IP,'sudo ifconfig eth1 up')

        log.info('bring down the interaces in ovs-4')
        #remote_cmd.ssh_run_cmd(ovs4_IP,'sudo ifconfig eth1 down')
        
        log.info('move ovs-3')
        log.debug('bring down the interfaces on ovs-3')
        remote_cmd.ssh_run_cmd(ovs3_IP,'sudo ifconfig eth1 down')

        log.info('request flow tables on ovs3')
        for connection in core.openflow._connections.values():
              if connection.dpid == ovs3_dpid:
                    _request_flow_info(connection)

  elif event.connection.dpid == ovs3_dpid:
        log.info('bring down the interaces in ovs-5')
        #remote_cmd.ssh_run_cmd(ovs4_IP,'sudo ifconfig eth1 down')

        log.info('redirect at gateway 3 to vn2')
        for connection in core.openflow._connections.values():
              if connection.dpid == g3_dpid:
                    _gw_to_vn(connection, 1, 3, 2)

        log.info('migration finished')
        global start_time
        migration_time = time.time() - start_time
        log.info("%s seconds", migration_time)
                  
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

  # migrate virtual network
  _migrate_vn()

