
##Setup and Run Instructions


#### Setup Amazon AWS CLI

Create an amazon AWS account at <https://aws.amazon.com/>. If you already have an account this step can be skipped.

Install and configure the AWS CLI according to the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)


#### Download the source code

```
git clone https://github.com/jldaniel/SU2_AWS.git
```

#### Installing the Python Package Requirements

Running the software requires python3, if python3 is not installed it can by obtained from [here](https://www.python.org/download/releases/3.0/) or from one of the python distributions. I personally like [Anaconda](https://www.anaconda.com/download/)

Open a terminal and `cd` into the project directory

```bash
cd SU2_AWS
```

Create a virtual python environment to sandbox the project dependencies

```bash
python3 -m virtualenv venv
```

Activate the virtual environment

```bash
source env/bin/activate
```

Install the project dependencies

```bash
pip install -r requirements.txt
```

#### Running the code

The main program file is [su2_aws.py](su2_aws.py) and has the following command line options

```bash
usage: su2_aws.py [-h] [-n N] [--ec2_ami EC2_AMI] [--instance INSTANCE]
                  case_file mesh_file

Utility for setting up and running SU2 CFD cases on AWS

positional arguments:
  case_file            The SU2 CFD case file
  mesh_file            The SU2 CFD mesh file

optional arguments:
  -h, --help           show this help message and exit
  -n N                 The number of nodes to use for computation
  --ec2_ami EC2_AMI    The EC2 AMI code for compute node configuration
  --instance INSTANCE  The instance type for the ec2 nodes
```

To run the provided example case with a 3 node cluster, the program would be run in the following way

```bash
python su2_aws.py example/inv_NACA0012.cfd example/mesh_NACA0012_inv.su2 -n 3 
```

The program defaults to the US West(N. California) AWS region, if the cluster is going to be operated in a different region then find the correct Ubuntu 16.04 AMI code for the region using the AWS console and supply the code using the `--ec2_ami` option.

The default instance type is `t2.medium`. If a different type of instance is desired, use the `--instance` option.

