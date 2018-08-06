
import uuid
import time
from datetime import datetime


# Escape codes for generated colored console output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_timestamp():
    """
    Get the current timestamp as a string for creating unique file names
    :return: current timestamp as a string
    """
    d = datetime.now()
    timestamp = str(d).replace(' ', '_').replace(':', '_').replace('-', '_').split('.')[0]
    return timestamp


def print_stdout(stdout):
    """
    Print a stdout stream to console
    :param stdout: The stdout stream
    :return: None
    """
    timeout = 180
    endtime = time.time() + timeout
    while not stdout.channel.eof_received:
        time.sleep(1)

        if time.time() > endtime:
            stdout.channel.close()
            break

    for line in stdout.readlines():
        print(bcolors.OKGREEN + line.rstrip() + bcolors.ENDC)


def print_stderr(stderr):
    """
    Print a stderr stream to console
    :param stderr: The stderr stream
    :return: None
    """
    timeout = 180
    endtime = time.time() + timeout
    while not stderr.channel.eof_received:
        time.sleep(1)

        if time.time() > endtime:
            stderr.channel.close()
            break

    for line in stderr.readlines():
        print(bcolors.WARNING + line.rstrip() + bcolors.ENDC)


def get_n_processors(instance_type):
    """
    Get the number of vCPU's for a given AWS EC2 instance type
    :param instance_type: The type of instance
    :return: The number of vCPU's
    """

    if instance_type in ['t2.nano', 't2.micro', 't2.small']:
        n_processors = 1
    elif instance_type in ['t2.medium', 't2.large']:
        n_processors = 2
    elif instance_type in ['t2.xlarge']:
        n_processors = 4
    elif instance_type in ['t2.2xlarge']:
        n_processors = 8
    else:
        raise Exception('Unrecognized instance type ' + instance_type)

    return n_processors
