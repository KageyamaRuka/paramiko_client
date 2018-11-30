# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
import paramiko
import time
from utils import (
    log,
)


class Client(object):
    def __init__(self, nodeInfo):
        self.hostname = nodeInfo.get('hostname', None)
        self.port = nodeInfo.get('port', 22)
        self.username = nodeInfo.get('username', 'root')
        self.password = nodeInfo.get('password', None)

    def connect(self):
        log("Attempting connection to {} via SSH".format(self.hostname))

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.hostname, port=self.port,
                       username=self.username, password=self.password)

        log("Connection to node {} established.".format(self.hostname))
        self.client = client
        self.transport = self.client.get_transport()

    def sshJump(self, jumpInfo):
        transport = self.client.get_transport()
        dst_address = (jumpInfo['hostname'], jumpInfo.get('port', 22))
        src_address = transport.getpeername()

        log("Attempting connection to {} via SSH from {}".format(
            dst_address[0], src_address[0]))

        new_channel = transport.open_channel(
            "direct-tcpip", dst_address, src_address)
        new_client = paramiko.SSHClient()
        new_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        new_client.connect(hostname=jumpInfo['hostname'], port=jumpInfo.get(
            'port', 22), username=jumpInfo['username'], password=jumpInfo['password'], sock=new_channel)

        log("Connection to node {} established.".format(jumpInfo['hostname']))
        self.client = new_client
        self.transport = self.client.get_transport()

    def execute(self, command, pty=True):
        log("Execute command <{}>".format(command))
        stdin, stdout, stderr = self.client.exec_command(command, get_pty=pty)
        result = stdout.readlines()
        log("Result is\n" + ''.join(result))
        return result

    def executeViaChannel(self, command):
        log("Execute command <{}>".format(command))
        channel = self.getChannel(self.transport)
        channel.send(command)
        self.refreshBuffer(channel)

    @staticmethod
    def getChannel(transport):
        channel = transport.open_session()
        channel.get_pty()
        channel.invoke_shell()
        # channel.settimeout(None)
        channel.set_combine_stderr(True)
        return channel

    @staticmethod
    def refreshBuffer(channel, timeout=0.1, bufsize=65535):
        while not channel.closed:
            if channel.recv_ready():
                log(channel.recv(bufsize))
                break
            else:
                time.sleep(timeout)

    def transportFile(self, download, upload):
        sftp = paramiko.SFTPClient.from_transport(self.transport)

        if download is not None:
            sftp.get(download['src'], download['dst'])
            log('Download Complete')
        else:
            pass

        if upload is not None:
            sftp.put(upload['src'], upload['dst'])
            log('Upload Complete')
        else:
            pass
