# Running the Benchmark

## Step 0: Create the python virtual environment (only if running application in local terminal)
If you haven't run the tests before, run\
1. ```python -m venv venv```\
2. ```source venv/bin/activate```\
3. ```pip install -r requirements.txt```\

## Step 1: Deploy to OpenFaaS
Follow the [instructions](https://docs.google.com/document/d/1q5SlrphUP3UjC4WZjoS6KGtU1CfBCuRGGXwgjHyj_Hk/edit?tab=t.0) in the google drive. Do not implement routing via the ingress operator. The benchmark calls the functions directly.\

## Step 2: Test Deployment Locally
Run the following curl to ensure the application has been deployed correctly. Output received should be "Hello from app!" \
```curl http://127.0.0.1:8080/function/benchmark-app/quickapi/test1```

## Step 3: Install Jmeter
If you haven't run the tests before, run\
#### MacOS
 ```brew install jmeter ```

## Step 4: Run Jmeter
1. ```whereis jmeter```\
2. ```open <path to jmeter>```\

## Step 5: Run benchmark
1. Open benchmark. Any file ending in jmx is a Jmeter benchmark you can open. 
2. Click the green play button and wait until execution finishes. Note: may take 15 minutes
3. Open the aggregate results to see the latencies 