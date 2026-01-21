package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestTenantValidator(t *testing.T) {
	tests := []struct {
		name           string
		tenantHeader   string
		expectedStatus int
	}{
		{
			name:           "Valid tenant ID",
			tenantHeader:   "acme-corp",
			expectedStatus: http.StatusOK,
		},
		{
			name:           "Missing tenant header",
			tenantHeader:   "",
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:           "Tenant ID too short",
			tenantHeader:   "ab",
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:           "Tenant ID too long",
			tenantHeader:   "this-is-a-very-long-tenant-id-that-exceeds-sixty-three-characters-limit",
			expectedStatus: http.StatusBadRequest,
		},
	}

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check tenant ID was added to context
		tenantID := r.Context().Value("tenant_id")
		if tenantID == nil {
			t.Error("Expected tenant_id in context")
		}
		w.WriteHeader(http.StatusOK)
	})

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/test", nil)
			if tt.tenantHeader != "" {
				req.Header.Set("X-Tenant-ID", tt.tenantHeader)
			}

			rr := httptest.NewRecorder()
			middleware := TenantValidator("")(handler)
			middleware.ServeHTTP(rr, req)

			if rr.Code != tt.expectedStatus {
				t.Errorf("Expected status %d, got %d", tt.expectedStatus, rr.Code)
			}
		})
	}
}
