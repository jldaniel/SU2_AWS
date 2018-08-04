
import uuid
import time


def get_unique_name(prefix=None, postfix=None):
    unique = str(uuid.uuid4())
    return prefix + unique + postfix


def print_stdout(stdout):
    timeout = 180
    endtime = time.time() + timeout
    while not stdout.channel.eof_received:
        time.sleep(1)

        if time.time() > endtime:
            stdout.channel.close()
            break

    for line in stdout.readlines():
        print(line)


def get_n_processors(instance_type):

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

if __name__ == '__main__':
    file = get_unique_name(prefix='cfd_', postfix='.pem')
    print(file)
