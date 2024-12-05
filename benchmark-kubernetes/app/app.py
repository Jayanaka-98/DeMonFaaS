from flask import Flask
from app.apis.quick import quick_api
from app.apis.compute import compute_api
from app.apis.data import data_api
from prometheus_client import start_http_server, Counter, Histogram, Gauge

# Create the Flask app
app = Flask(__name__)

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total number of HTTP requests', ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'http_request_latency_seconds', 'Latency of HTTP requests in seconds', ['method', 'endpoint']
)
ACTIVE_REQUESTS = Gauge(
    'http_active_requests', 'Number of active requests', ['method', 'endpoint']
)

# Start Prometheus metrics server
with app.app_context():
    start_http_server(8080)  # Expose metrics on port 8080

# Middleware to collect metrics
import time
from flask import request
@app.before_request
def before_request():
    request.start_time = time.time()


@app.after_request
def after_request(response):
    # Record latency
    request_latency = time.time() - request.start_time
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.path).observe(request_latency)

    # Record request count
    REQUEST_COUNT.labels(
        method=request.method, endpoint=request.path, http_status=response.status_code
    ).inc()

    # Track active requests
    ACTIVE_REQUESTS.labels(method=request.method, endpoint=request.path).inc()
    ACTIVE_REQUESTS.labels(method=request.method, endpoint=request.path).dec()

    return response

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


# Define a route within app
@app.route('/')
def index():
    return 'Hello from app!'

# Register the blueprints with the app
app.register_blueprint(quick_api)
app.register_blueprint(compute_api)
app.register_blueprint(data_api)

if __name__ == '__main__':
    app.run()