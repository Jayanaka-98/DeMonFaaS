package controller

import (
	"context"
	"fmt"
	"time"

	"github.com/prometheus/client_golang/api"
	v1 "github.com/prometheus/client_golang/api/prometheus/v1"
	"github.com/prometheus/common/model"
	"go.uber.org/zap"
	"golang.org/x/time/rate"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// Configuration holds the controller settings
type Config struct {
	Namespace       string
	WSGIService     string
	OpenFaaSService string
	Thresholds      Thresholds
	CheckInterval   time.Duration
}

// Thresholds defines the metrics thresholds for decision making
type Thresholds struct {
	CPUUsage    float64
	MemoryUsage float64
	RequestRate float64
	ErrorRate   float64
}

// MetricsData holds the current metrics
type MetricsData struct {
	CPUUsage    float64
	MemoryUsage float64
	RequestRate float64
	ErrorRate   float64
	Latency     float64
	Timestamp   time.Time
}

type RequestRouter struct {
	config       Config
	kubeClient   *kubernetes.Clientset
	promClient   v1.API
	logger       *zap.Logger
	limiter      *rate.Limiter
	metricsCache []MetricsData
	failureCount int
}

func NewRequestRouter(config Config) (*RequestRouter, error) {
	// Initialize logger
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to initialize logger: %v", err)
	}

	// Initialize Kubernetes client
	kubeConfig, err := rest.InClusterConfig()
	if err != nil {
		return nil, fmt.Errorf("failed to get cluster config: %v", err)
	}

	kubeClient, err := kubernetes.NewForConfig(kubeConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create kubernetes client: %v", err)
	}

	// Initialize Prometheus client
	promClient, err := api.NewClient(api.Config{
		Address: "http://prometheus-server.monitoring:9090",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create prometheus client: %v", err)
	}

	return &RequestRouter{
		config:       config,
		kubeClient:   kubeClient,
		promClient:   v1.NewAPI(promClient),
		logger:       logger,
		limiter:      rate.NewLimiter(rate.Every(10*time.Second), 1), // Limit routing changes
		metricsCache: make([]MetricsData, 0, 10),
	}, nil
}

func (r *RequestRouter) getMetrics(ctx context.Context) (*MetricsData, error) {
	metrics := &MetricsData{Timestamp: time.Now()}
	var err error

	// Query CPU usage with error rate tracking
	cpuQuery := fmt.Sprintf(`
        avg(rate(container_cpu_usage_seconds_total{namespace="%s"}[5m]))
    `, r.config.Namespace)

	if metrics.CPUUsage, err = r.queryPrometheus(ctx, cpuQuery); err != nil {
		return nil, fmt.Errorf("CPU metric query failed: %v", err)
	}

	// Query memory usage with error handling
	memQuery := fmt.Sprintf(`
        avg(container_memory_usage_bytes{namespace="%s"} / 
        container_memory_max_usage_bytes * 100)
    `, r.config.Namespace)

	if metrics.MemoryUsage, err = r.queryPrometheus(ctx, memQuery); err != nil {
		return nil, fmt.Errorf("memory metric query failed: %v", err)
	}

	// Query request rate and error rate
	reqQuery := fmt.Sprintf(`
        sum(rate(http_requests_total{namespace="%s"}[5m]))
    `, r.config.Namespace)

	errQuery := fmt.Sprintf(`
        sum(rate(http_requests_errors_total{namespace="%s"}[5m])) /
        sum(rate(http_requests_total{namespace="%s"}[5m])) * 100
    `, r.config.Namespace, r.config.Namespace)

	if metrics.RequestRate, err = r.queryPrometheus(ctx, reqQuery); err != nil {
		return nil, fmt.Errorf("request rate query failed: %v", err)
	}

	if metrics.ErrorRate, err = r.queryPrometheus(ctx, errQuery); err != nil {
		return nil, fmt.Errorf("error rate query failed: %v", err)
	}

	// Cache metrics for trend analysis
	r.metricsCache = append(r.metricsCache, *metrics)
	if len(r.metricsCache) > 10 {
		r.metricsCache = r.metricsCache[1:]
	}

	return metrics, nil
}

func (r *RequestRouter) queryPrometheus(ctx context.Context, query string) (float64, error) {
	result, _, err := r.promClient.Query(ctx, query, time.Now())
	if err != nil {
		return 0, err
	}

	if result.Type() != model.ValVector {
		return 0, fmt.Errorf("unexpected result type: %s", result.Type())
	}

	vector := result.(model.Vector)
	if len(vector) == 0 {
		return 0, fmt.Errorf("no data points found")
	}

	return float64(vector[0].Value), nil
}

func (r *RequestRouter) analyzeTrends() (bool, float64) {
	if len(r.metricsCache) < 2 {
		return false, 0
	}

	// Calculate rate of change for key metrics
	var cpuTrend, memTrend, reqTrend float64
	for i := 1; i < len(r.metricsCache); i++ {
		cpuTrend += r.metricsCache[i].CPUUsage - r.metricsCache[i-1].CPUUsage
		memTrend += r.metricsCache[i].MemoryUsage - r.metricsCache[i-1].MemoryUsage
		reqTrend += r.metricsCache[i].RequestRate - r.metricsCache[i-1].RequestRate
	}

	// Normalize trends
	n := float64(len(r.metricsCache) - 1)
	cpuTrend /= n
	memTrend /= n
	reqTrend /= n

	// Calculate composite trend score
	trendScore := (cpuTrend + memTrend + reqTrend) / 3
	rapidChange := abs(trendScore) > 10.0 // Threshold for rapid change

	return rapidChange, trendScore
}

func (r *RequestRouter) shouldUseServerless(metrics *MetricsData) (bool, error) {
	// Check rate limiting
	if !r.limiter.Allow() {
		return false, fmt.Errorf("rate limit exceeded for routing changes")
	}

	// Get trend analysis
	rapidChange, trendScore := r.analyzeTrends()

	// Decision logic based on current metrics and trends
	useServerless := false
	reason := ""

	switch {
	case metrics.CPUUsage > r.config.Thresholds.CPUUsage:
		useServerless = true
		reason = "CPU usage exceeded threshold"
	case metrics.MemoryUsage > r.config.Thresholds.MemoryUsage:
		useServerless = true
		reason = "Memory usage exceeded threshold"
	case metrics.RequestRate > r.config.Thresholds.RequestRate:
		useServerless = true
		reason = "Request rate exceeded threshold"
	case metrics.ErrorRate > r.config.Thresholds.ErrorRate:
		useServerless = true
		reason = "Error rate exceeded threshold"
	case rapidChange && trendScore > 0:
		useServerless = true
		reason = "Rapid increase in resource usage detected"
	}

	if useServerless {
		r.logger.Info("Switching to serverless",
			zap.String("reason", reason),
			zap.Float64("cpu_usage", metrics.CPUUsage),
			zap.Float64("memory_usage", metrics.MemoryUsage),
			zap.Float64("request_rate", metrics.RequestRate),
			zap.Float64("error_rate", metrics.ErrorRate),
			zap.Float64("trend_score", trendScore),
		)
	}

	return useServerless, nil
}

func (r *RequestRouter) updateRouting(ctx context.Context) error {
	metrics, err := r.getMetrics(ctx)
	if err != nil {
		r.failureCount++
		r.logger.Error("Failed to get metrics", zap.Error(err))
		if r.failureCount >= 3 {
			return fmt.Errorf("consecutive metric collection failures: %v", err)
		}
		return nil
	}
	r.failureCount = 0

	useServerless, err := r.shouldUseServerless(metrics)
	if err != nil {
		return fmt.Errorf("decision making failed: %v", err)
	}

	// Get current service
	service, err := r.kubeClient.CoreV1().Services(r.config.Namespace).Get(
		ctx,
		r.config.WSGIService,
		metav1.GetOptions{},
	)
	if err != nil {
		return fmt.Errorf("failed to get service: %v", err)
	}

	// Check if update is needed
	currentBackend := service.Spec.Selector["app"]
	targetBackend := r.config.OpenFaaSService
	if !useServerless {
		targetBackend = r.config.WSGIService
	}

	if currentBackend == targetBackend {
		return nil
	}

	// Update service with retries
	for i := 0; i < 3; i++ {
		service.Spec.Selector["app"] = targetBackend
		_, err = r.kubeClient.CoreV1().Services(r.config.Namespace).Update(
			ctx,
			service,
			metav1.UpdateOptions{},
		)
		if err == nil {
			break
		}
		time.Sleep(time.Second * time.Duration(i+1))
	}

	if err != nil {
		return fmt.Errorf("failed to update service after retries: %v", err)
	}

	return nil
}

func (r *RequestRouter) Run(stopCh <-chan struct{}) {
	ticker := time.NewTicker(r.config.CheckInterval)
	defer ticker.Stop()
	defer r.logger.Sync()

	r.logger.Info("Starting RequestRouter controller",
		zap.String("namespace", r.config.Namespace),
		zap.String("wsgi_service", r.config.WSGIService),
		zap.String("openfaas_service", r.config.OpenFaaSService),
	)

	for {
		select {
		case <-ticker.C:
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			if err := r.updateRouting(ctx); err != nil {
				r.logger.Error("Failed to update routing", zap.Error(err))
			}
			cancel()
		case <-stopCh:
			r.logger.Info("Shutting down RequestRouter controller")
			return
		}
	}
}

// Helper function for absolute value
func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}
