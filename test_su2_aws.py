
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
    instance_type = 't2.small'

    cfd0 = Node('i-00f0aeabab3219100', '54.215.250.86', '172.31.13.183', 'cfd0', key_file, username)
    cfd1 = Node('i-028a6fa168ab18033', '13.57.212.70', '172.31.14.36', 'cfd1', key_file, username)
    cfd2 = Node('i-0d9d136336f03c1ce', '13.57.3.239', '172.31.4.187', 'cfd2', key_file, username)
    nodes = [cfd0, cfd1, cfd2]
    n_nodes = 3
    case_filename = 'inv_NACA0012.cfg'

    #cluster = Cluster()
    #cluster.nodes = nodes
    #cluster.n_nodes = 3
    #cluster.instance_type = 't2.small'



    #cfd0.ssh.copy_file_to_remote('example/inv_NACA0012.cfg', '/home/ubuntu/share/inv_NACA0012.cfg')
    #cfd0.ssh.copy_file_to_remote('example/mesh_NACA0012_inv.su2', '/home/ubuntu/share/mesh_NACA0012_inv.su2')

    #cluster.run_case('example/inv_NACA0012.cfg', 'example/mesh_NACA0012_inv.su2')


    print('Executing SU2_CFD run command')
    hosts_list = ','.join([n.hostname for n in nodes])

    # Get the number of processors to use
    n_processes = None
    if instance_type in ['t2.nano', 't2.micro', 't2.small']:
        n_processes = str(int(1 * n_nodes))
    elif instance_type in ['t2.medium', 't2.large']:
        n_processes = str(int(2 * n_nodes))
    elif instance_type in ['t2.xlarge']:
        n_processes = str(int(4 * n_nodes))
    elif instance_type in ['t2.2xlarge']:
        n_processes = str(int(8 * n_nodes))
    else:
        raise Exception('Unrecognized instance type ' + instance_type)

    cmd = 'cd ~/share; mpirun -np ' + n_processes + ' --hosts ' + hosts_list + ' /home/ubuntu/share/SU2/bin/SU2_CFD ' + case_filename
    print(cmd)
    cfd0.ssh.run_long_running_command(cmd)

    #ssh = SSHClient('54.215.250.86', username, key_file)

    #print('Retrieving SU2 source code')
    #ssh.run_long_running_command('git clone https://github.com/su2code/SU2.git')

    #configure_cmd = 'cd ~/SU2; sudo ./configure --prefix=/home/ubuntu/share/SU2 --enable-mpi ' \
    #                '--with-cc=/usr/bin/mpicc --with-cxx=/usr/bin/mpicxx CXXFLAGS="-O3"'

    #print('Configuring SU2 for build')
    #ssh.run_long_running_command(configure_cmd)

    #print('Building SU2')
    #ssh.run_long_running_command('cd ~/SU2; sudo make -j 2')

    #print('Installing SU2')
    #ssh.run_long_running_command('cd ~/SU2; sudo make install')

    #stdout, stdin, stderr = ssh.run_remote_command('sudo apt-get -y install python-pip')
    #print(stdout.readlines())
    #print(stdin.readlines())
    #print(stderr.readlines())

    #stdout, stdin, stderr = ssh.run_remote_command('pip install python-config')
    #print(stdout.readlines())
    #print(stdin.readlines())
    #print(stderr.readlines())

    #stdout, stdin, stderr = ssh.run_remote_command('git clone https://github.com/su2code/SU2.git')
    #print(stdout.readlines())
    #print(stdin.readlines())
    #print(stderr.readlines())

    #configure_cmd = 'cd ~/SU2; sudo ./configure --prefix=/home/ubuntu/share/SU2 --enable-mpi ' \
    #                '--with-cc=/usr/bin/mpicc --with-cxx=/usr/bin/mpicxx CXXFLAGS="-O3"'
    #stdout, stdin, stderr = ssh.run_remote_command(configure_cmd)
    #print(stdout.readlines())
    #print(stdin.readlines())
    #print(stderr.readlines())

    #stdout, stdin, stderr = ssh.run_remote_command('cd ~/SU2; sudo make -j 2')
    #print(stdout.readlines())
    #print(stdin.readlines())
    #print(stderr.readlines())

    #stdout, stdin, stderr = ssh.run_remote_command('cd ~/SU2; sudo make install')
    #print(stdout.readlines())
    #print(stdin.readlines())
    #print(stderr.readlines())


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

