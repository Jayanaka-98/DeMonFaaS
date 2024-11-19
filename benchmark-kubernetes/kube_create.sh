if [ -z "$1" ]; then
    echo "Error: Please include docker username as first arg." >&2
    exit 1  # Exit with a non-zero code to indicate an error
fi

docker build -t $1/demonfaas-benchmark-app:latest .

docker push $1/demonfaas-benchmark-app:latest

kind create cluster --config cluster-config.yml

kind load docker-image $1/demonfaas-benchmark-app:latest --name demonfaas-cluster

kubectl config use-context kind-demonfaas-cluster

kubectl create configmap postgres-init-sql --from-file=init.sql -o yaml > postgres-init-sql.yaml

kubectl create configmap postgres-insert-sql --from-file=insert.sql -o yaml > postgres-insert-sql.yaml

cd controller/
./register_crd.sh $1
cd ..

kubectl apply -f postgres-init-sql.yaml
kubectl apply -f postgres-insert-sql.yaml
kubectl apply -f deployment.yaml