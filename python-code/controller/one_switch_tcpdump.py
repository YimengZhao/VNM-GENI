import remote_cmd
import threading
import os
import re
from os.path import expanduser
import sys


def _get_files(path, prefix):
    files = []
    for i in os.listdir(path):
        if i.startswith(prefix):
            files.append(i)

    return files

def _create_filename(path, prefix):
    files = _get_files(path, prefix)
    print files
    files.sort(key = _alphanum_key)
    filesub = re.split('([0-9]+)',files[-1])
    seq = _tryint(filesub[1])
    seq = seq+1
    file_name = prefix + "_" + str(seq) + '.pcap'
    return file_name
    
def _tryint(s):
    try:
        return int(s)
    except:
        return s

def _alphanum_key(s):
    return [ _tryint(c) for c in re.split('([0-9]+)', s)]
    

def main():
    hosts = ['172.17.5.26', '172.17.1.4', '128.163.232.70']
    #hosts = ['172.17.5.26']
    dump_duration = sys.argv[-1]
    cmd = 'sudo python VNM-dump.py ' + dump_duration
    threads = []
    for h in hosts:
        t = threading.Thread(target=_dump_flow, args=(h,cmd,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    

def _dump_flow(host, cmd):
    remote_cmd.ssh_run_cmd(host, cmd)

main()


