import time
import yaml
import paramiko


def yaml_loader(yaml_path):
    with open(yaml_path) as f:
        yaml_to_dict = yaml.load(f)
    return yaml_to_dict


def log(*args, **kwargs):
    format = '%m/%d %H:%M:%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(format, value)
    with open('log', 'a', encoding='utf-8') as f:
        print(dt, *args, file=f, **kwargs)


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

    def sshJump(self, JumpInfo):
        transport = self.client.get_transport()
        dst_address = (JumpInfo['hostname'], JumpInfo.get('port', 22))
        src_address = transport.getpeername()

        log("Attempting connection to {} via SSH from {}".format(
            dst_address[0], src_address[0]))

        new_channel = transport.open_channel(
            "direct-tcpip", dst_address, src_address)
        new_client = paramiko.SSHClient()
        new_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        new_client.connect(hostname=JumpInfo['hostname'], port=JumpInfo.get(
            'port', 22), username=JumpInfo['username'], password=JumpInfo['password'], sock=new_channel)

        log("Connection to node {} established.".format(JumpInfo['hostname']))
        self.client = new_client

    def execute(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        log(''.join(stdout.readlines()))


def sshNode(node, user, pwd, port=22, client=None):

    if client is not None:
        transport = client.get_transport()
        dst_address = (node, port)
        src_address = transport.getpeername()

        log("Attempting connection to {} via SSH from {}".format(
            node, src_address[0]))

        new_channel = transport.open_channel(
            "direct-tcpip", dst_address, src_address)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=node, username=user,
                       password=pwd, sock=new_channel)

        log("Connection to node {} established.".format(node))

    else:

        log("Attempting connection to {} via SSH".format(node))

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=node, username=user,
                       password=pwd, port=port)

        log("Connection to node {} established.".format(node))

    return client


def execCommand(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    log(''.join(stdout.readlines()))


def transportFile(client, download, upload):

    transport = client.get_transport()
    sftp = paramiko.SFTPClient.from_transport(transport)

    if download:
        sftp.get(download['src'], download['dst'])
        log('Download Complete')
    else:
        pass

    if upload:
        sftp.put(upload['src'], upload['dst'])
        log('Upload Complete')
    else:
        pass


# def getChannel(transport):
#     channel = transport.open_session()
#     # channel.get_pty()
#     # channel.invoke_shell()
#     channel.settimeout(None)
#     channel.set_combine_stderr(True)
#     return channel


# def refreshBuffer(channel, timeout=0.1, bufsize=65535):

#     while not channel.closed:
#         if channel.recv_ready():
#             print(channel.recv(bufsize))
#             break
#         else:
#             time.sleep(timeout)


# def execCommand(transport, cmd):

#     channel = getChannel(transport)
#     channel.exec_command(cmd)
#     refreshBuffer(channel)
#     # while not channel.closed or channel.recv_ready():
#     #     stdout.write(channel.makefile('rb').read(10))
#     channel.close()
