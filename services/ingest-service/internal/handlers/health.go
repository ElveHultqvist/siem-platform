package handlers

import (
	"encoding/json"
	"net/http"
)

// HealthHandler returns 200 OK if service is alive
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

// ReadyHandler returns 200 OK if service is ready to accept traffic
func ReadyHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Add checks for NATS connection, etc.
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
}

// MetricsHandler returns Prometheus metrics (stub for now)
func MetricsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	// TODO: Implement Prometheus metrics
	w.Write([]byte("# No metrics yet\n"))
}
