#!/bin/bash

if [ -z "$1" ]; then
    echo "Error: Please include docker username as first arg." >&2
    exit 1  # Exit with a non-zero code to indicate an error
fi

cd controller

# Delete controller deployment
echo "Deleting controller deployment..."
kubectl delete -f controller-deployment.yml

# Remove the controller image from kind cluster
echo "Removing controller image from kind cluster..."
# Note: There's no direct 'unload' in kind, the image will be removed when the resources are deleted

# Remove the docker image (both locally and from registry)
echo "Removing docker images..."
docker rmi $1/demonfaas-controller:latest
docker push $1/demonfaas-controller:latest

# Delete controller RBAC resources
echo "Deleting controller RBAC resources..."
kubectl delete -f controller-role-binding.yml
kubectl delete -f controller-role.yml
kubectl delete -f controller-service-account.yml

# Delete ApiTransformation resources
echo "Deleting ApiTransformation resources..."
kubectl delete -f api-transformation.yml
kubectl delete -f api-transformation-definition.yml

echo "Cleanup completed successfully"

cd ..