# SU2 AWS

An python package and script for automating an [AWS EC2](https://aws.amazon.com/ec2/) cluster setup, execution of the Standford  [SU2](https://su2code.github.io/) CFD code, retrieval of results and cluster shutdown.

##### Project Goals

The goal of this project is to automate the following steps to allow for parallel execution of SU2 on AWS:
 
1. Generate a key-pair for connecting to the instances
2. Create a security group to open port 22 for SSH
3. Spin up a specified number of AWS EC2 instances
4. Create a security group to allow inter-node communication for MPI
5. Configure password-less SSH between the head node and worker nodes for MPI 
6. Install [MPICH](https://www.mpich.org/) (an implementation of MPI) on the nodes
7. Configure and install [NFS](https://en.wikipedia.org/wiki/Network_File_System) on each of the nodes
8. Install the SU2 software on the head node
9. Copy the SU2 configuration and mesh file to the cluster
10. Execute the CFD case
11. Retrieve the results
12. Shutdown the cluster and cleanup related artifacts

##### Development Process and Decisions

The golden rule of automation is to first be able to go through the process manually. To achieve this standard bash commands and the Amazon [AWS CLI](https://aws.amazon.com/cli/) were used to get an understanding of the API and steps involved. Detailed notes on the manual process is documented in [manual_steps.md](/docs/manual_setup.md).

 For the automated process python was chosen as the weapon of choice for readability of the solution and to utilize [boto3](https://boto3.readthedocs.io/en/latest/) the python AWS SDK. The python package [su2_aws](su2_aws) was created to allow for flexibility in development and testings with a main script and command line interface utilizing the package in the [su2_aws.py](su2_aws.py) file. 
 
 The current implementation has been tested and proven to work using the provided SU2 example configuration and mesh file which is available for convenience in the [example](example) directory. Because this project just serves as an example of how this process could be automated it is _very_ verbose in it's operations and only contains minimal error handling which would be needed for use in a production environment.
 
 ##### Package Architecture
 
 The [su2_aws](su2_aws) package contains three main pieces
 
 1. The [SSHClient](su2_aws/sshclient.py) which wraps the [paramiko](http://www.paramiko.org/) SSH package for connecting to the EC2 instances, executing remote commands, and transfering files.
 2. The [Node](su2_aws/node.py) which represents a single instance in the cluster and contains an [SSHClient](su2_aws/sshclient.py) and instance metadata.
 3. The [Cluster](su2_aws/cluster.py) that interacts with the cluster as a whole and contains the implementation to setup the cluster, run the CFD case, and then cleanup.
   