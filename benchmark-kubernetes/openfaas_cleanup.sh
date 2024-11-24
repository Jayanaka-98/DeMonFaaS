echo "Starting cleanup..."

# Delete OpenFaaS namespace and resources
echo "Cleaning up OpenFaaS..."
helm uninstall openfaas --namespace openfaas 2>/dev/null || true
kubectl delete namespace openfaas 2>/dev/null || true
kubectl delete namespace openfaas-fn 2>/dev/null || true

# Delete Prometheus Stack and monitoring namespace
echo "Cleaning up Prometheus Stack..."
helm uninstall kind-prometheus --namespace monitoring 2>/dev/null || true
kubectl delete namespace monitoring 2>/dev/null || true

# Remove Helm repositories
echo "Removing Helm repositories..."
helm repo remove prometheus-community 2>/dev/null || true
helm repo remove stable 2>/dev/null || true
helm repo remove openfaas 2>/dev/null || true

# Update Helm repositories
helm repo update

echo "Cleanup completed!"

# Optional: verify cleanup
echo "Verifying cleanup..."
echo "Checking namespaces:"
echo "Checking helm repositories:"
helm repo list | grep -E 'prometheus-community|stable|openfaas'