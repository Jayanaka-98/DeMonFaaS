# Registers yaml file with Kubernetes
kubectl apply -f api_transformation_definition.yml
# Adds a ApiTransformation to the Kubernetes cluster
kubectl apply -f api_transformation.yml
# Build the controller image that monitors that resource
go mod tidy
go build -o controller .
docker build -t stoneann/demonfaas-controller:latest .
docker push stoneann/demonfaas-controller:latest
