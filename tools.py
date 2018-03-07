import argparse, os, sys, re, datetime, time, subprocess
import pexpect
import yaml
import paramiko
from sys import stdout

def yaml_loader(yaml_path):
    with open(yaml_path) as f:
        yaml_to_dict = yaml.load(f)
    return yaml_to_dict


def auto_command(child, cmd, expect = '#', timeout = 60):

    child.sendline(cmd)
    result = child.expect_exact(expect, timeout = timeout)

    print(child.before)

    return result

def ats_command(child, cmd, timeout = None):

    child.sendline(cmd)
    child.expect_exact('\x1b[31;2m>', timeout = timeout)

    print_log(child.before)

def sshNode(node, user, pwd, transport = None):

    if transport:
        #transport = child.get_transport()
        dst_address = (node, 22)
        src_address = transport.getpeername()

        print_log("Attempting connection to {} via SSH from {}".format(node, src_address[0]))

        new_channel = transport.open_channel("direct-tcpip", dst_address, src_address)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname = node, username = user, password = pwd, sock = new_channel)

        print_log("Connection to node {} established.".format(node))

        transport = client.get_transport()
        channel = getChannel(transport)
        #refreshBuffer(channel)

    else:

        print_log("Attempting connection to {} via SSH".format(node))

        transport = paramiko.Transport((node, 22))
        transport.connect(username = user, password = pwd)
        channel = getChannel(transport)
        #refreshBuffer(channel)

        print_log("Connection to node {} established.".format(node))

    return transport

def getChannel(transport):
    channel = transport.open_session()
    #channel.get_pty()
    #channel.invoke_shell()
    channel.settimeout(None)
    channel.set_combine_stderr(True)
    return channel

def refreshBuffer(channel, timeout = 0.1, bufsize = 65535):

    while not channel.closed:
        if channel.recv_ready():
            print(channel.recv(bufsize))
            break
        else:
            time.sleep(timeout)

def runCommand(transport, cmd):

    channel = getChannel(transport)
    channel.exec_command(cmd)
    while not channel.closed or channel.recv_ready():
        stdout.write(channel.makefile('rb').read(10))
    channel.close()

def transportFile(channel, download, upload):

    transport = channel.get_transport()
    sftp = paramiko.SFTPClient.from_transport(transport)

    if download:
        sftp.get(download['src'], download['dst'])
        print_log('Download Complete')
    else:
        pass

    if upload:
        sftp.put(upload['src'], upload['dst'])
        print_log('Upload Complete')
    else:
        pass

def auto_scp(src, dst, host, user = 'dev', pwd = 'dev', timeout = 60, debug = False):

    child = pexpect.spawn('scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=quiet {0} {1}@{2}:{3}'.format(src, user, host, dst))
    if debug:
        child.logfile = sys.stdout

    try:
        result = child.expect(["#", "password:", pexpect.EOF], timeout = timeout)
    except:
        print_log("Node unreachable!")
        child.close()
        sys.exit(1)

    if result == 1:
        child.sendline(pwd)
        child.expect(["#", pexpect.EOF])
    else:
        print_log("Log in successful without password!")

    child.close()

def print_log(log):

    ctime= datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sys.stdout.write("\n### {0} {1}\n".format(ctime, log))
    sys.stdout.flush()

def login_node(node, user, pwd, timeout = 10, child = None):

    print_log("Start to log in node")

    if child:
        child.sendline("ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ForwardX11=no {0}@{1}".format(user, node))
    else:
        child = pexpect.spawn("ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ForwardX11=no {0}@{1}".format(user, node), timeout = timeout)
        child.logfile = sys.stdout

    try:
        result = child.expect(["#", "assword:", pexpect.EOF], timeout = timeout)
    except:
        print_log("Node unreachable!")
        child.close()
        sys.exit(1)

    if result == 1:
        child.sendline(pwd)
        child.expect(["#", pexpect.EOF])
    else:
        print_log("Log in successful without password!")

    print(child.before)

    return child
