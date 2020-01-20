# Hands-on Trivy to Tracee
A hands on guided lesson for DevOps Playground walking through how to use the Aqua open source tools Trivy, Kube-hunter and Tracee.

<img src="https://github.com/aquasecurity/trivy/blob/master/imgs/logo.png" height="150" align="left">
<img src="https://github.com/aquasecurity/kube-hunter/blob/master/kube-hunter.png" height="150" align="left">
<img src="https://github.com/eurogig/hands-on-trivy-to-tracee/blob/master/temptraceelogo.png" height="150">


## Part 0
### Prep the environment.

#### Install docker
```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
apt-cache policy docker-ce
sudo apt-get -y install -y docker-ce
sudo usermod -aG docker ${USER}
```
#### Test it
#### First log out and then log back into your terminal to enable your user account to user the docker group.
#### Now try...
```
docker run -it --rm alpine sh
```

## NOTE: To use sudo you'll need your account password assigned by DevOps Playground

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

### Using Trivy
##### Example.
```
trivy -h
```

#### Note some key paramters are -s to filter on severity and --ignore-unfixed to eliminate reporting any vulnerabilities that do not currently have fixes available
```
trivy postgres:9.5.20
trivy -s CRITICAL postgres:9.5.20
trivy -s CRITICAL --ignore-unfixed postgres:9.5.20
```

##### Notes:
Be specific on tags!!!   
Using the tag 9.5 can mean trivy -s CRITICAL postgres:9.5.20 or 21 or 10 or...
Ambiguous tags (latest being the worst) means you can get misleading results based on local caching of the image.


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

##### CHANGE the job’s metadata: name: from “kube-hunter” to something unique to you “initials-birthyear-kube-hunter” to avoid collisions
```
vim job.yaml
```
### In the job.yaml file make a few changes
```
metadata:
  name: sg-1971-kube-hunter
# ADD a new parameter by CHANGING
        args: ["--pod"]
# to
        args: ["--pod”,”--quick”]
```
#### NOTE: the --quick argument limits the network interface scanning.   It can turn a 45 min scan into seconds. Better for demos but not for security.
```./kubectl create -f ./job.yaml
./kubectl describe job “your-job-name”
./kubectl logs “pod name” > myresultspassive.txt

cat myresultspassive.txt
```

## Part 2b
### First delete the old job
```
./kubectl delete -f ./job.yaml
```
### In the job.yaml file we will make one more change
```
# ADD a new parameter by CHANGING
        args: ["--pod"]
# to
        args: ["--pod”,”--quick”, “--active”]
```
#### NOTE: the --active argument extends the test to use finding to test for specific exploits. Better for security. Most effective run within the cluster.
### Let's try it again
```
./kubectl create -f ./job.yaml
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
