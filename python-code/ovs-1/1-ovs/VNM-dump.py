import os
import re
import subprocess
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
    if not files:
        file_name = prefix + "0.pcap"
        return file_name

    files.sort(key = _alphanum_key)
    filesub = re.split('_([0-9]+)',files[-1])
    seq = _tryint(filesub[1])
    seq = seq+1
    file_name = prefix + str(seq) + '.pcap'
    return file_name

def _tryint(s):
    try:
        return int(s)
    except:
        return s

def _alphanum_key(s):
    return [ _tryint(c) for c in re.split('_([0-9]+)', s)[1]]


def main():
    prefix1 = 'tcpdump-eth1_'
    prefix2 = 'tcpdump-eth2_'
    base_dir = './ovs1_tcpdump/'
    dump_time = "10s"

    for arg in sys.argv:
        dump_time = arg
        print dump_time

    file_name_1 = _create_filename(base_dir, prefix1)
    file_name_2 = _create_filename(base_dir, prefix2)
    tcpdump_dir1 = base_dir + file_name_1
    tcpdump_dir2 = base_dir + file_name_2
    print tcpdump_dir1
    cmd_1 = "sudo sh tcpdump.sh " + tcpdump_dir1 + " " + tcpdump_dir2 + " " + dump_time 
    print cmd_1
    tcpdump_process = subprocess.Popen(cmd_1, shell=True, stdout=subprocess.PIPE)
    output = tcpdump_process.stdout.readlines()
    print output


main()
