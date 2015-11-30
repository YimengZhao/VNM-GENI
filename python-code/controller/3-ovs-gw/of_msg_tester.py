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
from repeated_timer import *

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
global xid
global start_time
LOG_FILE_DIR = 'of_time.log'
def _of_test():
      threading.Timer(15, _of_test_start).start()
      
def _of_test_start():
      rt = RepeatedTimer(10, _of_test_once, 50)
      rt.start()
      rt.wait()

def _of_test_once():
     
      log.info('get connections...')

      for connection in core.openflow._connections.values():
            if connection.dpid == g1_dpid:
                  global start_time
                  start_time = time.time()

                  msg = of.ofp_flow_mod()
                  msg.match.in_port = 1
                  msg.xid = of.generate_xid()
                  global xid
                  xid = msg.xid
                  connection.send(msg)

                  connection.send(of.ofp_barrier_request(xid=msg.xid))
                  connection.addListenerByName("BarrierIn", _handle_BarrierIn)


def _handle_BarrierIn(event):
      global xid
      if event.ofp.xid == xid:
            _log_data()

def _log_data():
      log.info('migration ends')
      global start_time
      exe_time = time.time() - start_time
      log.info('%s seconds' % exe_time)
      _write_to_log(LOG_FILE_DIR, '%s' % exe_time)

def _write_to_log(log_file_dir, data):
  if log_file_dir == '':
    return
  target = open(log_file_dir, 'a')
  target.write(str(data))
  target.write('\n')
  target.close()



    
# main functiont to launch the module
def launch ():
  from pox.lib.recoco import Timer

  _of_test()
