package middleware

import (
	"context"
	"net/http"

	"github.com/rs/zerolog/log"
)

// TenantValidator validates tenant context
func TenantValidator(jwtPublicKey string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract X-Tenant-ID header
			tenantID := r.Header.Get("X-Tenant-ID")
			if tenantID == "" {
				log.Warn().Msg("Missing X-Tenant-ID header")
				http.Error(w, "Missing X-Tenant-ID header", http.StatusBadRequest)
				return
			}

			// Validate tenant ID format (basic validation)
			if len(tenantID) < 3 || len(tenantID) > 63 {
				log.Warn().Str("tenant_id", tenantID).Msg("Invalid tenant ID format")
				http.Error(w, "Invalid tenant ID format", http.StatusBadRequest)
				return
			}

			// TODO: Verify tenant exists in tenant service
			// For MVP, we just accept any valid-looking tenant ID

			// Add tenant ID to context
			ctx := context.WithValue(r.Context(), "tenant_id", tenantID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
