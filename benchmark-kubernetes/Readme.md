# Deploying to Kind Kubernetes Distro

I have created 3 bash scripts that will help locally deploy the application to kind, a kubernetes distro. See comments inside bash scripts to understand more of how they work. Be sure to login to docker before running the scripts. You can do so in the terminal by the following command. \
```docker login```

## IMPORTANT: You must go into deployment.yaml and controller-deployment-yml and change the image form stoneann5490 to your docker username.

## kube_create.sh
This bash script can be used to create a kubernetes cluster and deploy the sample app onto it. It takes in one argument, your docker username. See example below. \
```./kube_create.sh <dockeruser>```

### Verify Successful Deployment
Run the following commands. You should see both the benchmark app as well as a postgres db in both. The first gets the deployments and the second gets the services. \
```kubectl get pods``` \
```kubectl get svc``` \
You can also try sending a request to the app to verify its successfully deployed. Please run the following two lines of code in 2 separate terminal windows. The curl should return "Hello from app!" \
```kubectl port-forward svc/benchmark-app-service 8000:80``` \
```curl http://localhost:8080/``` 

### Testing
Here are some helpful commands to help test the code if there is a bug. \
```kubectl describe pod <podname>``` \
```kubectl log <podname>``` \
```kubectl get crds | grep apitransformations``` \
```kubectl get apitransformations -A``` \
```kubectl auth can-i list apitransformations --as=system:serviceaccount:default:apitransformation-controller```


## kube_delete.sh
This bash script can be used to delete the current cluster. It is helpful in restarting the cluster if things get too messy.

## kube_update.sh
If you make any updates to the source app, dockerfile, or deployment.yaml then you can run this bash script. If you changed any other files, it would be best to just delete the cluster via the kube_delete script and recreate it.

# Running the Benchmark

## Step 1: Install Jmeter
If you haven't run the tests before, run\
#### MacOS
 ```brew install jmeter ```

## Step 2: Run Jmeter
1. ```whereis jmeter```\
2. ```open <path to jmeter>```\

## Step 3: Run benchmark
1. Open benchmark. Any file ending in jmx is a Jmeter benchmark you can open. 
2. Click the green play button and wait until execution finishes. Note: may take 15 minutes
3. Open the aggregate results to see the latencies 