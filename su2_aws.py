
import argparse
import os

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

# Configure the CLI options parser
parser = argparse.ArgumentParser(description='Utility for setting up and running SU2 CFD cases on AWS')
parser.add_argument('-n', type=int, default=3, help='The number of nodes to use for computation')
parser.add_argument('case_file', type=argparse.FileType('r'), help='The SU2 CFD case file')
parser.add_argument('mesh_file', type=argparse.FileType('r'), help='The SU2 CFD mesh file')
parser.add_argument('--ec2_ami',  type=str, default='ami-4aa04129', help='The EC2 AMI code for compute node configuration')
parser.add_argument('--instance', type=str, default='t2.medium', help='The instance type for the ec2 nodes')


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

    print('\nCleaning Up')
    cluster.clean_up()

    print('Results saved to ' + cluster.results_dir)
    print('Finished')

