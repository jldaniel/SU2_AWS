
from su2_aws import SSHClient


class Node(object):
    """
    Represents a resource on the AWS cluster
    """

    def __init__(self, id, public_ip, private_ip, hostname, key_file, username):
        self.id = id
        self.public_ip = public_ip
        self.private_ip = private_ip
        self.hostname = hostname
        self.key_file = key_file
        self.username = username
        # Note: Setting very long timeout due to some of the installs taking along time
        self.ssh = SSHClient(public_ip, username, key_file, port=22, timeout=2400)

    def __repr__(self):
        s = 'NodeID: ' + repr(self.id)
        s += '\nPublic IP: ' + repr(self.public_ip)
        s += '\nPrivate IP: ' + repr(self.private_ip)
        s += '\nHostname: ' + repr(self.hostname)
        s += '\nKey File: ' + repr(self.key_file)
        s += '\nUsername: ' + repr(self.username)
        return s


