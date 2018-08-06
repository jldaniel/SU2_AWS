
import boto3
import os
import time
import shutil

from su2_aws import Node
from su2_aws.util import print_stdout, print_stderr, get_n_processors, get_timestamp


# TODO: Move print statements to a logger

class Cluster(object):
    """
    Represents a cluster of AWS resources
    """

    def __init__(self):
        self.n_nodes = None
        self.ec2_ami = None
        self.instance_type = None

        self.nodes = None
        self.key_file = None
        self.key_name = 'cfdkey'
        self.username = 'ubuntu'
        self.sg_ssh = None
        self.sg_mpi = None
        self.nfs_share_dir = os.path.join('/home', self.username, 'share')
        self.nfs_exports_file = '/etc/exports'
        self.temp_dir = None
        self.results_dir = None
        self.n_retries = 5

        self.ec2 = boto3.client('ec2')

    def generate_key_pair(self, keyname='cluster.pem', location=''):
        """
        Generate a key pair for connecting to the cluster
        :return: None
        """
        self.temp_dir = location
        key_location = os.path.join(location, keyname)
        key_fo = open(key_location, 'w')
        key_pair = self.ec2.create_key_pair(KeyName=self.key_name)
        private_key = str(key_pair['KeyMaterial'])
        key_fo.write(private_key)
        key_fo.close()
        os.chmod(key_location, 0o400)
        self.key_file = key_location
        print('Key file generated ' + key_location)

    def generate_ssh_security_group(self):
        """
        Generate a new security group to open port 22 for connecting to the instances via SSH
        :return: None
        """
        security_group_name = 'cfd-ssh'
        sg_ssh = self.ec2.create_security_group(GroupName=security_group_name,
                                                Description='Security group for SSH to cluster')

        sg_ssh_id = sg_ssh['GroupId']

        self.ec2.authorize_security_group_ingress(
            GroupId=sg_ssh_id,
            CidrIp='0.0.0.0/0',
            IpProtocol='tcp',
            FromPort=22,
            ToPort=22
        )

        self.sg_ssh = self.ec2.describe_security_groups(GroupIds=[sg_ssh_id])['SecurityGroups'][0]
        print('Security group ' + security_group_name + ' generated with ID: ' + sg_ssh_id)

    def generate_mpi_security_group(self):
        """
        Generate a new security group to open ports for inter-instance communication needed for MPI
        :return: None
        """
        print('Creating MPI Security group')
        sg_mpi = self.ec2.create_security_group(
            GroupName='cfd-mpi',
            Description='CFD Cluster MPI Security Group',
        )

        sg_mpi_id = sg_mpi['GroupId']
        sg_ssh_id = self.sg_ssh['GroupId']

        ip_ranges = []
        for n in self.nodes:
            ip_ranges.append({'CidrIp': n.private_ip + '/32'})

        self.ec2.authorize_security_group_ingress(
            GroupId=sg_mpi_id,
            IpPermissions=[{
                'FromPort': 0,
                'ToPort': 65535,
                'IpRanges': ip_ranges,
                'IpProtocol': 'tcp'
            }]
        )

        self.sg_mpi = self.ec2.describe_security_groups(GroupIds=[sg_mpi_id])['SecurityGroups'][0]
        print('Security group cfd-mpi created with ID: ' + sg_mpi_id)

        for n in self.nodes:
            print('Modifying instance ' + n.hostname + ' to include new security group')
            self.ec2.modify_instance_attribute(InstanceId=n.id, Groups=[sg_ssh_id, sg_mpi_id])

    def create_nodes(self, n_nodes, ec2_ami, instance_type):
        """
        Create the nodes
        :param n_nodes: Number of nodes to create
        :param ec2_ami: The EC2 AMI code to use for base instance configuration
        :param instance_type: The type of instance to create, t2.small, t2.medium, etc.
        :return:
        """
        self.n_nodes = n_nodes
        self.ec2_ami = ec2_ami
        self.instance_type = instance_type

        print('Spinning up EC2 Nodes...')
        cluster = self.ec2.run_instances(
            InstanceType=instance_type,
            KeyName=self.key_name,
            MaxCount=n_nodes,
            MinCount=n_nodes,
            SecurityGroupIds=[self.sg_ssh['GroupId']],
            ImageId=ec2_ami
        )

        instance_ids = []
        for idx, instance in enumerate(cluster['Instances']):
            print('Created instance with ID: ' + instance['InstanceId'])
            instance_ids.append(instance['InstanceId'])

        # Wait for the instances to be assigned private IP's
        print('Waiting for nodes to be in a running state')
        waiter = self.ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
        # TODO: See if the sleep is still necessary now that there are multiple attempts to connect
        # Sometimes the nodes still aren't ready to ssh into even though they should be running
        time.sleep(10)

        # Get the cluster networking info
        print('Collecting node info')
        nodes = []
        for idx, instance_id in enumerate(instance_ids):
            response = self.ec2.describe_instances(
                InstanceIds=[instance_id]
            )

            instance = response['Reservations'][0]['Instances'][0]
            private_ip = instance['PrivateIpAddress']
            public_ip = instance['PublicIpAddress']
            hostname = 'cfd' + str(idx)

            node = None
            tries = 0
            while tries < self.n_retries:
                try:
                    node = Node(
                        instance_id,
                        public_ip,
                        private_ip,
                        hostname,
                        self.key_file,
                        self.username)
                    break
                except Exception as ex:
                    tries += 1
                    print('Failed to connect, retrying ' + str(tries) + ' out of ' + str(self.n_retries))
                    time.sleep(3)

            if node is None:
                raise Exception('Failed to connect after ' + str(self.n_retries) + ' attempts')

            nodes.append(node)

        self.nodes = nodes

    def update_packages(self):
        """
        Update apt-get packages on each of the nodes, required to install some of the used packages
        :return: None
        """
        # Update the packages on each of the nodes
        for n in self.nodes:
            print('Updating packages on node: ' + repr(n.id))
            n.ssh.run_remote_command('sudo apt-get update')

    def install_mpi(self):
        """
        Install MPI on all of the nodes
        :return: None
        """
        # Configure networking for MPI
        print('Update /etc/hosts')
        hosts_file_text = '# Cluster Hosts\n'

        for n in self.nodes:
            hosts_file_text += n.private_ip + ' ' + n.hostname + '\n'

        hosts_file = '/etc/hosts'
        for n in self.nodes:
            cmd = 'echo -e ' + '"' + hosts_file_text + '" | sudo tee -a ' + hosts_file
            n.ssh.run_remote_command(cmd)

        # Add the each of the worker nodes to the master nodes known_hosts
        master = self.nodes[0]
        workers = self.nodes[1:]

        # Generate a key-pair on the master node
        print('Generating key-pair for master node')
        master.ssh.run_remote_command('ssh-keygen -t rsa -N "" -f /home/ubuntu/.ssh/id_rsa')
        stdin, stdout, stderr = master.ssh.run_remote_command('cat /home/ubuntu/.ssh/id_rsa.pub')
        master_key_string = stdout.readlines()[0]
        master.ssh.run_remote_command('echo -e "' + master_key_string + '" >> /home/ubuntu/.ssh/authorized_keys')

        # Copy the public key into each of the workers authorized_keys files
        for n in workers:
            n.ssh.run_remote_command('echo -e "' + master_key_string + '" >> /home/ubuntu/.ssh/authorized_keys')

        # Generate a key-pair on each of the workers
        worker_key_strings = []
        for n in workers:
            print('Generating key-pair for worker ' + n.hostname)
            n.ssh.run_remote_command('ssh-keygen -t rsa -N "" -f /home/ubuntu/.ssh/id_rsa')
            stdin, stdout, stderr = n.ssh.run_remote_command('cat /home/ubuntu/.ssh/id_rsa.pub')
            public_key_string = stdout.readlines()[0]
            n.ssh.run_remote_command('echo -e "' + public_key_string + '" >> /home/ubuntu/.ssh/authorized_keys')
            worker_key_strings.append(public_key_string)

        # Add the worker keys to the master node
        for key_string in worker_key_strings:
            master.ssh.run_remote_command('echo -e "' + key_string + '" >> /home/ubuntu/.ssh/authorized_keys')

        # Add they keys to each of the hosts known_hosts file
        print('Adding hosts to known_hosts file')
        hostnames = [n.hostname for n in self.nodes]
        for n in self.nodes:
            for hostname in hostnames:
                n.ssh.run_remote_command('ssh-keyscan ' + hostname + ' >> /home/ubuntu/.ssh/known_hosts')

        # Install MPI on each of the nodes
        for n in self.nodes:
            print('\nInstalling MPI on ' + n.hostname)
            stdin, stdout, stderr = n.ssh.run_remote_command('sudo apt-get -y install mpich')
            print_stdout(stdout)
            print_stderr(stderr)

        # SSH Between the hosts
        for n in workers:
            print('Testing ssh from master to ' + n.hostname)
            master.ssh.run_remote_command('ssh ' + n.hostname)

        for n in workers:
            print('Testing ssh from ' + n.hostname + ' to master')
            n.ssh.run_remote_command('ssh ' + master.hostname)

    def install_nfs(self):
        """
        Install NFS on the master node and then configure the worker nodes to use the shared directory
        :return: None
        """
        master_node = self.nodes[0]
        worker_nodes = self.nodes[1:]

        print('\nInstalling nfs-kernel-service on master node')
        stdin, stdout, stderr = master_node.ssh.run_remote_command('sudo apt-get -y install nfs-kernel-server')
        print_stdout(stdout)
        print_stderr(stderr)

        print('\nCreating share directory ' + self.nfs_share_dir)
        master_node.ssh.mkdir(self.nfs_share_dir, mode=0o775)

        print('\nCreating exports file ' + self.nfs_exports_file)
        cmd = 'echo -e "/home/ubuntu/share *(rw,sync,no_root_squash,no_subtree_check)" | sudo tee -a ' + self.nfs_exports_file
        master_node.ssh.run_remote_command(cmd)

        print('Updating nfs exports')
        master_node.ssh.run_remote_command('sudo exportfs -a')

        for n in worker_nodes:
            print('\nInstalling nfs-common on node ' + n.hostname)
            stdin, stdout, stderr = n.ssh.run_remote_command('sudo apt-get -y install nfs-common')
            print_stdout(stdout)
            print_stderr(stderr)

            print('Creating nfs share directory')
            n.ssh.mkdir(self.nfs_share_dir, mode=0o775)

            # NOTE This assumes that the NFS share dir is in the same location on the master and worker nodes
            # NOTE This assumes that the master node is named cfd0
            print('Mounting the directory to NFS')
            mount_cmd = 'sudo mount -t nfs cfd0:/home/ubuntu/share /home/ubuntu/share'
            n.ssh.run_remote_command(mount_cmd)

    def install_su2(self):
        """
        Configure and install the SU2 software
        :return: None
        """
        master_node = self.nodes[0]

        print('\nInstalling pip')
        pip_cmd = 'sudo apt-get -y install python-pip'
        print(pip_cmd)
        stdin, stdout, stderr = master_node.ssh.run_remote_command(pip_cmd)
        print_stdout(stdout)
        print_stderr(stderr)

        print('\nInstalling python-config')
        pycfg_cmd = 'pip install python-config'
        print(pycfg_cmd)
        stdin, stdout, stderr = master_node.ssh.run_remote_command(pycfg_cmd)
        print_stdout(stdout)
        print_stderr(stderr)

        print('\nRetrieving SU2 source code')
        git_cmd = 'git clone https://github.com/su2code/SU2.git -q'
        print(git_cmd)
        master_node.ssh.run_long_running_command(git_cmd)

        configure_cmd = 'sudo sh /home/ubuntu/SU2/configure --prefix=/home/ubuntu/share/SU2 --enable-mpi ' \
                        '--with-cc=/usr/bin/mpicc --with-cxx=/usr/bin/mpicxx CXXFLAGS="-O3"'

        print('\nConfiguring SU2 for build')
        print(configure_cmd)
        master_node.ssh.run_long_running_command(configure_cmd)

        print('\nBuilding SU2')
        n_processors = get_n_processors(self.instance_type)

        if n_processors == 1:
            build_cmd = 'sudo make'
        else:
            # Build in parallel if additional processors are available for the instance type
            build_cmd = 'sudo make -j ' + str(n_processors)

        print(build_cmd)
        master_node.ssh.run_long_running_command(build_cmd)

        print('\nInstalling SU2')
        install_cmd = 'sudo make install'
        print(install_cmd)
        master_node.ssh.run_long_running_command(install_cmd)

        # Set the environmental variables for the node
        print('Adding SU2 commands to bash profile')
        cmd = 'echo -e "export SU2_RUN="/home/ubuntu/share/SU2/bin"" | sudo tee -a ~/.bashrc'
        print(cmd)
        master_node.ssh.run_remote_command(cmd)

        cmd = 'echo -e "export SU2_HOME="/home/ubuntu/SU2"" | sudo tee -a ~/.bashrc'
        print(cmd)
        master_node.ssh.run_remote_command(cmd)

        cmd = 'echo -e "export PATH=$PATH:$SU2_RUN" | sudo tee -a ~/.bashrc'
        print(cmd)
        master_node.ssh.run_remote_command(cmd)

        cmd = 'echo -e "export PYTHONPATH=$PYTHONPATH:$SU2_RUN" | sudo tee -a ~/.bashrc'
        print(cmd)
        master_node.ssh.run_remote_command(cmd)

    def run_case(self, case_file, mesh_file):
        """
        Run the SU2 CFD case on the cluster and retrieve the results
        :param case_file: The SU2 .cfg file that defines the case to the run
        :param mesh_file: THe .su2 mesh file the defines the computational domain
        :return: None
        """
        print('Preparing to run SU2 case with')
        print('Configuration File: ' + case_file)
        print('Mesh File: ' + mesh_file)

        print('Copying case and mesh file to master node')
        master_node = self.nodes[0]
        path, case_filename = os.path.split(case_file)
        path, mesh_filename = os.path.split(mesh_file)

        master_node.ssh.copy_file_to_remote(case_file, os.path.join(self.nfs_share_dir, case_filename))
        master_node.ssh.copy_file_to_remote(mesh_file, os.path.join(self.nfs_share_dir, mesh_filename))

        print('Executing SU2_CFD run command')
        hosts_list = ','.join([n.hostname for n in self.nodes])

        # Get the number of processors to use
        n_processes = str(int(get_n_processors(self.instance_type)*self.n_nodes))
        su2_run = '/home/ubuntu/share/SU2/bin/SU2_CFD'
        cmd = 'cd ~/share; mpirun -np ' + n_processes + ' --hosts ' + hosts_list + ' ' + su2_run + ' ' + case_filename
        print(cmd)
        master_node.ssh.run_long_running_command(cmd)

        cwd = os.getcwd()
        self.results_dir = os.path.join(cwd, 'results_' + get_timestamp())

        if not os.path.exists(self.results_dir):
            print('Creating results directory ' + self.results_dir)
            os.makedirs(self.results_dir)

        print('Copying results from cluster to local host')
        master_node.ssh.copy_file_to_local(os.path.join(self.nfs_share_dir, case_filename),
                                           os.path.join(self.results_dir, case_filename))

        master_node.ssh.copy_file_to_local(os.path.join(self.nfs_share_dir, mesh_filename),
                                           os.path.join(self.results_dir, mesh_filename))

        master_node.ssh.copy_file_to_local(os.path.join(self.nfs_share_dir, 'forces_breakdown.dat'),
                                           os.path.join(self.results_dir, 'forces_breakdown.dat'))

        master_node.ssh.copy_file_to_local(os.path.join(self.nfs_share_dir, 'restart_flow.dat'),
                                           os.path.join(self.results_dir, 'restart_flow.dat'))

        master_node.ssh.copy_file_to_local(os.path.join(self.nfs_share_dir, 'surface_flow.csv'),
                                           os.path.join(self.results_dir, 'surface_flow.csv'))

        master_node.ssh.copy_file_to_local(os.path.join(self.nfs_share_dir, 'history.dat'),
                                           os.path.join(self.results_dir, 'history.dat'))

        print('\nFinished run')

    def clean_up(self):
        """
        Clean up the artifacts that were created and shut down the cluster
        :return: None
        """
        # Terminate the instances
        print('Terminating instances')
        instance_ids = [n.id for n in self.nodes]

        self.ec2.terminate_instances(InstanceIds=instance_ids)
        waiter = self.ec2.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids)

        # Remove the security groups
        sg_ssh_id = self.sg_ssh['GroupId']
        sg_mpi_id = self.sg_mpi['GroupId']

        print('Removing security group cfd-ssh')
        try:
            self.ec2.delete_security_group(GroupId=sg_ssh_id)
            print('Security Group Deleted')
        except Exception as e:
            print('Error deleting security group cfd-ssh with ID: ' + sg_ssh_id)
            print(e)

        print('Removing security group cfd-mpi')
        try:
            self.ec2.delete_security_group(GroupId=sg_mpi_id)
            print('Security Group Deleted')
        except Exception as e:
            print('Error deleting security group cfd-ssh with ID: ' + sg_mpi_id)
            print(e)

        # Remove the ec2 access key
        self.ec2.delete_key_pair(KeyName=self.key_name)

        # Remove the tmp directory
        shutil.rmtree(self.temp_dir)



