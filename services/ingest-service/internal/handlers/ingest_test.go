package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/siem-platform/ingest-service/internal/publisher"
)

func TestIngestEvents(t *testing.T) {
	mockPub := publisher.NewMockPublisher()
	handler := NewIngestHandler(mockPub)

	tests := []struct {
		name           string
		method         string
		tenantID       string
		body           map[string]interface{}
		expectedStatus int
	}{
		{
			name:     "Valid event",
			method:   "POST",
			tenantID: "acme-corp",
			body: map[string]interface{}{
				"category": "auth",
				"severity": 5,
				"actor": map[string]string{
					"id":   "user123",
					"name": "John Doe",
				},
			},
			expectedStatus: http.StatusAccepted,
		},
		{
			name:           "Missing category",
			method:         "POST",
			tenantID:       "acme-corp",
			body:           map[string]interface{}{"severity": 5},
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:           "Invalid method",
			method:         "GET",
			tenantID:       "acme-corp",
			body:           map[string]interface{}{"category": "auth"},
			expectedStatus: http.StatusMethodNotAllowed,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			bodyBytes, _ := json.Marshal(tt.body)
			req := httptest.NewRequest(tt.method, "/v1/ingest/events", bytes.NewReader(bodyBytes))
			req.Header.Set("Content-Type", "application/json")

			// Add tenant ID to context (normally done by middleware)
			if tt.tenantID != "" {
				ctx := context.WithValue(req.Context(), "tenant_id", tt.tenantID)
				req = req.WithContext(ctx)
			}

			rr := httptest.NewRecorder()
			handler.IngestEvents(rr, req)

			if rr.Code != tt.expectedStatus {
				t.Errorf("Expected status %d, got %d", tt.expectedStatus, rr.Code)
			}

			// Check successful event was published
			if tt.expectedStatus == http.StatusAccepted {
				published := mockPub.GetPublished("raw.events." + tt.tenantID)
				if len(published) == 0 {
					t.Error("Expected event to be published")
				}

				// Verify response contains event_id
				var response map[string]string
				json.NewDecoder(rr.Body).Decode(&response)
				if response["event_id"] == "" {
					t.Error("Expected event_id in response")
				}
			}
		})
	}
}
