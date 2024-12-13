# DeMonFaaS

DeMonFaaS automates the decomposition of monolithic applications into hybrid Function-as-a-Service (FaaS) architectures. This system minimizes developer time and effort by automatically creating functions for python WSGI applications. By integrating with OpenFaaS, our solution abstracts away the complexity of serverless deployments. Through latency profiling and dynamic updates, DeMonFaaS will determine the optimal balance between FaaS and stateful containers, enhancing performance while reducing the barriers to adopting serverless computing. The results of DeMonFaaS under a singular application use case provide a promising foundation for further research.

### benchmark
This folder contains the code for a deploying the benchmark app to openfaas as one function.

### benchmark-kubernetes
This folder contains the code for deploying the benchmark app to Kubernetes.

### benchmark-openfaas
This folder contains the code for deploying the benchmark app to openfaas as separate functions.

### controller
This folder contains all of the controller code, including the api transformation resources and bash scripts to deploy them.

## demonfaas
This folder contains some python wrapper code that was originally going to be in our implementation to help scan source files and identify 
functions. It did not make it into our final product.

### examples
This folder contains a bunch of python api examples that we tinkered with at the beginning of the project to see how they worked and how they could be deployed to openfaas.

### faas-cli
This folder contains the faas-cli code. Note here that we added a file, demonfaas.go, in the subfolder commands to implement our extra command.

### graph-data
This folder contains all data, graphs, and scripts to create graphs that we collected during the project.

### jmeter
This folder contains the jmeter workloads run. We mainly used the EvenlyDistributedWorkload.

### scripts
This folder contains all the helpful scripts we used to make deploying easier.

### tests
This folder contains tests we had for the python wrapper that did not make the final cut of the project.

## How to get Faas-CLI running

* Download Go 1.13 from https://golang.org/dl/

Then after installing run this command or place it in your `$HOME/.bash_profile`

```bash
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
```

* Now clone / build `faas-cli`:

run
```bash
mkdir -p $GOPATH/src/github.com/openfaas/
cd $GOPATH/src/github.com/openfaas/
git clone https://github.com/openfaas/faas-cli
cd faas-cli
make local-install
```

## Installing DeMonFaaS Extention

As DeMonFaaS is an extention for faas-cli, the previous step of installing faas-cli locally must be completed.

Then from repo source,
```bash
cd faas-cli
make build_nested
```

This will install the extention.

## Using DeMonFaaS,

Login to your DockerHub account using `docker login`. Then go to source and,

```bash
faas-cli demonfaas --path benchmark-kubernetes/ --username <your-dockerhub-username>
```

This will deploy the already split function to openfaas.

> **Note :**
>
> The Kubernates cluster must be installed before running this command by running `./scripts/kube_create.sh <your-dockerhub-username>`