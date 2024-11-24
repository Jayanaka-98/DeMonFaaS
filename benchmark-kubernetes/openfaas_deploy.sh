#!/bin/bash

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add stable https://charts.helm.sh/stable
helm repo update
kubectl create namespace monitoring
echo "Installing Prometheus Stack..."
helm install kind-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.service.nodePort=30000 \
  --set prometheus.service.type=NodePort \
  --set grafana.service.nodePort=31000 \
  --set grafana.service.type=NodePort \
  --set alertmanager.service.nodePort=32000 \
  --set alertmanager.service.type=NodePort \
  --set prometheus-node-exporter.service.nodePort=32001 \
  --set prometheus-node-exporter.service.type=NodePort  #\
#   --debug --wait

helm repo add openfaas https://openfaas.github.io/faas-netes/ 
helm repo update
# Creates the namespaces
kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml
# Create pods, deployments, and servicds
helm install openfaas openfaas/openfaas --namespace openfaas --set gateway.externalURL=http://127.0.0.1:8080
# saves password and logs in and deployss

# MANUALLY DO
PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
kubectl -n openfaas port-forward svc/gateway 8080:8080 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!
echo $! > port_forward.pid
echo "Waiting for port-forwarding to become ready..."
while ! nc -z 127.0.0.1 8080; do
    sleep 1
done
echo "Port-forwarding is ready."
echo "Port forwarding started with PID $PORT_FORWARD_PID"
echo -n $PASSWORD | faas-cli login -s
faas-cli up
# MANUALLY DO END
echo "OpenFaaS admin password: $PASSWORD"
kubectl create namespace openfaas