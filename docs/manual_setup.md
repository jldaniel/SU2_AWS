
##### Goals:
  1. Script to spin up n number of AWS instances.
  Install and configure SU2.
  2. Script to run SU2 analysis, and retrieve results.

##### Links Used for Reference
Configuring MPI
<http://mpitutorial.com/tutorials/running-an-mpi-cluster-within-a-lan/>

Example MPI Program
<https://hpcc.usc.edu/support/documentation/examples-of-mpi-programs/>

__connecting to nodes__

```bash
ssh -i ssh-test-key.pem ubuntu@54.193.92.46
```


##### Manual Configuration of 2 Nodes

Spin up 2 AWS linux instances

Using AWS AMI: Ubuntu Server 16.04 LTS (HVM), SSD Volume Type
`ami-4aa04129`

__NOTE__: Make sure that the correct region for the IAM user that is going to be used and is selected in the AWS console (top right) in order to get the correct AMI ID for the instance.

**Setup the environment**

Setup roles on AWS

Create new group called "Rescale" with the Administrator policy.

Create a new user called "rescale-admin" and select "Programmatic access" as the Access type. Attach the user to the Rescale group

**Region Info**
```
Region Name: US West(N. California)
Region: us-west-1
Endpoint: rds.us-west-1.amazonaws.com
Protocol: HTTPS
```

Region Reference: <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html>



**Install AWS CLI**

Installing the AWS Command Line Interface on Mac
OS X

Update pip

```bash
pip install --upgrade pip
```

Install the AWS CLI

```bash
pip install awscli --upgrade --user
```

 Using the AWS CLI

 ```bash
aws [options] <command> <subcommand> [parameters]
 ```

Checking the AWS CLI version

```bash
aws --version
```

**Configure the AWS CLI**

Run
```bash
aws configure
```
and enter the requested information

```bash
AWS Access Key ID [None]: <key>
AWS Secret Access Key [None]: <key>
Default region name [None]: us-west-1
Default output format [None]: json
```

Note that aws configuration and credentials can be supplied via files
or environmental variables.

<https://docs.aws.amazon.com/cli/latest/userguide/cli-environment.html>

**Create a security group and key pair for connecting**

_TODO_: See if the same security group can be used for both rules

Create a security group

```bash
aws ec2 create-security-group --group-name rescale-dev --description "security group for rescale dev"
```

Authorize the security group

```bash
aws ec2 authorize-security-group-ingress --group-name rescale-dev --protocol tcp --port 22 --cidr 0.0.0.0/0
```

_NOTE:_
``"GroupId": "sg-7fd28207"``


Create a key pair to connect

```bash
aws ec2 create-key-pair --key-name rescale-key --query 'KeyMaterial' --output text > rescale-key.pem
```

Set the permissions on the key file

```bash
chmod 400 rescale-key.pem
```

**Run the instance**

```bash
aws ec2 run-instances --image-id ami-4aa04129 --security-group-ids sg-7fd28207 --count 1 --instance-type t2.medium --key-name rescale-key --query 'Instances[0].InstanceId'
```

The instance will spin up and return the ID from the query

`"i-055f86cc94128b4fd"`

Use the ID to obtain the public IP address for the instance

```bash
aws ec2 describe-instances --instance-ids i-055f86cc94128b4fd --query 'Reservations[0].Instances[0].PublicIpAddress'
```

The command will return with the instance public IP
`"54.183.139.116"`

To connect to the instance, use the public IP address and the private key

```bash
ssh -i rescale-key.pem ubuntu@54.183.139.116
```

To start the instance, use the `start-instances` command

```bash
aws ec2 start-instances --instance-ids i-055f86cc94128b4fd
```

and to stop it, use the `stop-instances` command

```bash
aws ec2 stop-instances --instance-ids i-055f86cc94128b4fd
```

**Spinning up multiple instances**

```bash
aws ec2 run-instances --image-id ami-4aa04129 --security-group-ids sg-7fd28207 --count 2 --instance-type t2.medium --key-name rescale-key --query 'Instances[*].InstanceId'
```

Get all of the instance ID's

```bash
aws ec2 describe-instances --query 'Reservations[*].Instances[*].InstanceId'
```

_response_

```
[
    "i-04c22667452d4c96d",
    "i-0f60ff51d36a4c199"
]
```

Get the IP addresses for the instances

```bash
aws ec2 describe-instances --instance-ids i-04c22667452d4c96d i-0f60ff51d36a4c199 --query 'Reservations[*].Instances[*].PublicIpAddress'
```

_response_

```
[
    [
        "13.56.12.225",
        "13.56.11.155"
    ]
]
```

ssh into the instances

Dedicating `13.56.12.225` as the head node and `13.56.11.155` as the slave

##### Setting up ssh keys

**Head to Slave**

On the head node run

```bash
ssh-keygen
```

press enter through the prompts, then view the key

```bash
cat ~/.ssh./id_rsa.pub
```

copy the contents to the clipboard

On the node copy the public key into the `authorized_keys` file and then on slave node node as well.

```bash
cat >> ~/.ssh/authorized_keys
```

Paste in the contents then press `Ctrl-d` to exit.

Follow the same process from the slave node.

#### Install and configure MPI

```bash
sudo apt-get update
sudo apt-get install mpich
```

Create and set a new security group to open ports for MPI

```bash
aws ec2 create-security-group --group-name mpi-sg --description "Security group to open ports for MPI"
```

_response_

```
{
    "GroupId": "sg-d77a29af"
}
```

Update the security group to open ports for each machine

```bash
aws ec2 authorize-security-group-ingress --group-id sg-d77a29af --protocol tcp --port 0-65535 --cidr 172.31.28.11/32

aws ec2 authorize-security-group-ingress --group-id sg-d77a29af --protocol tcp --port 0-65535 --cidr 172.31.28.198/32
```

Modify the instances to add the new security group

```bash
aws ec2 modify-instance-attribute --instance-id i-04c22667452d4c96d --groups sg-7fd28207 sg-d77a29af

aws ec2 modify-instance-attribute --instance-id i-0f60ff51d36a4c199 --groups sg-7fd28207 sg-d77a29af

```

_TODO_: For script check if security group already exists or use a GUID to make it unique each time the cluster is spun up and remove the group afterwords.

Test that MPICH install

```bash
mpirun
```

Set up the hosts file

On each machine add the other hosts and name them, starting with the master node

```bash
sudo vim /etc/hosts
```

And add in the lines

```
127.0.0.1 localhost

# Cluster Hosts
172.31.28.198 master
172.31.28.11 cfd1

```

then on the slave node

```
127.0.0.1 localhost

# Cluster Hosts
172.31.28.198 master
172.31.28.11 cfd1
```

_NOTE_: For the master file add all of the slave nodes, for each of the slave nodes just add the master and itself

**Setup NSF**

Because we are on AWS, a separate EFS instance will need to be created to host the NSF filesystem.

Install NSF on the master node

```bash
sudo apt-get install nfs-kernel-serverssh
```

Make a directory that will be used by NFS

```bash
mkdir share
```

Export the directory to be used by NSF

```bash
sudo vim /etc/exports
```

and add the line

```bash
/home/ubuntu/share *(rw,sync,no_root_squash,no_subtree_check)
```

after adding the entry

```bash
sudo exportfs -a
```

Restart the NFS server for the changes to take effect

```bash
sudo service nfs-kernel-server restart
```

Setup NFS on the client machine

```bash
sudo apt-get install nfs-common
```

Create a directory on the client machine with the same name

```bash
mkdir share
```

Mount the shared directory

```bash
sudo mount -t nfs master:/home/ubuntu/share ~/share
```

**Testing MPI**

Simple MPI Hello World Test Program

`mpitest.c`

```cpp
/* program hello */
/* Adapted from mpihello.f by drs */

#include <mpi.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv)
{
  int rank;
  char hostname[256];

  MPI_Init(&argc,&argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  gethostname(hostname,255);

  printf("Hello world!  I am process number: %d on host %s\n", rank, hostname);

  MPI_Finalize();

  return 0;
}
```

Compile the program using

```bash
mpicc -o mpitest mpitest.c
```

Create a hosts file for MPI

```bash
touch mpi_hosts
```

Then add the following lines to the hosts file

```
master:2
cfd1:2
```

Run the program with

```bash
mpirun -np 4 --hosts master,cfd1 ./mpitest
```

_output_

```
Hello world!  I am process number: 1 on host ip-172-31-28-11
Hello world!  I am process number: 3 on host ip-172-31-28-11
Hello world!  I am process number: 2 on host ip-172-31-28-198
Hello world!  I am process number: 0 on host ip-172-31-28-198
```

##### Install SU2

Make sure that git is installed

```bash
git --version
```

if not install git

```
sudo apt-get install git
```

Make sure that make is install

```
make -v
```

if not install make

```bash
sudo apt-get install make
```

Install `pip` and the `python-config` package

```bash
sudo apt-get install pip
pip install python-config
```

Get the SU2 source code on the master node

```bash
git clone https://github.com/su2code/SU2.git
```

This will create the directory `SU2` where the command was run

`cd` into the `SU2` directory.

Run the configuration for make

_note_: SU2 needs to be installed on the NFS share in order to work with MPI on multiple clients

```bash
sudo ./configure --prefix=/home/ubuntu/share/SU2 --enable-mpi --with-cc=/usr/bin/mpicc --with-cxx=/usr/bin/mpicxx CXXFLAGS="-O3"
```

_NOTE_: For automation can use the `-q` option to suppress output

After the configuration is complete, compile the code

```bash
sudo make -j 2
```

After compiling, install SU2

```bash
sudo make install
```

Clean up the intermediary files from the install

```bash
make clean
```

Create environmental variables for SU2

```bash
export SU2_RUN="/home/ubuntu/share/SU2/bin"
export SU2_HOME="/home/ubuntu/SU2"
export PATH=$PATH:$SU2_RUN
export PYTHONPATH=$PYTHONPATH:$SU2_RUN
```

Test that the solver runs in serial


```bash
cd ~/SU2/Quickstart
SU2_CFD inv_NACA0012.cfg
```

Test that the solver runs in parallel on a single node

```bash
mpirun -n 2 SU2_CFD inv_NACA0012.cfg
```

Test that the solver runs in parallel on multiple clients

```bash
mpirun -n 4 --hosts master,cfd1 SU2_CFD inv_NACA0012.cfg
```
