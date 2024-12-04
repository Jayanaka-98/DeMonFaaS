if [ -z "$1" ]; then
    echo "Error: Please include docker username as first arg." >&2
    exit 1  # Exit with a non-zero code to indicate an error
fi

docker build -t $1/demonfaas-benchmark-app-kubernetes:latest -f Dockerfile.kubernetes .

docker push $1/demonfaas-benchmark-app-kubernetes:latest

kind load docker-image $1/demonfaas-benchmark-app-kubernetes:latest --name demonfaas-cluster
