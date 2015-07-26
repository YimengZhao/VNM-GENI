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

def ssh_run_cmd(server,cmd):
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

#ssh_run_cmd('128.163.232.70','sudo at -f interface-down.sh -v now + 1 minute')
