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

# import customer class
import remote_cmd
from gw_config import *
from gw_config_rule_seq import *
from repeated_timer import *

# include as part of the betta branch
from pox.openflow.of_json import *
import sys

ovs1_dpid = 1
ovs2_dpid = 2
ovs3_dpid = 3
ovs4_dpid = 4
ovs5_dpid = 5
ovs6_dpid = 6
h1_IP = '10.10.1.1'
h2_IP = '10.10.1.4'
h3_IP = '10.10.1.6'
host1_IP = '172.17.2.11'
host2_IP = '172.17.5.4'
host3_IP = '172.17.5.5'
g1_IP = '128.163.232.71'
g2_IP = '128.163.232.72'
g3_IP = '128.163.232.73'
ovs1_IP = '128.163.232.91'
ovs2_IP = '128.163.232.92'
ovs3_IP = '128.163.232.93'
ovs4_IP = '128.163.232.96'
ovs5_IP = '128.163.232.97'
ovs6_IP = '128.163.232.98'
copy_barrier_id = 0x80000000

log = core.getLogger()

class VnMigrateExp:

       def __init__(self):
              self.name = 'exp'

       def multiNode_exp_start(self):
              _config_gateway(1, '')


              '''print 'start h1-h2'
              self._expset_start('h1', 'h2')'''

              print 'start h1-h3'
              self._expset_start('h1', 'h3')

              '''print 'start h2-h1'
              self._expset_start('h2', 'h1')

              print 'start h2-h3'
              self._expset_start('h2', 'h3')

              print 'start h3-h1'
              self._expset_start('h3', 'h1')

              print 'start h3-h2'
              self._expset_start('h3', 'h2')'''



       def _expset_start(self, client, server):
              interval = 60*(11 + 1)
              exp_interval = 60

              server_IP = ''
              if server == 'h1':
                     server_IP = host1_IP
              elif server == 'h2':
                     server_IP = host2_IP
              elif server == 'h3':
                     server_IP = host3_IP

              log_duration = interval
              '''log_file = './iperf-result/' + client + '-' + server + '-base.log' 
              cmd = 'sudo sh udp_server.sh ' + log_file + ' ' + str(log_duration)
              self._start_udpserver(server_IP, cmd)
              self._exp_start(ExpType.base, client, server)
              time.sleep(exp_interval)'''
              
              log_file = './iperf-result/' + client + '-' + server + '-sym.log' 
              cmd = 'sudo sh udp_server.sh ' + log_file + ' ' + str(log_duration)
              self._start_udpserver(server_IP, cmd)
              self._exp_start(ExpType.sym, client, server)
              time.sleep(exp_interval)

              '''log_file = './iperf-result/' + client + '-' + server + '-asym.log' 
              cmd = 'sudo sh udp_server.sh ' + log_file + ' ' + str(log_duration)
              self._start_udpserver(server_IP, cmd)
              self._exp_start(ExpType.asym, client, server)
              time.sleep(exp_interval)       

              log_file = './iperf-result/' + client + '-' + server + '-opt.log' 
              cmd = 'sudo sh udp_server.sh ' + log_file + ' ' + str(log_duration)
              self._start_udpserver(server_IP, cmd)
              self._exp_start(ExpType.opt, client, server)
              time.sleep(exp_interval)'''

       def _exp_start(self, exp_type, client, server):
              interval = 60
              count = 11

              '''rt1 = RepeatedTimer(interval, self._migrate_vn, count, exp_type, client, server, '10')
              rt1.start()
              rt1.wait()

              rt2 = RepeatedTimer(interval, self._migrate_vn, count, exp_type, client, server, '30')
              rt2.start()
              rt2.wait()

              rt3 = RepeatedTimer(interval, self._migrate_vn, count, exp_type, client, server, '60')
              rt3.start()
              rt3.wait()'''

              rt4 = RepeatedTimer(interval, self._migrate_vn, count, exp_type, client, server, '200')
              rt4.start()
              rt4.wait()
              print client,'-', server,':',str(exp_type),' finish'

             

       # migrate virtual network
       def _migrate_vn (self, exp_type, client, server, data_rate):
              ctrl_log_file_pref = './vnm_log/' + client + '-' + server + '-' + data_rate
              client_log_dir = './client-sent/' + client + '-' + server + '-' + str(exp_type) + '.log'
              gw_log_pref = './gw_log/' + client + '-' + server + '-' + str(exp_type)

              client_IP = ''
              server_IP = ''
              if client == 'h1':
                     client_IP = host1_IP
              elif client == 'h2':
                     client_IP = host2_IP
              elif client == 'h3':
                     client_IP = host3_IP

              if server == 'h1':
                     server_IP = h1_IP
              elif server == 'h2':
                     server_IP = h2_IP
              elif server == 'h3':
                     server_IP = h3_IP

              global barrier_count
              barrier_count = 0

              self._config_gateway(1, exp_type, ctrl_log_file_pref)


              # start migration after 1 minute
              if exp_type != ExpType.base:
                     print "start migration after 30s"
                     threading.Timer(30, self.start_migration).start()
              threading.Timer(10, self._start_gw_log, args=(g1_IP, gw_log_pref, )).start()
              threading.Timer(10, self._start_gw_log, args=(g2_IP, gw_log_pref, )).start()
              threading.Timer(10, self._start_gw_log, args=(g3_IP, gw_log_pref, )).start()

              threading.Timer(20, self._start_ovs_log, args=(ovs1_IP, gw_log_pref, )).start()
              threading.Timer(20, self._start_ovs_log, args=(ovs2_IP, gw_log_pref, )).start()
              threading.Timer(20, self._start_ovs_log, args=(ovs3_IP, gw_log_pref, )).start()   
             
              threading.Timer(20, self._start_ovs_log, args=(ovs4_IP, gw_log_pref, )).start()
              threading.Timer(20, self._start_ovs_log, args=(ovs5_IP, gw_log_pref, )).start()
              threading.Timer(20, self._start_ovs_log, args=(ovs6_IP, gw_log_pref, )).start()   
             
              client_cmd = 'sudo python udp_client.py ' + server_IP + ' ' + data_rate + ' ' + client_log_dir              
              threading.Timer(25, self._start_udpclient, args=(client_IP, client_cmd, )).start()


       def _config_gateway(self, vn_id, exp_type, log_file_pref):
              if exp_type == ExpType.base:
                     gw_config = ConfigGWRequest_sym('')
                     gw_config._config_gw(vn_id, True)
              elif exp_type == ExpType.sym:
                     gw_config = ConfigGWRequest_sym(log_file_pref + "-sym.log")
                     gw_config._config_gw(vn_id, False)
              elif exp_type == ExpType.asym:
                     gw_config = ConfigGWRequest_sym(log_file_pref + "-asym.log")
                     gw_config._config_gw(vn_id, True)
              elif exp_type == ExpType.opt:
                     gw_config = ConfigGWRequest_opt(log_file_pref + "-opt.log")
                     gw_config._config_gw(vn_id)



       def _start_gw_log(self, IP, dump_file_pref):
              print 'start tcpdump at ', IP
              dump_file_1 = dump_file_pref + '-eth1.log'
              dump_file_2 = dump_file_pref + '-eth2.log'
              dump_file_3 = dump_file_pref + '-eth3.log'
              cmd = 'sudo sh tcpdump.sh ' + dump_file_1 + ' ' + dump_file_2 + ' ' + dump_file_3 + ' 40s'
              t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd,))
              t.start()

       def _start_ovs_log(self, IP, dump_file_pref):
              print 'start tcpdump at ', IP
              dump_file_1 = dump_file_pref + '-eth1.log'
              dump_file_2 = dump_file_pref + '-eth2.log'
              dump_file_3 = dump_file_pref + '-eth3.log'
              cmd = ''
              if IP == ovs4_IP or IP == ovs1_IP:
                     cmd = 'sudo sh tcpdump.sh ' + dump_file_1 + ' ' + dump_file_2 + ' ' + dump_file_3 + ' 20s'
              else:
                     cmd = 'sudo sh tcpdump.sh ' + dump_file_1 + ' ' + dump_file_2 + ' 20s'
              t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd,))
              t.start()

       def _start_udpserver(self, IP, cmd):
              print 'start udpserver at ', IP, ':', cmd
              t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd, ))
              t.start()

       def _start_udpclient(self, IP, cmd):
              print 'start udpclient at ', IP, ':', cmd
              t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd, ))
              t.start()

       # start migration: copy the rules from old switches to new switches
       def start_migration(self):

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


def _config_gateway(vn_id, log_file):
      gw_config = ConfigGWRequest_sym(log_file)
      gw_config._config_gw(vn_id, True)

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
      log.debug("install rule on switch %s", connection.dpid)
      for flow in flows:
        #log.info("flow: %s", flow)
        msg = _flow_stats_to_flow_mod(flow, port_dict)
        #log.info("msg: %s", msg)
        connection.send(msg)

      
# handler to bring down the interfaces in new VNs after all flows are installed
def _handle_flow_ready(event):
  if event.ofp.xid == copy_barrier_id:
        #log.info("barrier msg received from %s: ", event.connection.dpid)
  
        global barrier_count
        if barrier_count <= 0:
              return

        barrier_count -= 1

        if barrier_count <= 0:
               time.sleep(1)
               log.info("Start migration...")

               log.info('install rules on gw to redirect traffic')
               _config_gateway(2, '')

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
  exp = VnMigrateExp()
  threading.Timer(15, exp.multiNode_exp_start).start()

  #Timer(60, _migrate_vn, recurring=True)

class ExpType:
      base = 1
      sym = 2
      asym = 3
      opt = 4
