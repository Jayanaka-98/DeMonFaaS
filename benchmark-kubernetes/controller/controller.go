package main

import (
	"context" // Manages lifecycle of API requests
	"encoding/json"
	"fmt" // string formatting
	"io/ioutil"
	"net/http" // standard http library
	"net/url"

	"k8s.io/apimachinery/pkg/runtime"           // represents kubernetes object model schema
	ctrl "sigs.k8s.io/controller-runtime"       // go framework for building controllers
	"sigs.k8s.io/controller-runtime/pkg/client" // go framework for building controllers
	"sigs.k8s.io/controller-runtime/pkg/log"    // logger
)

var logger = log.Log.WithName("demonfaas-controller")

// Define the ApiTransformation resource
type ApiTransformation struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec              ApiTransformationSpec `json:"spec,omitempty"`
}

type ApiTransformationSpec struct {
	SourceApi string `json:"sourceApi"`
	TargetApi string `json:"targetApi"`
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
	// Define Prometheus query URL (modify with your Prometheus service)
	prometheusURL := "http://prometheus-k8s.default.svc.cluster.local:9090/api/v1/query"

	// Encode the query parameter
	params := url.Values{}
	params.Add("query", query)

	// Make the HTTP request to Prometheus
	resp, err := http.Get(prometheusURL + "?" + params.Encode())
	if err != nil {
		return nil, fmt.Errorf("error querying Prometheus: %v", err)
	}
	defer resp.Body.Close()

	// Read the response body
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response body: %v", err)
	}

	// Check if the request was successful (status code 200)
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("Prometheus query failed with status: %d", resp.StatusCode)
	}

	// Parse the JSON response into the PrometheusResponse struct
	var prometheusResponse PrometheusResponse
	err = json.Unmarshal(body, &prometheusResponse)
	if err != nil {
		return nil, fmt.Errorf("error unmarshaling JSON response: %v", err)
	}

	// Check if we received any results
	if len(prometheusResponse.Data.Result) == 0 {
		return nil, fmt.Errorf("no results found for the query")
	}

	return &prometheusResponse, nil
}

// Implemented inside ApiTransformationReconciler - like Scope Operator :: in C++
func (r *ApiTransformationReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger.Info("Handling the request") // Example of structured
	// Fetch the ApiTransformation resource
	// ApiTransformation resource is used to define rules for transforming API calls. It specifies...
	// - source API endpoint (where it came from)
	// - target API endpoint (where it is going)
	// - transformation logic (details on how to modify the request)
	var transformation ApiTransformation
	if err := r.Get(ctx, req.NamespacedName, &transformation); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	// Check if target API has changed
	oldTargetApi, exists := r.getCachedTargetAPI(req.NamespacedName)
	if exists && oldTargetApi != transformation.Spec.TargetApi {
		// Handle logic for target API change, e.g., log the change or reset resources
		fmt.Printf("Target API changed: %s -> %s\n", oldTargetApi, transformation.Spec.TargetApi)
		r.updateCachedTargetAPI(req.NamespacedName, transformation.Spec.TargetApi)
	}

	// Directly forward the request from source to target
	err := forward(transformation.Spec.SourceApi, transformation.Spec.TargetApi)
	if err != nil {
		return ctrl.Result{}, err
	}

	return ctrl.Result{}, nil
}

func forward(sourceApi, targetApi string) error {
	// Fetch from source API
	// - Calls the source API
	// - response body is used as an input to the next step
	resp, err := http.Get(sourceApi)
	if err != nil {
		return fmt.Errorf("error calling source API: %v", err)
	}
	defer resp.Body.Close()

	// Forward to target API
	// - creates post request with the source API's response body
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

func main() {
	logger.Info("Starting the controller") // Example of structured
	scheme := runtime.NewScheme()
	utilruntime.Must(AddToScheme(scheme)) // Register the ApiTransformation resource scheme

	// Set up controller manager which manages the lifecycle of the controller.
	// Connect Manager to kubernetes cluster.
	logger.Info("Starting the controller 2") // Example of structured
	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
	})
	if err != nil {
		panic(fmt.Sprintf("unable to start manager: %v", err))
	}

	// Add controller to manager.
	// Registers the reconciler with the manager.
	logger.Info("Starting the controller 3") // Example of structured
	if err := (&ApiTransformationReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		panic(fmt.Sprintf("unable to create controller: %v", err))
	}

	// Start manager
	// Starts the controller and starts reconciling events
	logger.Info("Starting the controller 4") // Example of structured
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		panic(fmt.Sprintf("unable to run manager: %v", err))
	}
}

// AddToScheme registers ApiTransformation with the runtime scheme
func AddToScheme(scheme *runtime.Scheme) error {
	scheme.AddKnownTypes(
		runtime.NewSchemeBuilder(
			func(s *runtime.Scheme) error {
				s.AddKnownTypeWithName(ApiTransformationGVK(), &ApiTransformation{})
				return nil
			},
		).Build(),
	)
	metav1.AddToGroupVersion(scheme, ApiTransformationGVK().GroupVersion())
	return nil
}

// ApiTransformationGVK returns the GroupVersionKind for ApiTransformation
func ApiTransformationGVK() metav1.GroupVersionKind {
	return metav1.GroupVersionKind{
		Group:   "myapi.example.com",
		Version: "v1",
		Kind:    "ApiTransformation",
	}
}
