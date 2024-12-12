# Overview of DeMonFaaS

## benchmark
This folder contains the code for a deploying the benchmark app to openfaas as one function.

## benchmark-kubernetes
This folder contains the code for deploying the benchmark app to Kubernetes.

## benchmark-openfaas
This folder contains the code for deploying the benchmark app to openfaas as separate functions.

## controller
This folder contains all of the controller code, including the api transformation resources and bash scripts to deploy them.

## demonfaas
This folder contains some python wrapper code that was originally going to be in our implementation to help scan source files and identify 
functions. It did not make it into our final product.

## examples
This folder contains a bunch of python api examples that we tinkered with at the beginning of the project to see how they worked and how they could be deployed to openfaas.

## faas-cli
This folder contains the faas-cli code. Note here that we added a file, demonfaas.go, in the subfolder commands to implement our extra command.

## graph-data
This folder contains all data, graphs, and scripts to create graphs that we collected during the project.

## jmeter
This folder contains the jmeter workloads run. We mainly used the EvenlyDistributedWorkload.

## scripts
This folder contains all the helpful scripts we used to make deploying easier.

## tests
This folder contains tests we had for the python wrapper that did not make the final cut of the project.

# How to get Faas-CLI running

* Download Go 1.13 from https://golang.org/dl/

Then after installing run this command or place it in your `$HOME/.bash_profile`

```bash
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
```

* Now clone / build `faas-cli`:

from source run
```bash
mkdir -p $GOPATH/src/github.com/openfaas/
cd $GOPATH/src/github.com/openfaas/
cp -r faas-cli $GOPATH/src/github.com/openfaas/ faas-cli
$ cd $GOPATH/src/github.com/openfaas/faas-cli
$ make local-install
```

* Build multi-arch binaries

To build the release binaries type in:

```
./extract_binaries.sh
```