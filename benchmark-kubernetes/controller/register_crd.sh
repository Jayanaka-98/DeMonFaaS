if [ -z "$1" ]; then
    echo "Error: Please include docker username as first arg." >&2
    exit 1  # Exit with a non-zero code to indicate an error
fi

# Registers yaml file with Kubernetes
kubectl apply -f api-transformation-definition.yml

# Adds a ApiTransformation to the Kubernetes cluster
kubectl apply -f api-transformation.yml

# Build the controller image that monitors that resource
docker build -t $1/demonfaas-controller:v1 .
docker push $1/demonfaas-controller:v1

kind load docker-image $1/demonfaas-controller:v1 --name demonfaas-cluster

kubectl apply -f controller-deployment.yml