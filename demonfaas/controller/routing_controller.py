import time
import requests
from kubernetes import client, config

config.load_kube_config()

def get_workload_metrics():
    response = requests.get('http://prometheus-server/api/v1/query', params={
        'query': 'rate(container_cpu_usage_seconds_total{pod="wsgi-app"}[1m])'
    })
    return float(response.json()['data']['result'][0]['value'][1])

def update_ingress_route(use_serverless):
    v1 = client.NetworkingV1Api()
    ingress = v1.read_namespaced_ingress(name="wsgi-ingress", namespace="default")
    
    if use_serverless:
        ingress.spec.rules[0].http.paths[0].backend.service.name = "wsgi-function"
    else:
        ingress.spec.rules[0].http.paths[0].backend.service.name = "wsgi-app"

    v1.replace_namespaced_ingress(name="wsgi-ingress", namespace="default", body=ingress)
    print(f"Routed to {'serverless' if use_serverless else 'continuous'} instance")

while True:
    cpu_usage = get_workload_metrics()
    print(f"Current CPU Usage: {cpu_usage}")

    if cpu_usage > 0.7:
        update_ingress_route(use_serverless=True)
    else:
        update_ingress_route(use_serverless=False)
    
    time.sleep(10)
