import base64
from binascii import hexlify
import getpass
import os
import select
import socket
import sys
import time
import traceback
from paramiko.py3compat import input

import paramiko
import threading


def ssh_run_cmd_interactive(server, cmd):
    PRIVATEKEY = '/users/yzhao389/.ssh/id_geni_ssh_rsa'
    user = 'yzhao389'
    #server = '128.163.232.84'
    port = 22
    password = 'zym931011'
    #paramiko.util.log_to_file("support_scripts.log")
    trans = paramiko.Transport((server,port))
    rsa_key = paramiko.RSAKey.from_private_key_file(PRIVATEKEY, password)
    trans.connect(username=user, pkey=rsa_key)
    session = trans.open_channel("session")
    session.exec_command(cmd)
    print session.recv_exit_status()
    session.close()
    trans.close()

def ssh_run_cmd(server_IP, cmd):
    ssh = paramiko.SSHClient()
    password = 'zym931011'
    PRIVATEKEY = '/users/yzhao389/.ssh/id_geni_ssh_rsa'
    user = 'yzhao389'
    rsa_key = paramiko.RSAKey.from_private_key_file(PRIVATEKEY, password)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_IP, username=user, password=password, pkey=rsa_key)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)

#ssh_run_cmd('128.163.232.70','sudo at -f interface-down.sh -v now + 1 minute')
#test('172.17.2.11', 'sudo tcpdump -i eth1')
