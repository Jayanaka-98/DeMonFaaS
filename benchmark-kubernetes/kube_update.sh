if [ -z "$1" ]; then
    echo "Error: Please include docker username as first arg." >&2
    exit 1  # Exit with a non-zero code to indicate an error
fi

docker build -t $1/demonfaas-benchmark-app:latest .

docker push $1/demonfaas-benchmark-app:latest

kubectl apply -f deployment.yaml