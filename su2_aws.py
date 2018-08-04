
import argparse
import os
import boto3


from su2_aws import Cluster


def get_header():
    header = "\n" \
        " $$$$$$\\  $$\\   $$\\  $$$$$$\\         $$$$$$\\  $$\\      $$\\  $$$$$$\\  \n" \
        "$$  __$$\\ $$ |  $$ |$$  __$$\\       $$  __$$\\ $$ | $\\  $$ |$$  __$$\\ \n" \
        "$$ /  \\__|$$ |  $$ |\\__/  $$ |      $$ /  $$ |$$ |$$$\\ $$ |$$ /  \\__|\n" \
        "\\$$$$$$\\  $$ |  $$ | $$$$$$  |      $$$$$$$$ |$$ $$ $$\\$$ |\\$$$$$$\\  \n" \
        " \\____$$\\ $$ |  $$ |$$  ____/       $$  __$$ |$$$$  _$$$$ | \\____$$\\ \n" \
        "$$\\   $$ |$$ |  $$ |$$ |            $$ |  $$ |$$$  / \\$$$ |$$\\   $$ |\n" \
        "\\$$$$$$  |\\$$$$$$  |$$$$$$$$\\       $$ |  $$ |$$  /   \\$$ |\\$$$$$$  |\n" \
        " \\______/  \\______/ \\________|      \\__|  \\__|\\__/     \\__| \\______/ \n" \
        "                                                                     \n" \
        "                                                                     \n" \
        "                                                                     \n"

    return header







# Parse the command line options
# Options
# -n number of nodes, default 3
# -ami amazon ami code, default 'ami-4aa04129' us-west

parser = argparse.ArgumentParser(description='Utility for setting up and running SU2 CFD cases on AWS')
parser.add_argument('-n', type=int, default=3, help='The number of nodes to use for computation')
parser.add_argument('case_file', type=argparse.FileType('r'), help='The SU2 CFD case file')
parser.add_argument('mesh_file', type=argparse.FileType('r'), help='The SU2 CFD mesh file')
parser.add_argument('--ec2_ami',  type=str, default='ami-4aa04129', help='The EC2 AMI code for compute node configuration')
parser.add_argument('--instance', type=str, default='t2.small', help='The instance type for the ec2 nodes')


# TODO Create an AWS CLI profile to use for this case





# MAIN

# Create an ec2 client

# Generate a security group to open port 22 for ssh

# TODO Test if we can update the secuirty group for internal MPI communication instead of creating a new one


# Generate a key pair for connecting to the EC2 cluster


# Spin up the EC2 instances

# Obtain the public and private IP addresses of the instances


# Setup MPI


# Setup NFS


# Setup SU2

# Copy the case and mesh file

# Run the SU2 case


# Retrieve the solution files


# Shutdown the cluster

# Remove generated artifacts


if __name__ == '__main__':
    # Parse command line args and display header
    args = parser.parse_args()
    n_nodes = vars(args)['n']
    case_file = vars(args)['case_file']
    mesh_file = vars(args)['mesh_file']
    ec2_ami = vars(args)['ec2_ami']
    instance_type = vars(args)['instance']

    print(get_header())

    print('Preparing to configure cluster with ' + str(n_nodes) + ' nodes')
    print('to run SU2 with case file ' + case_file.name)
    print('and mesh file ' + mesh_file.name)

    # Create a temp directory for storing intermediary artifacts
    cwd = os.getcwd()
    temp_dir = os.path.join(cwd, 'tmp')

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    cluster = Cluster()

    print('\nGenerating EC2 Key Pair')
    cluster.generate_key_pair(location=temp_dir)

    print('\nSetting up security group for SSH to the cluster')
    cluster.generate_ssh_security_group()

    print('\nCreating cluster nodes on EC2')
    cluster.create_nodes(n_nodes, ec2_ami, instance_type)

    print('\nUpdating security policy for MPI')
    cluster.generate_mpi_security_group()

    print('\nUpdating packages on nodes')
    cluster.update_packages()

    print('\nInstalling MPI on each of the nodes')
    cluster.install_mpi()

    print('\nConfiguring NFS')
    cluster.install_nfs()

    print('\nInstalling SU2')
    cluster.install_su2()

    print('\nRunning SU2 Case')
    cluster.run_case(case_file.name, mesh_file.name)

    # TODO Shutdown and cleanup cluster
    # Terminate the instances
    # Wait for instances to be terminated
    # Remove the security groups
    # Remove the key-pair
    # Remove the tmp dir

    # Print where the results are
    print('Finished')




    # Clean Up
