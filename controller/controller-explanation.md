# Kubernetes Controller for Dynamic API Routing - In-Depth Explanation

## 1. Core Components

### Custom Resource Definition (CRD)
```go
type ApiTransformation struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`
    Spec              ApiTransformationSpec   `json:"spec,omitempty"`
    Status            ApiTransformationStatus `json:"status,omitempty"`
}
```
- Defines a new Kubernetes resource type `ApiTransformation`
- Extends standard Kubernetes metadata
- Contains Spec (desired state) and Status (current state)

### Specification Structure
```go
type ApiTransformationSpec struct {
    SourceApi          string  `json:"sourceApi"`          // Original API endpoint
    ServerlessApi      string  `json:"serverlessApi"`      // OpenFaaS function endpoint
    ServerfulApi       string  `json:"serverfulApi"`       // WSGI application endpoint
    RequestThreshold   int64   `json:"requestThreshold"`   // Request count threshold
    LatencyThreshold   float64 `json:"latencyThreshold"`   // Response time threshold
    EvaluationInterval int     `json:"evaluationInterval"` // How often to check metrics
    CooldownPeriod     int     `json:"cooldownPeriod"`     // Minimum time between switches
}
```

## 2. Key Functionalities

### A. Metric Collection System
```go
func (r *ApiTransformationReconciler) getMetrics(ctx context.Context, apiPath string) (*Metrics, error) {
    metrics := &Metrics{}
    // Collects:
    // 1. Request rate (requests per second)
    // 2. Average latency
    // 3. Error rate
    // 4. CPU utilization
}
```

Key Metrics Monitored:
1. **Request Rate**: Number of requests per time unit
2. **Latency**: Average response time
3. **Error Rate**: Percentage of 5xx errors
4. **CPU Utilization**: Server resource usage

### B. Decision Making Logic
```go
func (r *ApiTransformationReconciler) shouldUseServerless(metrics *Metrics, spec *ApiTransformationSpec) bool {
    // Decides routing based on:
    // 1. High request volume
    // 2. Latency thresholds
    // 3. CPU utilization
}
```

Decision Factors:
- Switches to serverless when:
  - Request rate exceeds threshold
  - CPU utilization is high (>80%)
- Stays with serverful when:
  - Latency is critical
  - Request rate is manageable

### C. Request Routing System
```go
func ProxyHandler(w http.ResponseWriter, r *http.Request) {
    // 1. Gets routing decision from cache
    // 2. Determines target URL
    // 3. Sets up reverse proxy
    // 4. Forwards request with headers
}
```

Routing Process:
1. Intercepts incoming requests
2. Checks cached routing decision
3. Forwards to appropriate backend
4. Maintains request context and headers

## 3. Controller Operations

### A. Reconciliation Loop
```go
func (r *ApiTransformationReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // 1. Fetches current state
    // 2. Collects metrics
    // 3. Makes routing decision
    // 4. Updates status
    // 5. Stores decision in cache
}
```

Reconciliation Steps:
1. Retrieves ApiTransformation resource
2. Collects current metrics
3. Determines optimal routing
4. Updates resource status
5. Caches decision for proxy

### B. Caching System
```go
var routingCache = &sync.Map{}
```
- Thread-safe cache for routing decisions
- Prevents repetitive decision-making
- Enables fast request routing

## 4. Integration Points

### A. Prometheus Integration
```go
func queryPrometheusMetric(query string) (float64, error) {
    // 1. Constructs Prometheus query
    // 2. Sends HTTP request
    // 3. Parses response
    // 4. Returns metric value
}
```
- Queries Prometheus for metrics
- Uses PromQL for metric queries
- Handles response parsing

### B. Kubernetes Integration
```go
func (r *ApiTransformationReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&ApiTransformation{}).
        Complete(r)
}
```
- Registers with Kubernetes controller manager
- Watches ApiTransformation resources
- Handles resource events

## 5. Operational Flow

1. **Initialization**
   - Controller starts
   - Registers CRD
   - Sets up HTTP server
   - Initializes caches

2. **Continuous Operation**
   - Monitors ApiTransformation resources
   - Collects metrics periodically
   - Updates routing decisions
   - Handles incoming requests

3. **Request Handling**
   - Receives incoming request
   - Checks routing cache
   - Forwards to appropriate backend
   - Maintains request context

4. **State Management**
   - Updates resource status
   - Maintains routing cache
   - Handles reconciliation
   - Manages cooldown periods

