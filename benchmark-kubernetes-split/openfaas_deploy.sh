#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for a deployment to be ready
wait_for_deployment() {
    local namespace=$1
    local deployment=$2
    local timeout=$3
    local counter=0
    
    echo "Waiting for deployment $deployment in namespace $namespace to be ready..."
    while ! kubectl -n "$namespace" get deployment "$deployment" >/dev/null 2>&1 || \
          [ "$(kubectl -n "$namespace" get deployment "$deployment" -o jsonpath='{.status.readyReplicas}')" != \
            "$(kubectl -n "$namespace" get deployment "$deployment" -o jsonpath='{.spec.replicas}')" ]; do
        sleep 2
        counter=$((counter + 2))
        if [ $counter -ge $timeout ]; then
            echo "Timeout waiting for deployment $deployment after ${timeout} seconds"
            return 1
        fi
        echo "Waiting for deployment... ($counter seconds)"
    done
    echo "Deployment $deployment is ready!"
    return 0
}

# Check required commands
for cmd in helm kubectl nc faas-cli; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Install Prometheus Stack
echo "Setting up Prometheus Stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add stable https://charts.helm.sh/stable
helm repo update

# kubectl create namespace monitoring 2>/dev/null || true
echo "Installing Prometheus Stack..."
helm install kind-prometheus prometheus-community/kube-prometheus-stack \
    --namespace default \
    --set prometheus.service.nodePort=30000 \
    --set prometheus.service.type=NodePort \
    --set grafana.service.nodePort=31000 \
    --set grafana.service.type=NodePort \
    --set alertmanager.service.nodePort=32000 \
    --set alertmanager.service.type=NodePort \
    --set prometheus-node-exporter.service.nodePort=32001 \
    --set prometheus-node-exporter.service.type=NodePort

# Install OpenFaaS
echo "Setting up OpenFaaS..."
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update

# Create namespaces
kubectl create namespace openfaas 2>/dev/null || true
kubectl create namespace openfaas-fn 2>/dev/null || true
kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml

# Install OpenFaaS
echo "Installing OpenFaaS..."
helm install openfaas openfaas/openfaas \
    --namespace openfaas \
    --set gateway.externalURL=http://127.0.0.1:8080

# Wait for OpenFaaS gateway deployment to be ready
if ! wait_for_deployment "openfaas" "gateway" 120; then
    echo "Failed to deploy OpenFaaS gateway"
    exit 1
fi

# Get the password
echo "Retrieving OpenFaaS password..."
PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
if [ -z "$PASSWORD" ]; then
    echo "Error: Could not retrieve OpenFaaS password"
    exit 1
fi

# Clean up existing port-forward
if [ -f port_forward.pid ]; then
    pid=$(cat port_forward.pid)
    kill $pid 2>/dev/null || true
    rm port_forward.pid
    # Wait a moment for the port to be released
    sleep 2
fi

# Check if port 8080 is already in use
if nc -z 127.0.0.1 8080 2>/dev/null; then
    echo "Error: Port 8080 is already in use"
    exit 1
fi

# Start port-forwarding
echo "Starting port-forwarding..."
kubectl -n openfaas port-forward svc/gateway 8080:8080 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!
echo $PORT_FORWARD_PID > port_forward.pid

# Wait for port-forward to be ready
echo "Waiting for port-forwarding to become ready..."
TIMEOUT=30
counter=0
while ! nc -z 127.0.0.1 8080; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $TIMEOUT ]; then
        echo "Timeout waiting for port-forward after ${TIMEOUT} seconds"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        rm port_forward.pid
        exit 1
    fi
    echo "Waiting... ($counter seconds)"
done

echo "Port-forwarding is ready."
echo "Port forwarding started with PID $PORT_FORWARD_PID"

# Login to OpenFaaS
echo "Logging in to OpenFaaS..."
echo -n $PASSWORD | faas-cli login -s

# Deploy functions
echo "Deploying OpenFaaS functions..."
faas-cli up

echo "Setup complete!"
echo "OpenFaaS admin password: $PASSWORD"
echo "OpenFaaS UI available at: http://127.0.0.1:8080/ui/"
echo "Grafana available at: http://localhost:31000"
echo "Prometheus available at: http://localhost:30000"
echo "AlertManager available at: http://localhost:32000"