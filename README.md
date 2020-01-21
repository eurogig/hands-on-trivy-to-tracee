# Hands-on Trivy to Tracee
A hands on guided lesson for DevOps Playground walking through how to use the Aqua open source tools Trivy, Kube-hunter and Tracee.

<img src="https://github.com/aquasecurity/trivy/blob/master/imgs/logo.png" height="150" align="left">
<img src="https://github.com/aquasecurity/kube-hunter/blob/master/kube-hunter.png" height="150" align="left">
<img src="https://github.com/eurogig/hands-on-trivy-to-tracee/blob/master/temptraceelogo.png" height="150">


## Part 0
### Prep the environment.

#### Check docker is installed
```
docker -v
```

## Part 1 - Trivy (https://github.com/aquasecurity/trivy)
<img src="https://github.com/aquasecurity/trivy/blob/master/imgs/logo.png" height="150">

### Installing Trivy
```
sudo apt-get -y install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get -y install trivy
```
### NOTE: You might need to run the above twice if one of the apt-get does something unexpected.

### Using Trivy
##### Example.
```
trivy -h
```

#### Note some key paramters are -s to filter on severity and --ignore-unfixed to eliminate reporting any vulnerabilities that do not currently have fixes available

### Let's play with Trivy.   As an experiment let's take the advice of a recent 2019 article about choosing the best base image for a python application.  
https://pythonspeed.com/articles/base-image-python-docker-images/
### It recommends NOT using alpine but instead using ubuntu:18.04 or centos:7.6.1810 or debian:10 but let's try debian:10.2-slim to reduce result.  Which is the most secure?

#### First let's get a summary
```
trivy ubuntu:18.04 | grep Total
```
#### Let's look at the total list now 
```
trivy ubuntu:18.04 
```
#### Now let's try filtering on just CRITICAL vulnerabilities using the -s option total
```
trivy -s CRITICAL --ignore-unfixed ubuntu:18.04
```
### Try these steps quickly again using the centos:7.6.1810 or debian:10.2-slim in place of ubuntu:18.04.  I'll past the commands below to help
```
trivy centos:7.6.1810 | grep Total
```
```
trivy debian:10.2-slim | grep Total
```

### Which base image would you choose at a glance?

### Let's take a quick look at the latest alpine base image to compare
```
trivy alpine:3.11
```
### or perhaps a dedicate python image based on alpine made by João Ferreira Loff (https://github.com/jfloff/alpine-python)

```
trivy jfloff/alpine-python:3.8-slim
```

##### Notes:
Be specific on tags!!!   
Using the latest tag or non-specific tags can mean trivy could produce misleading results based on local caching of the image.


## Part 2 Kube-hunter (remote) (https://github.com/aquasecurity/kube-hunter)

<img src="https://github.com/aquasecurity/kube-hunter/blob/master/kube-hunter.png" height="150">

### Install kube-hunter by cloning the git repo
```
git clone https://github.com/aquasecurity/kube-hunter.git
```

#### We will run kube-hunter within a cluster in two different ways.  Active and Passive.
#### A kubeconfig file has been provided to give access to the cluster.  Let's set that up now.
```
export KUBECONFIG=~/Desktop/hands-on-trivy-to-tracee/DevopsPGkconfig.yaml
cd ./kube-hunter
```

### Install/Download kubectl

```
curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
chmod +x ./kubectl
```

##### CHANGE the job’s metadata: name: from “kube-hunter” to something unique to you “$USER-kube-hunter” to avoid collisions
```
vim job.yaml
```
### Also in the job.yaml we will file make a few changes
```
metadata:
  name: sg-1971-kube-hunter
# ADD a new parameter by CHANGING
        args: ["--pod"]
# to
        args: ["--pod”,”--quick”]
```

### You can do all this quickly via running a short command
```
cat job.yaml | sed 's/\["--pod"\]/\["--pod","--quick"\]/' | sed "s/name: kube-hunter/name: $USER-kubehunter/" > job2.yaml
```

#### NOTE: the --quick argument limits the network interface scanning.   It can turn a 45 min scan into seconds. Better for demos but not for security.
```
./kubectl create -f ./job2.yaml
./kubectl describe job “your-job-name”
./kubectl logs “pod name” > myresultspassive.txt

cat myresultspassive.txt
```

## Part 2b
### First delete the old job
```
./kubectl delete -f ./job2.yaml
```
### In the job.yaml file we will make one more change
```
# ADD a new parameter by CHANGING
        args: ["--pod"]
# to
        args: ["--pod”,”--quick”, “--active”]
```
### You can do all this quickly via running a short command
```
cat job.yaml | sed 's/\["--pod"\]/\["--pod","--quick","--active"\]/' | sed "s/name: kube-hunter/name: $USER-3-kubehunter/" > job3.yaml
```

#### NOTE: the --active argument extends the test to use finding to test for specific exploits. Better for security. Most effective run within the cluster.
### Let's try it again
```
./kubectl create -f ./job3.yaml
./kubectl describe job “your-job-name”
./kubectl logs “pod name” > myresultsactive.txt

cat myresultsactive.txt

diff myresultsactive.txt myresultspassive.txt
```

#### Check the differences between the two results

## Part 3 - Tracee (https://github.com/aquasecurity/tracee)

### Tracee and Intro to eBPF (BPF references http://www.brendangregg.com/ebpf.html)
<img src="https://github.com/eurogig/hands-on-trivy-to-tracee/blob/master/temptraceelogo.png" height="150">

### Install BCC (and BCC for python) 

#### Warning:  Don’t install pip install bcc. Bad.  This project is not our BCC https://pypi.org/project/bcc/
```
sudo apt-get -y install libbcc
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys D4284CDD
echo "deb https://repo.iovisor.org/apt/bionic bionic main" | sudo tee /etc/apt/sources.list.d/iovisor.list
sudo apt-get update
sudo apt-get -y install python-bcc
sudo apt-get -y install python3-bcc
```

#### Create a split terminal or separate terminals for each of the following commands.

### Test our using eBPF
### Test Program:
```python
#!/usr/bin/python
  
from bcc import BPF
from time import sleep

program = """
    int hello(void *ctx) {
        bpf_trace_printk("Hello DevOps Playground\\n");
        return 0;
    }
"""

b=BPF(text=program)
b.attach_kprobe(event="sys_clone",fn_name="hello")
b.trace_print()
```
#### Create a new file called hello-devops.py and copy the contents above into it.

#### Run your program in terminal 1
```
chmod +x ./hello-devops.py
sudo ./hello-devops.py
```
#### It should be stuck waiting for activity

#### Open a second terminal and execute some simple commands in terminal 2 (eg. ls, ps, cd)
#### Then try in terminal 2
```
docker run -it --rm alpine sh
```
#### Run some of the same simple commands (eg ls, ps)

#### Observe the output in terminal 1
### What is the difference?

### If there is time try running your program using strace
### Example
```
sudo strace ./hello-devops.py
```
#### Run some of the same simple commands (eg ls, ps)

## Install Tracee by cloning the git repo

## Tracee (https://github.com/aquasecurity/tracee)
```
git clone https://github.com/aquasecurity/tracee.git
```

### Run in one terminal
```
sudo ./start.py -c
```
### Run in another terminal
```
docker run -it --rm alpine sh
```
### Try running similar commands in the docker shell to what you ran in the linux shell earlier and also experiment with networking commands like ping

### Observe the detailed tracing that appears in the first terminal!  There is a lot of detail.  Imagine what you could do with all that information programmatically to detect malicious behaviour built into containers from 3rd party providers or unvetted registries.  
