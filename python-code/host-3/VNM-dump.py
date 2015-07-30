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
        file_name = prefix + "_" +"0.pcap"
        return file_name

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
    prefix = 'tcpdump'
    base_dir = './host3_tcpdump/'
    dump_time = "10s"

    for arg in sys.argv:
        dump_time = arg
        print dump_time

    file_name = _create_filename(base_dir, prefix)
    tcpdump_dir = base_dir + file_name
    print tcpdump_dir
    cmd_1 = "sudo sh tcpdump.sh " + tcpdump_dir + " " + dump_time 
    print cmd_1
    tcpdump_process = subprocess.Popen(cmd_1, shell=True, stdout=subprocess.PIPE)
    output = tcpdump_process.stdout.readlines()
    print output


main()
