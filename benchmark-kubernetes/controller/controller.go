package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strconv"
	"sync"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	"sigs.k8s.io/controller-runtime/pkg/scheme"
)

var (
	logger            = log.Log.WithName("api-routing-controller")
	routingCache      = &sync.Map{}
	serverlessApiBase = ""
	serverfulApiBase  = ""
	countServerless   = 0
	countServerful    = 0
)

// GroupVersion is group version used to register these objects
var GroupVersion = schema.GroupVersion{Group: "myapi.example.com", Version: "v1"}

// SchemeBuilder is used to add go types to the GroupVersionKind scheme
var SchemeBuilder = &scheme.Builder{GroupVersion: GroupVersion}

// AddToScheme adds the types in this group-version to the given scheme.
func AddToScheme(s *runtime.Scheme) error {
	SchemeBuilder.Register(&ApiTransformation{}, &ApiTransformationList{})
	return nil
}

// ApiTransformation defines the custom resource
// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
type ApiTransformation struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec              ApiTransformationSpec   `json:"spec,omitempty"`
	Status            ApiTransformationStatus `json:"status,omitempty"`
}

// ApiTransformationList contains a list of ApiTransformation
// +kubebuilder:object:root=true
type ApiTransformationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ApiTransformation `json:"items"`
}

type RoutingDecision struct {
	UseServerless bool
	LastUpdated   time.Time
	RequestCount  int64
	LatencyAvg    float64
}

// DeepCopyInto copies all properties of this object into another object of the same type
func (in *ApiTransformation) DeepCopyInto(out *ApiTransformation) {
	*out = *in
	out.TypeMeta = in.TypeMeta
	in.ObjectMeta.DeepCopyInto(&out.ObjectMeta)
	out.Spec = in.Spec
	in.Status.DeepCopyInto(&out.Status)
}

// DeepCopy creates a deep copy of ApiTransformation
func (in *ApiTransformation) DeepCopy() *ApiTransformation {
	if in == nil {
		return nil
	}
	out := new(ApiTransformation)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyObject implements runtime.Object interface
func (in *ApiTransformation) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

// DeepCopyInto copies all properties of this object into another object of the same type
func (in *ApiTransformationList) DeepCopyInto(out *ApiTransformationList) {
	*out = *in
	out.TypeMeta = in.TypeMeta
	in.ListMeta.DeepCopyInto(&out.ListMeta)
	if in.Items != nil {
		in, out := &in.Items, &out.Items
		*out = make([]ApiTransformation, len(*in))
		for i := range *in {
			(*in)[i].DeepCopyInto(&(*out)[i])
		}
	}
}

// DeepCopy creates a deep copy of ApiTransformationList
func (in *ApiTransformationList) DeepCopy() *ApiTransformationList {
	if in == nil {
		return nil
	}
	out := new(ApiTransformationList)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyObject implements runtime.Object interface
func (in *ApiTransformationList) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

type ApiTransformationSpec struct {
	SourceApi          string  `json:"sourceApi"`
	ServerlessApi      string  `json:"serverlessApi"`
	ServerfulApi       string  `json:"serverfulApi"`
	RequestThreshold   int64   `json:"requestThreshold"`
	LatencyThreshold   float64 `json:"latencyThreshold"`
	EvaluationInterval int     `json:"evaluationInterval"`
	CooldownPeriod     int     `json:"cooldownPeriod"`
}

type ApiTransformationStatus struct {
	CurrentTarget  string      `json:"currentTarget"`
	LastUpdateTime metav1.Time `json:"lastUpdateTime"`
	CurrentMetrics Metrics     `json:"currentMetrics"`
}

// DeepCopyInto copies all properties of this object into another object of the same type
func (in *ApiTransformationStatus) DeepCopyInto(out *ApiTransformationStatus) {
	*out = *in
	in.LastUpdateTime.DeepCopyInto(&out.LastUpdateTime)
	out.CurrentMetrics = in.CurrentMetrics
}

type Metrics struct {
	RequestRate    float64 `json:"requestRate"`
	AvgLatency     float64 `json:"avgLatency"`
	ErrorRate      float64 `json:"errorRate"`
	CPUUtilization float64 `json:"cpuUtilization"`
}

// PrometheusResponse structure for metric queries
type PrometheusResponse struct {
	Status string `json:"status"`
	Data   struct {
		Result []struct {
			Metric map[string]string `json:"metric"`
			Value  []interface{}     `json:"value"`
		} `json:"result"`
	} `json:"data"`
}

type ApiTransformationReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

func (r *ApiTransformationReconciler) getMetrics(ctx context.Context, apiPath string) (*Metrics, error) {
	metrics := &Metrics{}

	// Query request rate
	requestRateQuery := fmt.Sprintf(`rate(http_requests_total{path="%s"}[5m])`, apiPath)
	if requestRate, err := queryPrometheusMetric(requestRateQuery); err == nil {
		metrics.RequestRate = requestRate
	}

	// Query latency
	latencyQuery := fmt.Sprintf(`rate(http_request_duration_seconds_sum{path="%s"}[5m]) / rate(http_request_duration_seconds_count{path="%s"}[5m])`, apiPath, apiPath)
	if latency, err := queryPrometheusMetric(latencyQuery); err == nil {
		metrics.AvgLatency = latency
	}

	// Query error rate
	errorRateQuery := fmt.Sprintf(`rate(http_requests_total{path="%s",status=~"5.."}[5m]) / rate(http_requests_total{path="%s"}[5m])`, apiPath, apiPath)
	if errorRate, err := queryPrometheusMetric(errorRateQuery); err == nil {
		metrics.ErrorRate = errorRate
	}

	// Query CPU utilization
	cpuQuery := fmt.Sprintf(`sum(rate(container_cpu_usage_seconds_total{container=~"%s"}[5m])) / sum(container_spec_cpu_quota{container=~"%s"}) * 100`, apiPath, apiPath)
	if cpuUtil, err := queryPrometheusMetric(cpuQuery); err == nil {
		metrics.CPUUtilization = cpuUtil
	}

	return metrics, nil
}

func (r *ApiTransformationReconciler) shouldUseServerless(metrics *Metrics, spec *ApiTransformationSpec) bool {
	// Decision logic based on multiple factors
	if metrics.RequestRate > float64(spec.RequestThreshold) {
		return true
	}
	if metrics.AvgLatency > spec.LatencyThreshold {
		return false
	}
	if metrics.CPUUtilization > 80 { // High CPU utilization on serverful
		return true
	}
	return false
}

// SetupWithManager sets up the controller with the Manager
func (r *ApiTransformationReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&ApiTransformation{}).
		Complete(r)
}

func (r *ApiTransformationReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)
	logger.Info("Reconciling ApiTransformation", "namespacedName", req.NamespacedName)

	var transformation ApiTransformation
	if err := r.Get(ctx, req.NamespacedName, &transformation); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	serverfulApiBase = transformation.Spec.ServerfulApi
	serverlessApiBase = transformation.Spec.ServerlessApi

	// Iterate through the sync.Map
	routingCache.Range(func(key, value interface{}) bool {
		route := key.(string) // Type assertion for key
		// ip := value.(string)  // Type assertion for value

		metrics, err := r.getMetrics(ctx, transformation.Spec.SourceApi+route)
		if err != nil {
			logger.Error(err, "Failed to get metrics")
		}

		useServerless := r.shouldUseServerless(metrics, &transformation.Spec)

		routingCache.Store(route, &RoutingDecision{
			UseServerless: useServerless,
			LastUpdated:   time.Now(),
			RequestCount:  int64(metrics.RequestRate),
			LatencyAvg:    metrics.AvgLatency,
		})

		return true // Returning true to continue iteration
	})

	// Update status
	// transformation.Status.CurrentMetrics = *metrics
	// transformation.Status.LastUpdateTime = metav1.Now()
	// transformation.Status.CurrentTarget = transformation.Spec.ServerfulApi
	// if useServerless {
	// 	transformation.Status.CurrentTarget = transformation.Spec.ServerlessApi
	// }

	// Store decision in cache
	// routingCache.Store(transformation.Spec.SourceApi, &RoutingDecision{
	// 	UseServerless: useServerless,
	// 	LastUpdated:   time.Now(),
	// 	RequestCount:  int64(metrics.RequestRate),
	// 	LatencyAvg:    metrics.AvgLatency,
	// })

	// fmt.Println("\n\nTRANSFORMATION: ", transformation)
	// if err := r.Update(ctx, &transformation); err != nil {
	// 	logger.Error(err, "Failed to update ApiTransformation status")
	// 	return ctrl.Result{}, err
	// }

	return ctrl.Result{
		RequeueAfter: time.Duration(transformation.Spec.EvaluationInterval) * time.Second,
	}, nil
}

func ProxyHandler(w http.ResponseWriter, r *http.Request) {
	sourceApi := r.URL.Path

	// Get routing decision from cache
	decision, ok := routingCache.Load(sourceApi)
	if !ok {
		var newRouteDecision = &RoutingDecision{
			UseServerless: false,
			LastUpdated:   time.Now(),
			RequestCount:  1,
			LatencyAvg:    0,
		}
		routingCache.Store(sourceApi, newRouteDecision)
		decision = newRouteDecision
	}

	routingDecision := decision.(*RoutingDecision)
	var targetUrl string

	// Determine target URL based on routing decision
	if routingDecision.UseServerless {
		targetUrl = serverlessApiBase
		countServerless += 1
		fmt.Printf("*** Serverless Count: %d", countServerless)
	} else {
		targetUrl = serverfulApiBase
		countServerful += 1
		fmt.Printf("*** Serverful Count: %d", countServerful)
	}

	// Create target URL
	target, err := url.Parse(targetUrl)
	if err != nil {
		http.Error(w, "Invalid target URL", http.StatusInternalServerError)
		return
	}

	// Create reverse proxy
	proxy := httputil.NewSingleHostReverseProxy(target)

	proxy.ModifyResponse = func(resp *http.Response) error {
		fmt.Println(resp)
		return nil
	}
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		http.Error(w, "Proxy error "+err.Error(), http.StatusBadGateway)
	}
	proxy.Transport = nil

	// Update request headers
	r.URL.Host = target.Host
	r.URL.Scheme = target.Scheme
	r.Header.Set("X-Forwarded-Host", r.Header.Get("Host"))
	r.Header.Set("X-Routing-Type", fmt.Sprintf("serverless=%v", routingDecision.UseServerless))
	r.Host = target.Host

	// Forward the request
	proxy.ServeHTTP(w, r)
}

func queryPrometheusMetric(query string) (float64, error) {
	prometheusURL := "http://prometheus-operated.monitoring.svc.cluster.local:9090"
	resp, err := http.Get(fmt.Sprintf("%s/api/v1/query?query=%s", prometheusURL, url.QueryEscape(query)))
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	var result PrometheusResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}

	if len(result.Data.Result) == 0 {
		return 0, fmt.Errorf("no data found")
	}

	// Extract value
	value, ok := result.Data.Result[0].Value[1].(string)
	if !ok {
		return 0, fmt.Errorf("invalid value type")
	}

	return strconv.ParseFloat(value, 64)
}

func main() {
	// Set up the logger (this is the default logger)
	// log.SetLogger(controller_runtime.NewLogger())
	ctrl.SetLogger(zap.New(zap.UseDevMode(true)))
	fmt.Println("Starting the controller")

	scheme := runtime.NewScheme()
	_ = AddToScheme(scheme)
	// metav1.AddMetaToScheme(scheme)
	scheme.AddKnownTypes(GroupVersion,
		&ApiTransformation{}, // Add your custom ApiTransformation type here
		&ApiTransformationList{},
	)
	metav1.AddToGroupVersion(scheme, GroupVersion)

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
	})
	if err != nil {
		panic(fmt.Sprintf("unable to start manager: %v", err))
	}

	// Start HTTP server for request routing
	go func() {
		http.HandleFunc("/", ProxyHandler)
		if err := http.ListenAndServe(":9000", nil); err != nil {
			panic(fmt.Sprintf("failed to start HTTP server: %v", err))
		}
	}()

	if err := (&ApiTransformationReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		panic(fmt.Sprintf("unable to create controller: %v", err))
	}

	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		panic(fmt.Sprintf("problem running manager: %v", err))
	}
}
