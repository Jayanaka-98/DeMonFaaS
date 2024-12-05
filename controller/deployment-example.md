# Deployment and Usage Guide

## 1. Deploy the Controller

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-routing-controller
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-routing-controller
  template:
    metadata:
      labels:
        app: api-routing-controller
    spec:
      containers:
      - name: controller
        image: api-routing-controller:latest
        ports:
        - containerPort: 8080
```

## 2. Create an ApiTransformation Resource

```yaml
apiVersion: myapi.example.com/v1
kind: ApiTransformation
metadata:
  name: my-api-route
spec:
  sourceApi: "/api/v1/data"
  serverlessApi: "http://openfaas-gateway:8080/function/my-function"
  serverfulApi: "http://wsgi-service:8000/api/v1/data"
  requestThreshold: 100
  latencyThreshold: 0.5
  evaluationInterval: 30
  cooldownPeriod: 300
```

## 3. Monitor Operation

```bash
# Watch the ApiTransformation status
kubectl get apitransformation my-api-route -o yaml

# Check controller logs
kubectl logs deployment/api-routing-controller

# Monitor metrics
kubectl port-forward svc/prometheus-k8s 9090:9090
```
