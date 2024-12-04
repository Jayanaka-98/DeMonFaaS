if [ -z "$1" ]; then
    echo "Error: Please include docker username as first arg." >&2
    exit 1  # Exit with a non-zero code to indicate an error
fi

kind create cluster --config cluster-config.yml

./rebuild_deploy.sh $1

kubectl config use-context kind-demonfaas-cluster

kubectl create configmap postgres-init-sql --from-file=init.sql -o yaml > postgres-init-sql.yaml

kubectl create configmap postgres-insert-sql --from-file=insert.sql -o yaml > postgres-insert-sql.yaml

cd controller/
./register_crd.sh $1
cd ..

# helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
# helm repo add stable https://charts.helm.sh/stable
# helm repo update
# kubectl create namespace monitoring
# helm install kind-prometheus prometheus-community/kube-prometheus-stack \
#   --namespace monitoring \
#   --set prometheus.service.nodePort=30000 \
#   --set prometheus.service.type=NodePort \
#   --set grafana.service.nodePort=31000 \
#   --set grafana.service.type=NodePort \
#   --set alertmanager.service.nodePort=32000 \
#   --set alertmanager.service.type=NodePort \
#   --set prometheus-node-exporter.service.nodePort=32001 \
#   --set prometheus-node-exporter.service.type=NodePort

# helm repo add openfaas https://openfaas.github.io/faas-netes/ 
# helm repo update
# # Creates the namespaces
# kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml
# # Create pods, deployments, and servicds
# helm install openfaas openfaas/openfaas --namespace openfaas --set gateway.externalURL=http://127.0.0.1:8081
# # saves password and logs in and deployss

# # MANUALLY DO
# PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
# echo "OpenFaaS admin password: $PASSWORD"
# echo -n $PASSWORD | faas-cli login -s
# faas-cli up
# # MANUALLY DO END

kubectl apply -f postgres-init-sql.yaml
kubectl apply -f postgres-insert-sql.yaml
kubectl apply -f deployment.yaml
# kubectl create namespace openfaas

./openfaas_deploy.sh