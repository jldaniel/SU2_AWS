import paramiko
import os
import socket
import scp
import select

from .util import bcolors

class SSHClient(object):
    """
    Client for interacting with remote systems.
    """
    def __init__(self, host, user, key_file, port=22, timeout=30):
        self._host = host
        self._user = user
        self._key_file = key_file
        self._key = None
        self._port = port
        self._timeout = timeout
        self._transport = None
        self._sftp = None
        self._scp = None
        self._client = paramiko.SSHClient()
        self._client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self._key = paramiko.RSAKey.from_private_key_file(key_file)
        except Exception as ex:
            print('Error loading private key ' + str(key_file))
            raise ex

        # Test the SSH connection and update known hosts
        try:
            self._client.connect(hostname=self._host, username=self._user, pkey=self._key)

        except Exception as ex:
            print('Error connecting to host ' + str(self._host) + ' as user ' +
                  str(self._user) + ' with key ' + str(self._key_file))
            raise ex

        # TODO Update known hosts

        self._client.close()

    def connect(self):
        # Find the correct address family to use for the transport
        address_info = socket.getaddrinfo(self._host, self._port)
        address_family = None
        for (fam, stype, proto, canon, saddr) in address_info:
            if stype == socket.SOCK_STREAM:
                address_family = fam
                break

        if not address_family:
            raise Exception('Invalid address family for host ' + self._host)

        # Create the transport
        try:
            s = socket.socket(address_family, socket.SOCK_STREAM)
            s.settimeout(self._timeout)
            s.connect((self._host, self._port))
            transport = paramiko.Transport(s)
            transport.banner_timeout = self._timeout
        except Exception as ex:
            print('Unable to create transport')
            raise ex

        try:
            transport.connect(username=self._user, pkey=self._key)
        except Exception as ex:
            print('Unable to connect to transport')
            raise ex

        self.close()
        self._transport = transport

        print('Successfully created connection to ' + str(self._host))

    @property
    def sftp(self):
        if not self._sftp or self._sftp.sock.closed:
            print('connecting to sftp')
            self._sftp = paramiko.SFTPClient.from_transport(self.transport)

        return self._sftp

    @property
    def transport(self):
        if not self._transport or not self._transport.is_active():
            self.connect()

        return self._transport

    @property
    def scp(self):
        if not self._scp or not self._scp.transport.is_active():
            self._scp = scp.SCPClient(self.transport, socket_timeout=self._timeout)

        return self._scp

    def close(self):
        if self._sftp:
            self._sftp.close()

        if self._transport:
            self._transport.close()

        print('SSH client to ' + str(self._host) + ' closed.')

    def access_remote_file(self, file, mode='w'):
        """
        Interact with a remote file using SFTP
        :param file: The location of the file to interact with
        :param mode: The mode to use for accessing the file
        :return: A handle to the remote file
        """
        remote_file = self.sftp.open(file, mode)
        remote_file.name = file
        return remote_file

    # TODO: Should this method actually return something?
    def get_file(self, target_path, local_path):
        """
        Retrieve a file from the remote machine
        :param target_path: The target file on the remote machine
        :param local_path: The local path to place the file
        :return: None
        """
        try:
            self.scp.get(target_path, local_path=local_path)
        except Exception as ex:
            print('Error retrieving file ' + target_path + ' from ' + self._host + ':' + local_path)
            raise ex

    def run_remote_command(self, command):
        self._client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        try:
            self._client.connect(hostname=self._host,username=self._user,pkey=self._key)
        except Exception as ex:
            print('Error connecting to host ' + str(self._host) + ' as user '
                  + str(self._user) + ' with key ' + str(self._key_file))
            raise ex

        (stdin, stdout, stderr) = self._client.exec_command(command)

        return stdin, stdout, stderr

    def run_long_running_command(self, command):
        # Send the command (non-blocking)
        self._client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        try:
            self._client.connect(hostname=self._host, username=self._user, pkey=self._key)
        except Exception as ex:
            print('Error connecting to host ' + str(self._host) + ' as user '
                  + str(self._user) + ' with key ' + str(self._key_file))
            raise ex

        stdin, stdout, stderr = self._client.exec_command(command)

        # Wait for the command to terminate
        while not stdout.channel.exit_status_ready():
            # Only print data if there is data to read in the channel
            if stdout.channel.recv_ready():
                rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
                if len(rl) > 0:
                    # Print data from stdout
                    print(bcolors.OKGREEN + stdout.channel.recv(1024).decode("utf-8") + bcolors.ENDC)

        for line in stderr:
            print(line.rstrip())

    def mkdir(self, path, mode=0o755):
        try:
            return self.sftp.mkdir(path, mode)
        except Exception as ex:
            print('Error creating directory ' + path + ' on ' + self._host)
            raise ex

    def copy_file_to_local(self, remote_file, local_file):
        self.sftp.get(remote_file, local_file)

    def copy_file_to_remote(self, local_file, remote_file):
        self.sftp.put(local_file, remote_file)


