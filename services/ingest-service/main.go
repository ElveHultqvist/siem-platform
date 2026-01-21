package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/siem-platform/ingest-service/internal/config"
	"github.com/siem-platform/ingest-service/internal/handlers"
	"github.com/siem-platform/ingest-service/internal/middleware"
	"github.com/siem-platform/ingest-service/internal/publisher"
)

func main() {
	// Initialize structured logging
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})

	// Load configuration
	cfg := config.Load()

	// Set log level
	level, err := zerolog.ParseLevel(cfg.LogLevel)
	if err != nil {
		level = zerolog.InfoLevel
	}
	zerolog.SetGlobalLevel(level)

	log.Info().
		Str("service", "ingest-service").
		Str("version", "0.1.0").
		Str("port", cfg.Port).
		Msg("Starting ingest service")

	// Initialize NATS publisher
	pub, err := publisher.NewNATSPublisher(cfg.NATSURL)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to connect to NATS")
	}
	defer pub.Close()

	log.Info().Str("nats_url", cfg.NATSURL).Msg("Connected to NATS")

	// Create HTTP handler
	handler := handlers.NewIngestHandler(pub)

	// Setup middleware chain
	mux := http.NewServeMux()

	// Health endpoints (no auth required)
	mux.HandleFunc("/health", handlers.HealthHandler)
	mux.HandleFunc("/ready", handlers.ReadyHandler)
	mux.HandleFunc("/metrics", handlers.MetricsHandler)

	// Ingest endpoints (with auth)
	authMux := http.NewServeMux()
	authMux.HandleFunc("/v1/ingest/events", handler.IngestEvents)

	// Apply middleware: logging -> tenant validation -> JWT auth
	chain := middleware.Chain(
		authMux,
		middleware.RequestLogger,
		middleware.TenantValidator(cfg.JWTPublicKey),
		middleware.JWTAuth(cfg.JWTPublicKey),
	)

	mux.Handle("/v1/", chain)

	// Create HTTP server
	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      mux,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Info().Str("addr", srv.Addr).Msg("HTTP server listening")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("HTTP server failed")
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info().Msg("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal().Err(err).Msg("Server forced to shutdown")
	}

	log.Info().Msg("Server exited")
}
