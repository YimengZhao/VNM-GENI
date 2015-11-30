import remote_cmd
import time

def _write_to_log(log_file_dir, data):
  if log_file_dir == '':
    return
  target = open(log_file_dir, 'a')
  target.write(str(data))
  target.write('\n')
  target.close()

gw_1 = '128.163.232.71'

for i in range(0, 50):
  start_time = time.time()
  cmd = 'sudo python ssh_cmd.py ' + str(start_time)
  remote_cmd.ssh_run_cmd(gw_1, cmd)
  print("--- %s seconds ---" % (time.time() - start_time))
  _write_to_log('time.log', "%s" % (time.time() - start_time))
