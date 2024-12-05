package main

import (
	"bytes"
	"context"
	"fmt"
	"io/ioutil"
	"math/rand/v2"
	"net/http"
	"net/http/httputil"
	"net/url"
	"sync"
	"time"

	"github.com/prometheus/common/expfmt"
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
	routingMap        = &sync.Map{}
	route_averages    = &sync.Map{}
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

type latencyAverages struct {
	slowAverage                 float64
	fastAverage                 float64
	slowWindow                  []float64
	fastWindow                  []float64
	slowMovingAverageWindowSize int
	fastMovingAverageWindowSize int
}

func (avg *latencyAverages) initAverages(slowSize int, fastSize int) {
	avg.slowMovingAverageWindowSize = slowSize
	avg.fastMovingAverageWindowSize = fastSize
	avg.slowWindow = make([]float64, 0)
	avg.fastWindow = make([]float64, 0)
}

func (avg *latencyAverages) updateAverages(latency float64) {
	avg.slowAverage += (latency / float64(avg.slowMovingAverageWindowSize))
	avg.slowWindow = append(avg.slowWindow, latency)

	avg.fastAverage += (latency / float64(avg.fastMovingAverageWindowSize))
	avg.fastWindow = append(avg.fastWindow, latency)

	if len(avg.slowWindow) > avg.slowMovingAverageWindowSize {
		avg.slowAverage -= (avg.slowWindow[0] / float64(avg.slowMovingAverageWindowSize))
		avg.slowWindow = avg.slowWindow[1:]
	}

	if len(avg.fastWindow) > avg.fastMovingAverageWindowSize {
		avg.fastAverage -= (avg.fastWindow[0] / float64(avg.slowMovingAverageWindowSize))
		avg.fastWindow = avg.fastWindow[1:]
	}
}

func (avg *latencyAverages) getAverage() float64 {
	return max(avg.slowAverage, avg.fastAverage)
}

func ChooseServerful(severful_percentage float64) bool {
	if rand.Float64() < severful_percentage {
		return true
	} else {
		return false
	}
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
	ServerfulPercentage float64
	LastUpdated         time.Time
	RequestCount        int64
	LatencyAvg          float64
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
	SourceApi                   string                   `json:"sourceApi"`
	ServerlessApi               string                   `json:"serverlessApi"`
	ServerfulApi                string                   `json:"serverfulApi"`
	RequestThreshold            int64                    `json:"requestThreshold"`
	LatencyThreshold            float64                  `json:"latencyThreshold"`
	EvaluationInterval          int                      `json:"evaluationInterval"`
	CooldownPeriod              int                      `json:"cooldownPeriod"`
	slowMovingAverageWindowSize int                      `json:"slowMovingAverageWindowSize"`
	fastMovingAverageWindowSize int                      `json:"fastMovingAverageWindowSize"`
	Routes                      []ApiTransformationRoute `json:"routes"`
}

type ApiTransformationRoute struct {
	Route    string `json:"route"`
	Function string `json:"function"`
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

	for _, route := range transformation.Spec.Routes {
		routingMap.Store(route.Route, route.Function)
		fmt.Printf("ROUTE: %s, FUNCTION: %s\n", route.Route, route.Function)
	}

	serverfulApiBase = transformation.Spec.ServerfulApi
	serverlessApiBase = transformation.Spec.ServerlessApi

	// Iterate through the sync.Map
	routingCache.Range(func(key, value interface{}) bool {
		route := key.(string) // Type assertion for key

		avgLatency, err := getAvgLatency(route)
		if err != nil {
			logger.Error(err, "Failed to get metrics")
		}

		// useServerless := r.shouldUseServerless(metrics, &transformation.Spec)
		_, ok := route_averages.Load(route)
		if !ok {
			avgObj := latencyAverages{}
			avgObj.initAverages(transformation.Spec.slowMovingAverageWindowSize, transformation.Spec.fastMovingAverageWindowSize)
			route_averages.Store(route, avgObj)
		}

		val, _ := route_averages.Load(route)
		avgObj := val.(latencyAverages)
		avgObj.updateAverages(avgLatency)
		route_averages.Store(route, avgObj)

		ratio := RatioCalculator(avgObj.getAverage(), transformation.Spec.LatencyThreshold)
		fmt.Println("UPDATED RATIO: ", ratio)

		routingCache.Store(route, &RoutingDecision{
			ServerfulPercentage: ratio,
			LastUpdated:         time.Now(),
			RequestCount:        int64(0),
			LatencyAvg:          avgLatency,
		})

		return true // Returning true to continue iteration
	})

	return ctrl.Result{
		RequeueAfter: time.Duration(transformation.Spec.EvaluationInterval) * time.Second,
	}, nil
}

func RatioCalculator(max_latency float64, latency_threshold float64) float64 {
	percentage_of_full := max_latency / latency_threshold
	if percentage_of_full >= 1 {
		return 0
	} else if percentage_of_full >= 0.6 {
		// 60 -> 80
		// 70 -> 60
		// 80 -> 40
		// 90 -> 20
		// 100 -> 0
		diff := percentage_of_full - 0.6
		return 1 - 2*diff
	} else {
		return 1
	}
}

func ProxyHandler(w http.ResponseWriter, r *http.Request) {
	sourceApi := r.URL.Path

	// Get routing decision from cache
	decision, ok := routingCache.Load(sourceApi)
	if !ok {
		var newRouteDecision = &RoutingDecision{
			ServerfulPercentage: 1,
			LastUpdated:         time.Now(),
			RequestCount:        1,
			LatencyAvg:          0,
		}

		routingCache.Store(sourceApi, newRouteDecision)
		decision = newRouteDecision
	}

	routingDecision := decision.(*RoutingDecision)
	var targetUrl string

	// Determine target URL based on routing decision
	if !ChooseServerful(routingDecision.ServerfulPercentage) {
		_, ok := routingMap.Load(sourceApi)
		if !ok {
			http.Error(w, "Invalid target URL", http.StatusInternalServerError)
			return
		}
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
	r.Header.Set("X-Routing-Type", fmt.Sprintf("serverless=%v", routingDecision.ServerfulPercentage))
	r.Host = target.Host

	// Forward the request
	proxy.ServeHTTP(w, r)
}

func getAvgLatency(route string) (float64, error) {
	// Step 1: Scrape metrics from the /metrics endpoint
	resp, err := http.Get("http://benchmark-app-service.default.svc.cluster.local:8080/metrics")
	if err != nil {
		fmt.Println("Error fetching metrics:", err)
		return 0, err
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Println("Error reading response body:", err)
		return 0, err
	}

	// Step 2: Parse metrics
	var parser expfmt.TextParser
	metrics, err := parser.TextToMetricFamilies(bytes.NewReader(body))
	if err != nil {
		fmt.Println("Error parsing metrics:", err)
		return 0, err
	}

	// Step 3: Extract latency metric
	metricName := "http_request_latency_seconds" // Adjust to your metric name
	if family, found := metrics[metricName]; found {
		for _, m := range family.GetMetric() {
			for _, label := range m.GetLabel() {
				if *label.Name == "endpoint" && *label.Value == route {
					if m.GetHistogram() != nil {
						hist := m.GetHistogram()
						count := float64(hist.GetSampleCount())
						sum := hist.GetSampleSum()
						// Calculate average latency
						if count > 0 {
							averageLatency := sum / count
							fmt.Printf("Average latency for endpoint %s: %.4f seconds\n", route, averageLatency)
							return averageLatency, nil
						} else {
							fmt.Println("No samples recorded for latency")
						}
					}
				}
			}
		}
	} else {
		fmt.Println("Latency metric not found")
	}
	return 0, nil
}

func queryPrometheusMetric(query string) (float64, error) {
	// Step 1: Scrape metrics from the /metrics endpoint
	resp, err := http.Get("http://benchmark-app-service.default.svc.cluster.local:8080/metrics")
	if err != nil {
		fmt.Println("Error fetching metrics:", err)
		return 0, err
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Println("Error reading response body:", err)
		return 0, err
	}

	// Step 2: Parse metrics
	var parser expfmt.TextParser
	metrics, err := parser.TextToMetricFamilies(bytes.NewReader(body))
	if err != nil {
		fmt.Println("Error parsing metrics:", err)
		return 0, err
	}

	// Step 3: Extract latency metric
	metricName := "http_request_latency_seconds" // Adjust to your metric name
	if family, found := metrics[metricName]; found {
		for _, m := range family.GetMetric() {
			if m.GetHistogram() != nil {
				hist := m.GetHistogram()
				count := float64(hist.GetSampleCount())
				sum := hist.GetSampleSum()

				// Calculate average latency
				if count > 0 {
					averageLatency := sum / count
					fmt.Printf("Average latency: %.4f seconds\n", averageLatency)
					return averageLatency, nil
				} else {
					fmt.Println("No samples recorded for latency")
				}
			}
		}
	} else {
		fmt.Println("Latency metric not found")
	}
	return 0, nil
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
