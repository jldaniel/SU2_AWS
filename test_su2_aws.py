
from su2_aws import Cluster, Node, SSHClient
import os
import boto3


N_NODES = 2
CASE_FILE = '/example/naca0012.cas'
MESH_FILE = '/example/naca0012.msh'
EC2_AMI = 'ami-4aa04129'
INSTANCE = 't2.small'

if __name__ == '__main__':

    key_file = '/Users/jdaniel/Desktop/SU2_AWS/tmp/cluster.pem'
    username = 'ubuntu'

    ssh = SSHClient('54.67.82.193', username, key_file)

    stdout, stdin, stderr = ssh.run_remote_command('sudo apt-get -y install python-pip')
    print(stdout.readlines())
    print(stdin.readlines())
    print(stderr.readlines())

    stdout, stdin, stderr = ssh.run_remote_command('pip install python-config')
    print(stdout.readlines())
    print(stdin.readlines())
    print(stderr.readlines())

    stdout, stdin, stderr = ssh.run_remote_command('git clone https://github.com/su2code/SU2.git')
    print(stdout.readlines())
    print(stdin.readlines())
    print(stderr.readlines())

    configure_cmd = 'cd ~/SU2; sudo ./configure --prefix=/home/ubuntu/share/SU2 --enable-mpi ' \
                    '--with-cc=/usr/bin/mpicc --with-cxx=/usr/bin/mpicxx CXXFLAGS="-O3"'
    stdout, stdin, stderr = ssh.run_remote_command(configure_cmd)
    print(stdout.readlines())
    print(stdin.readlines())
    print(stderr.readlines())

    stdout, stdin, stderr = ssh.run_remote_command('cd ~/SU2; sudo make -j 2')
    print(stdout.readlines())
    print(stdin.readlines())
    print(stderr.readlines())

    stdout, stdin, stderr = ssh.run_remote_command('cd ~/SU2; sudo make install')
    print(stdout.readlines())
    print(stdin.readlines())
    print(stderr.readlines())


    # Test Copy keys
    #master_ip = '13.57.222.239'
    #worker_ip = '13.57.32.148'

    # Handle the key from master to workers
    #print('Generating key on master')
    #local_public_key_location = os.path.join(temp_dir, 'id_rsa.pub')
    #ssh = SSHClient(master_ip, 'ubuntu', 'tmp/cluster.pem')
    #ssh.run_remote_command('ssh-keygen -t rsa -N "" -f /home/ubuntu/.ssh/id_rsa')
    #stdin, stdout, stderr = ssh.run_remote_command('cat /home/ubuntu/.ssh/id_rsa.pub')
    #public_key_string = stdout.readlines()[0]

    #print('Copying key to worker')
    #ssh = SSHClient(worker_ip, 'ubuntu', 'tmp/cluster.pem')
    #ssh.run_remote_command('echo -e "' + public_key_string + '" >> /home/ubuntu/.ssh/authorized_keys')


    #ssh.copy_file_to_local('/home/ubuntu/.ssh/id_rsa.pub', local_public_key_location)
    #ssh.run_remote_command('ssh-keyscan -H cfd1 >> /home/ubuntu/.ssh/known_hosts')
    #ssh.copy_file_to_remote(local_public_key_location, '/home/ubuntu/.ssh/cfd0.pub')
    #ssh.run_remote_command('cat /home/ubuntu/.ssh/cfd0.pub >> /home/ubuntu/.ssh/authorized_keys')



    # Handle the key from worker to master
    #print('Generating key on worker')
    #local_public_key_location = os.path.join(temp_dir, 'id_rsa.pub')
    #ssh = SSHClient(worker_ip, 'ubuntu', 'tmp/cluster.pem')
    #ssh.run_remote_command('ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa')

    #ssh.copy_file_to_local('/home/ubuntu/.ssh/id_rsa.pub', local_public_key_location)
    #ssh.run_remote_command('ssh-keyscan -H cfd0 >> /home/ubuntu/.ssh/known_hosts')

    #print('Copying key to master')
    #ssh = SSHClient(master_ip, 'ubuntu', 'tmp/cluster.pem')
    #ssh.copy_file_to_remote(local_public_key_location, '/home/ubuntu/.ssh/id_rsa.pub')
    #ssh.run_remote_command('cat /home/ubuntu/.ssh/cfd1.pub >> /home/ubuntu/.ssh/authorized_keys')
    #ssh.run_remote_command('ssh-keyscan -H ' + worker_ip + ' >> ~/.ssh/authorized_keys')


    #local_public_key_location = os.path.join(temp_dir, 'id_rsa.pub')
    #print(local_public_key_location)
    #ssh = SSHClient(master_ip, 'ubuntu', 'tmp/cluster.pem')
    #ssh.copy_file_to_local('/home/ubuntu/.ssh/id_rsa.pub', local_public_key_location)





    print('Finished')
