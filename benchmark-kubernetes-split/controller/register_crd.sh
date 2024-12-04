if [ -z "$1" ]; then
    echo "Error: Please include docker username as first arg." >&2
    exit 1  # Exit with a non-zero code to indicate an error
fi

# Registers yaml file with Kubernetes
kubectl apply -f api-transformation-definition.yml

# Adds a ApiTransformation to the Kubernetes cluster
kubectl apply -f api-transformation.yml

# Deploy role necessary to watch api transformation
kubectl apply -f controller-service-account.yml
kubectl apply -f controller-role.yml
kubectl apply -f controller-role-binding.yml

# Build the controller image that monitors that resource
go install sigs.k8s.io/controller-tools/cmd/controller-gen@latest
go mod tidy
~/go/bin/controller-gen object paths=./...

docker build -t $1/demonfaas-controller:latest .
docker push $1/demonfaas-controller:latest

kind load docker-image $1/demonfaas-controller:latest --name demonfaas-cluster

kubectl apply -f controller-deployment.yml

# kubectl port-forward $(kubectl get pods | grep demonfaas-controller | awk '{print $1}') 8000:9000
# kubectl logs $(kubectl get pods | grep demonfaas-controller | awk '{print $1}')