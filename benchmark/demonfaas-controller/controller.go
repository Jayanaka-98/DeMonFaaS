package main

import (
	"context" // Manages lifecycle of API requests
	"fmt" // string formatting
	"net/http" // standard http library
	"k8s.io/apimachinery/pkg/runtime" // represents kubernetes object model schema
	ctrl "sigs.k8s.io/controller-runtime" // go framework for building controllers
	"sigs.k8s.io/controller-runtime/pkg/client" // go framework for building controllers
)

type ApiTransformationReconciler struct {
	client.Client // lets controller interact with kubernetes resources
	Scheme *runtime.Scheme // manages object types - enables kubernetes to recognize and handle custom resources
}

// Implemented inside ApiTransformationReconciler - like Scope Operator :: in C++
func (r *ApiTransformationReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
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
	// Set up controller manager which manages the lifecycle of the controller.
	// Connect Manager to kubernetes cluster.
	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: runtime.NewScheme(),
	})
	if err != nil {
		panic(fmt.Sprintf("unable to start manager: %v", err))
	}

	// Add controller to manager.
	// Registers the reconciler with the manager.
	if err := (&ApiTransformationReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		panic(fmt.Sprintf("unable to create controller: %v", err))
	}

	// Start manager
	// Starts the controller and starts reconciling events
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		panic(fmt.Sprintf("unable to run manager: %v", err))
	}
}
