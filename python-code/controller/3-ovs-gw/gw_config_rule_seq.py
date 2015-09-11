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
LOG_FILE_DIR = 'vnm_log_1.txt'

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
      print msg

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

class GwRuleStruct():
  def __init__(self, in_port, out_port, drop_port):
    self.in_port = in_port
    self.out_port = out_port
    self.drop_port = drop_port

class VnGwPortStruct():
  def __init__(self, vn1_port_map, vn2_port_map):
    self.port_map = {1:vn1_port_map, 2:vn2_port_map}
  

class ConfigGWRequest ():
  def __init__(self):
    self.gw_record = {g1_dpid:0, g2_dpid:0, g3_dpid:0}
    vn1_port_map  = {g1_dpid: GwRuleStruct(1, 2, 3), g2_dpid: GwRuleStruct(2, 3, 1), g3_dpid: GwRuleStruct(1, 2, 3)}
    vn2_port_map  = {g1_dpid: GwRuleStruct(1, 3, 2), g2_dpid: GwRuleStruct(2, 1, 3), g3_dpid: GwRuleStruct(2, 3, 1)}
    self.port_map = VnGwPortStruct(vn1_port_map, vn2_port_map)
    self.install_first_rule = True

  def _config_gw (self, vn_id):
    self.vn_id = vn_id
    self.start_time = time.time()

    log.info('start configuring gateways in to vn %s', vn_id)

    for connection in core.openflow._connections.values():
      if connection.dpid != g1_dpid and connection.dpid != g2_dpid and connection.dpid != g3_dpid:
        continue
      
      msgs = self._construct_of_msg_1(vn_id, connection)
      self.install_first_rule = True
      gw_request = GWRequest()
      gw_request.bind_to(self._gw_config_finish)
      gw_request._send_msg(connection, msgs)

  def _construct_of_msg_2(self, vn_id, connection):
    msgs = []

    msg1 = of.ofp_flow_mod()
    msg1.match.in_port = self.port_map.port_map[vn_id][connection.dpid].in_port
    action = of.ofp_action_output(port = self.port_map.port_map[vn_id][connection.dpid].out_port)
    msg1.actions.append(action)
    print msg1
    msgs.append(msg1)

    return msgs

  def _construct_of_msg_1(self, vn_id, connection):
    msgs = []

    msg = of.ofp_flow_mod()
    msg.match.in_port = self.port_map.port_map[vn_id][connection.dpid].out_port
    action = of.ofp_action_output(port = self.port_map.port_map[vn_id][connection.dpid].in_port)
    msg.actions.append(action)
    msgs.append(msg)
    return msgs

  def _gw_config_finish(self, sw_dpid):
    self.gw_record[sw_dpid] = 1
    for key, value in self.gw_record.iteritems():
      if value == 0:
        print 'not ready'
        return
    if self.install_first_rule == True:
       for connection in core.openflow._connections.values():
         if connection.dpid != g1_dpid and connection.dpid != g2_dpid and connection.dpid != g3_dpid:
           continue

         msgs = self._construct_of_msg_2(self.vn_id, connection)
         self.install_first_rule = False
         gw_request = GWRequest()
         gw_request.bind_to(self._gw_config_finish)
         gw_request._send_msg(connection, msgs)
       self.gw_record = dict.fromkeys(self.gw_record, 0)
      
    else:
      log.info('migration ends')
      migration_time = time.time() - self.start_time
      log.info('%s seconds', migration_time)
      _write_to_log(LOG_FILE_DIR, migration_time)
 
def _write_to_log(log_file_dir, data):
  target = open(log_file_dir, 'a')
  target.write(str(data))
  target.write('\n')
  target.close()

