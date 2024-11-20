package main

import (
	"context" // Manages lifecycle of API requests
	"encoding/json"
	"fmt" // string formatting
	"io/ioutil"
	"net/http" // standard http library
	"net/url"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"           // represents kubernetes object model schema
	ctrl "sigs.k8s.io/controller-runtime"       // go framework for building controllers
	"sigs.k8s.io/controller-runtime/pkg/client" // go framework for building controllers
	"sigs.k8s.io/controller-runtime/pkg/log"    // logger
)

var logger = log.Log.WithName("demonfaas-controller")

// Define the ApiTransformation resource

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
type ApiTransformation struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec              ApiTransformationSpec   `json:"spec,omitempty"`
	Status            ApiTransformationStatus `json:"status,omitempty"`
}

type ApiTransformationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ApiTransformation `json:"items"`
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *ApiTransformationStatus) DeepCopyInto(out *ApiTransformationStatus) {
	*out = *in
	// If there are any nested fields that need deep copy (like time), add them here
	in.LastUpdateTime.DeepCopyInto(&out.LastUpdateTime)
}

type ApiTransformationSpec struct {
	SourceApi string `json:"sourceApi"`
	TargetApi string `json:"targetApi"`
}

type ApiTransformationStatus struct {
	LastUpdateTime metav1.Time `json:"lastUpdateTime,omitempty"` // Example status field
}

type ApiTransformationReconciler struct {
	client.Client                 // lets controller interact with kubernetes resources
	Scheme        *runtime.Scheme // manages object types - enables kubernetes to recognize and handle custom resources
}

// Structure for the response from Prometheus query
type PrometheusResponse struct {
	Status string `json:"status"`
	Data   struct {
		Result []struct {
			Metric map[string]string `json:"metric"`
			Value  []interface{}     `json:"value"`
		} `json:"result"`
	} `json:"data"`
}

// Function to query Prometheus API
func queryPrometheus(query string) (*PrometheusResponse, error) {
	prometheusURL := "http://prometheus-k8s.default.svc.cluster.local:9090/api/v1/query"
	params := url.Values{}
	params.Add("query", query)

	resp, err := http.Get(prometheusURL + "?" + params.Encode())
	if err != nil {
		return nil, fmt.Errorf("error querying Prometheus: %v", err)
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response body: %v", err)
	}

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("Prometheus query failed with status: %d", resp.StatusCode)
	}

	var prometheusResponse PrometheusResponse
	err = json.Unmarshal(body, &prometheusResponse)
	if err != nil {
		return nil, fmt.Errorf("error unmarshaling JSON response: %v", err)
	}

	if len(prometheusResponse.Data.Result) == 0 {
		return nil, fmt.Errorf("no results found for the query")
	}

	return &prometheusResponse, nil
}

// func decideTargetApi(prometheusResponse *PrometheusResponse) string {
// 	// Example: Choose the API with the highest availability or lowest latency
// 	bestTargetApi := ""
// 	bestValue := -1.0 // Replace with a suitable default value for your metric

// 	for _, result := range prometheusResponse.Data.Result {
// 		targetApi := result.Metric["targetApi"] // Assumes your metric labels include "targetApi"
// 		value, ok := result.Value[1].(string)
// 		if !ok {
// 			continue
// 		}

// 		metricValue, err := strconv.ParseFloat(value, 64)
// 		if err != nil {
// 			continue
// 		}

// 		if metricValue > bestValue { // Adjust this comparison based on your metric
// 			bestValue = metricValue
// 			bestTargetApi = targetApi
// 		}
// 	}

// 	return bestTargetApi
// }

// Implemented inside ApiTransformationReconciler - like Scope Operator :: in C++
func (r *ApiTransformationReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger.Info("Reconciling ApiTransformation")

	var transformation ApiTransformation
	if err := r.Get(ctx, req.NamespacedName, &transformation); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	// Example Prometheus Query Logic
	prometheusQuery := `rate(http_requests_total[5m])`
	prometheusResponse, err := queryPrometheus(prometheusQuery)
	if err != nil {
		logger.Error(err, "Failed to query Prometheus")
		return ctrl.Result{}, err
	}

	// Dynamically forward API requests based on Prometheus metrics
	for _, result := range prometheusResponse.Data.Result {
		logger.Info("Prometheus Metric", "metric", result.Metric, "value", result.Value)

		err := forward(transformation.Spec.SourceApi, transformation.Spec.TargetApi)
		if err != nil {
			logger.Error(err, "Failed to forward API request")
			return ctrl.Result{}, err
		}
	}

	return ctrl.Result{}, nil
}

func forward(sourceApi, targetApi string) error {
	resp, err := http.Get(sourceApi)
	if err != nil {
		return fmt.Errorf("error calling source API: %v", err)
	}
	defer resp.Body.Close()

	req, err := http.NewRequest("POST", targetApi, resp.Body)
	if err != nil {
		return fmt.Errorf("error creating target API request: %v", err)
	}
	client := &http.Client{}
	_, err = client.Do(req)
	if err != nil {
		return fmt.Errorf("error sending to target API: %v", err)
	}
	return nil
}

func (r *ApiTransformationReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&ApiTransformation{}).
		Complete(r)
}

func main() {
	logger.Info("Starting the controller")
	scheme := runtime.NewScheme()

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
	})
	if err != nil {
		panic(fmt.Sprintf("unable to start manager: %v", err))
	}

	if err := (&ApiTransformationReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		panic(fmt.Sprintf("unable to create controller: %v", err))
	}

	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		panic(fmt.Sprintf("unable to run manager: %v", err))
	}
}

// // ApiTransformationGVK returns the GroupVersionKind for ApiTransformation
// func ApiTransformationGVK() metav1.GroupVersionKind {
// 	return metav1.GroupVersionKind{
// 		Group:   "myapi.example.com",
// 		Version: "v1",
// 		Kind:    "ApiTransformation",
// 	}
// }

// // AddToScheme registers ApiTransformation with the runtime scheme
// func AddToScheme(scheme *runtime.Scheme) error {
// 	scheme.AddKnownTypes(
// 		runtime.NewSchemeBuilder(
// 			func(s *runtime.Scheme) error {
// 				s.AddKnownTypeWithName(ApiTransformationGVK(), &ApiTransformation{})
// 				return nil
// 			},
// 		).Build(),
// 	)
// 	metav1.AddToGroupVersion(scheme, ApiTransformationGVK().GroupVersion())
// 	return nil
// }
