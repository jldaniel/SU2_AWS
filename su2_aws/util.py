
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



if __name__ == '__main__':
    file = get_unique_name(prefix='cfd_', postfix='.pem')
    print(file)
