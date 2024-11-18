# Deploying to Kind Kubernetes Distro

I have created 3 bash scripts that will help locally deploy the application to kind, a kubernetes distro. See comments inside bash scripts to understand more of how they work. Be sure to login to docker before running the scripts. You can do so in the terminal by the following command. \
```docker login```

## kube_create.sh
This bash script can be used to create a kubernetes cluster and deploy the sample app onto it. It takes in one argument, your docker username. See example below. \
```./kube_create.sh <dockeruser>``` \

### Verify Successful Deployment
Run the following commands. You should see both the benchmark app as well as a postgres db in both. The first gets the deployments and the second gets the services. \
```kubectl get pods``` \
```kubectl get svc``` \ 

### Testing
Here are some helpful commands to help test the code if there is a bug. \
```kubectl describe pod <podname>```
```kubectl log <podname>```

## kube_delete.sh
This bash script can be used to delete the current cluster. It is helpful in restarting the cluster if things get too messy.

## kube_update.sh
If you make any updates to the source app, dockerfile, or deployment.yaml then you can run this bash script. If you changed any other files, it would be best to just delete the cluster via the kube_delete script and recreate it.

