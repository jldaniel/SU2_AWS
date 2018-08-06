
### Manual Setup Steps

**Setup the environment**

Setup roles on AWS

Create new group called "Test_Group" with the Administrator policy.

Create a new user called "tester" and select "Programmatic access" as the Access type. Attach the user to the Test_Group group.


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

Create a security group

```bash
aws ec2 create-security-group --group-name rescale-dev --description "security group for rescale dev"
```

Authorize the security group

```bash
aws ec2 authorize-security-group-ingress --group-name rescale-dev --protocol tcp --port 22 --cidr 0.0.0.0/0
```

_response:_
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

First select the AMI code that will be used to configure the instance. For this process Ubuntu 16.04 instances were used. Make sure the correct region is selected in order to obtain the correct AMI code for the instances.

[Region Reference](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html)

In this example the US West(N. California) region and AMI were used

**Region Info**
```
Region Name: US West(N. California)
Region: us-west-1
Endpoint: rds.us-west-1.amazonaws.com
Protocol: HTTPS
```

AWS AMI: Ubuntu Server 16.04 LTS (HVM), SSD Volume Type
`ami-4aa04129`

With the region and AMI selected, the instances are created using the `run-instances` API command

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

```bash
ssh -i ssh-test-key.pem ubuntu@54.193.92.46
```

Select one of the instances to act as the _head_ or _master_ node while the other instances will be the _workers_.

##### Setting up passwordless SSH between instances

**Head to Worker**

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

Follow the same process from each of the worker nodes to the head node.

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

Note that the `--cidr` option values are set to the private IP address of each of the nodes and need to include the `/32` at the end for proper functionality.

Modify the instances to add the new security group

```bash
aws ec2 modify-instance-attribute --instance-id i-04c22667452d4c96d --groups sg-7fd28207 sg-d77a29af

aws ec2 modify-instance-attribute --instance-id i-0f60ff51d36a4c199 --groups sg-7fd28207 sg-d77a29af

```

Test that MPICH install

```bash
mpirun
```

Set up the hosts file

On each machine add the other hosts and name them, starting with the master node starting with `cfd0` as the hostname for the master node.

```bash
sudo vim /etc/hosts
```

And add in the lines

```
127.0.0.1 localhost

# Cluster Hosts
172.31.28.198 cfd0
172.31.28.11 cfd1

```

then on the worker node

```
127.0.0.1 localhost

# Cluster Hosts
172.31.28.198 cfd0
172.31.28.11 cfd1
```

SSH from the master node to the worker nodes and visa-versa to add them to each nodes `known_hosts` file.


**Setup NSF**


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

Install NFS on each worker node

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

To test that NFS is working, a file can be created in the NFS `share` directory e.g.

```bash
touch ~/share/test.txt
```

that file should then be available in the mounted NFS share directory on each of the worker nodes

**Testing MPI**

Simple MPI Hello World Test Program from <https://hpcc.usc.edu/support/documentation/examples-of-mpi-programs/>

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

Create a new file in the NFS share directory called `mpitest.c`

```bash
touch ~/share/mpitest.c
```

and copy the test program into the file and save it.

Compile the program using

```bash
mpicc -o mpitest mpitest.c
```

Run the program with

```bash
mpirun -np 4 --hosts cfd0,cfd1 ./mpitest
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

_note_: SU2 needs to be installed on the NFS share in order to work with MPI on multiple clients as indicated by the `--prefix` option

```bash
sudo ./configure --prefix=/home/ubuntu/share/SU2 --enable-mpi --with-cc=/usr/bin/mpicc --with-cxx=/usr/bin/mpicxx CXXFLAGS="-O3"
```


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

Test that the solver runs in parallel on multiple clients

```bash
mpirun -n 4 --hosts master,cfd1 SU2_CFD inv_NACA0012.cfg
```


