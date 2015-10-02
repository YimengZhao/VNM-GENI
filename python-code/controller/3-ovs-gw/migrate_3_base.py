
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
import sys

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
      threading.Timer(15, _config_gateway, args=(1,)).start()
      
# migrate virtual network
def _migrate_vn ():
      global first_time
      if first_time:
            global exp_count
            exp_count = 0
            global client_IP
            client_IP = host3_IP
            first_time = False

      global barrier_count
      barrier_count = 0

      #_config_gateway(1)

      global client_cmd
      if exp_count < 11:
            client_cmd = 'sudo python udp_client.py 10'
      elif exp_count < 21:
            client_cmd = 'sudo python udp_client.py 30'
      elif exp_count < 31:
            client_cmd = 'sudo python udp_client.py 60'
      elif exp_count < 42:
            client_cmd = 'sudo python udp_client.py 200'
      else:
            print 'exit'
            sys.exit(1)

      threading.Timer(25, _iperf, args=(client_IP, client_cmd, )).start()
      threading.Timer(55, _iperf, args=(client_IP, client_cmd, )).start()
      exp_count += 1

def _config_gateway(vn_id):
      gw_config = ConfigGWRequest()
      gw_config._config_gw(vn_id)

            
def _iperf(IP, cmd):
  t = threading.Thread(target=remote_cmd.ssh_run_cmd, args=(IP, cmd, ))
  t.start()


    
# main functiont to launch the module
def launch ():
  from pox.lib.recoco import Timer

  # migrate virtual network
  global first_time
  first_time = True
  _exp_prepare()
  Timer(60, _migrate_vn, recurring=True)

