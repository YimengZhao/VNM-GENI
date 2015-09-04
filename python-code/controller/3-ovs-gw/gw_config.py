import sys
from pox.lib.util import dpidToStr, strToDPID, fields_of
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.openflow.of_json import *
from pox.web.jsonrpc import JSONRPCHandler, make_error
import threading
import time

log = core.getLogger()

g1_dpid = 7
g2_dpid = 8
g3_dpid = 9
LOG_FILE_DIR = 'vnm_log.txt'

class GWRequest():
  def __init__(self):
    self.done = False
    xid = of.generate_xid()
    self.xid = xid
    self.count = 0

  def _get_response(self):
    while (self.done==False):
      time.sleep(0.1)
    

  def _send_msg(self, con, msgs):
    for msg in msgs:
      msg.xid = self.xid
      con.send(msg)

    self.count += 1
    con.send(of.ofp_barrier_request(xid=self.xid))
    con.addListenerByName("BarrierIn", self._handle_BarrierIn)

  def _handle_BarrierIn(self, event):
    log.info("receive barrier msg from gw %s", event.connection.dpid)
    if event.ofp.xid != self.xid:
      return
    self.count -= 1
    if self.count <= 0:
      self.done = True
      self.callback(event.connection.dpid)

  def bind_to(self, callback):
    self.callback = callback
    
class ConfigGWRequest ():
  def __init__(self):
    self.gw_record = {g1_dpid:0, g2_dpid:0, g3_dpid:0}

  def _config_gw (self, vn_id):
    self.start_time = time.time()

    log.info('start configuring gateways in to vn %s', vn_id)
    in_port = 0
    out_port = 0
    drop_port = 0
    threads = []

    for connection in core.openflow._connections.values():
      if vn_id == 1:
        if connection.dpid == g1_dpid:
          in_port = 1
          out_port = 2
          drop_port = 3
        elif connection.dpid == g2_dpid:
          in_port = 2
          out_port = 3
          drop_port = 1
        elif connection.dpid == g3_dpid:
          in_port = 1
          out_port = 2
          drop_port = 3
        else:
          continue
      elif vn_id == 2:
        if connection.dpid == g1_dpid:
          in_port = 1
          out_port = 3
          drop_port = 2
        elif connection.dpid == g2_dpid:
          in_port = 2
          out_port = 1
          drop_port = 3
        elif connection.dpid == g3_dpid:
          in_port = 2
          out_port = 3
          drop_port = 1
        else:
          continue
        
      msgs = []

      msg3 = of.ofp_flow_mod()
      msg3.match.in_port = drop_port
      #msgs.append(msg3)

      msg1 = of.ofp_flow_mod()
      msg1.match.in_port = in_port
      action = of.ofp_action_output(port = out_port)
      msg1.actions.append(action)
      msgs.append(msg1)

      msg2 = of.ofp_flow_mod()
      msg2.match.in_port = out_port
      action = of.ofp_action_output(port = in_port)
      msg2.actions.append(action)
      msgs.append(msg2)


      gw_request = GWRequest()
      gw_request.bind_to(self._gw_config_finish)
      gw_request._send_msg(connection, msgs)

  def _gw_config_finish(self, sw_dpid):
    self.gw_record[sw_dpid] = 1
    for key, value in self.gw_record.iteritems():
      if value == 0:
        print 'not ready'
        return
    log.info('migration ends')
    migration_time = time.time() - self.start_time
    log.info('%s seconds', migration_time)
    _write_to_log(LOG_FILE_DIR, migration_time)
 
def _write_to_log(log_file_dir, data):
  target = open(log_file_dir, 'a')
  target.write(str(data))
  target.write('\n')
  target.close()

