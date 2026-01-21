package config

import (
	"os"
)

// Config holds the application configuration
type Config struct {
	Port         string
	NATSURL      string
	JWTPublicKey string
	LogLevel     string
}

// Load reads configuration from environment variables with defaults
func Load() *Config {
	return &Config{
		Port:         getEnv("PORT", "8080"),
		NATSURL:      getEnv("NATS_URL", "nats://nats:4222"),
		JWTPublicKey: getEnv("JWT_PUBLIC_KEY", ""),
		LogLevel:     getEnv("LOG_LEVEL", "info"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
