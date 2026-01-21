package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
	"github.com/rs/zerolog/log"
)

// JWTAuth validates JWT tokens and tenant claims
func JWTAuth(publicKey string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract Authorization header
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				log.Warn().Msg("Missing Authorization header")
				http.Error(w, "Missing Authorization header", http.StatusUnauthorized)
				return
			}

			// Check Bearer prefix
			if !strings.HasPrefix(authHeader, "Bearer ") {
				log.Warn().Msg("Invalid Authorization header format")
				http.Error(w, "Invalid Authorization header format", http.StatusUnauthorized)
				return
			}

			tokenString := strings.TrimPrefix(authHeader, "Bearer ")

			// For MVP development: accept any token if no public key configured
			if publicKey == "" {
				log.Warn().Msg("JWT validation disabled (no public key configured)")
				// In dev mode, extract tenant_id from context set by TenantValidator
				next.ServeHTTP(w, r)
				return
			}

			// Parse and validate JWT
			token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
				// Validate signing method
				if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
					return nil, jwt.ErrSignatureInvalid
				}
				// TODO: Load actual public key from file/env
				return []byte(publicKey), nil
			})

			if err != nil {
				log.Warn().Err(err).Msg("Invalid JWT token")
				http.Error(w, "Invalid token", http.StatusUnauthorized)
				return
			}

			if !token.Valid {
				log.Warn().Msg("Token not valid")
				http.Error(w, "Invalid token", http.StatusUnauthorized)
				return
			}

			// Extract claims
			claims, ok := token.Claims.(jwt.MapClaims)
			if !ok {
				log.Warn().Msg("Invalid token claims")
				http.Error(w, "Invalid token claims", http.StatusUnauthorized)
				return
			}

			// Validate tenant_id in JWT matches X-Tenant-ID header
			jwtTenantID, ok := claims["tenant_id"].(string)
			if !ok {
				log.Warn().Msg("Missing tenant_id in JWT claims")
				http.Error(w, "Missing tenant_id in token", http.StatusUnauthorized)
				return
			}

			headerTenantID := r.Context().Value("tenant_id").(string)
			if jwtTenantID != headerTenantID {
				log.Warn().
					Str("jwt_tenant_id", jwtTenantID).
					Str("header_tenant_id", headerTenantID).
					Msg("Tenant ID mismatch")
				http.Error(w, "Tenant ID mismatch", http.StatusForbidden)
				return
			}

			// Add user info to context if available
			if userID, ok := claims["sub"].(string); ok {
				ctx := context.WithValue(r.Context(), "user_id", userID)
				r = r.WithContext(ctx)
			}

			next.ServeHTTP(w, r)
		})
	}
}
