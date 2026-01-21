package handlers

import (
	"encoding/json"
	"io"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/rs/zerolog/log"
	"github.com/siem-platform/ingest-service/internal/models"
	"github.com/siem-platform/ingest-service/internal/publisher"
)

// IngestHandler handles event ingestion
type IngestHandler struct {
	publisher publisher.Publisher
}

// NewIngestHandler creates a new ingest handler
func NewIngestHandler(pub publisher.Publisher) *IngestHandler {
	return &IngestHandler{
		publisher: pub,
	}
}

// IngestEvents handles POST /v1/ingest/events
func (h *IngestHandler) IngestEvents(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get tenant ID from context (set by middleware)
	tenantID, ok := r.Context().Value("tenant_id").(string)
	if !ok || tenantID == "" {
		log.Error().Msg("Tenant ID not found in context")
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Read and parse request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		log.Error().Err(err).Msg("Failed to read request body")
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Parse event
	var event models.Event
	if err := json.Unmarshal(body, &event); err != nil {
		log.Error().Err(err).Msg("Failed to parse event")
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if event.Category == "" {
		http.Error(w, "Missing required field: category", http.StatusBadRequest)
		return
	}

	// Enrich event with metadata
	event.TenantID = tenantID
	event.EventID = uuid.New().String()
	event.Timestamp = time.Now().UTC().Format(time.RFC3339)
	event.Source.Host = r.RemoteAddr

	// Publish to NATS
	topic := "raw.events." + tenantID
	if err := h.publisher.Publish(topic, &event); err != nil {
		log.Error().
			Err(err).
			Str("tenant_id", tenantID).
			Str("topic", topic).
			Msg("Failed to publish event")
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	log.Info().
		Str("tenant_id", tenantID).
		Str("event_id", event.EventID).
		Str("category", event.Category).
		Int("severity", event.Severity).
		Msg("Event ingested")

	// Return success response
	response := map[string]string{
		"event_id": event.EventID,
		"status":   "accepted",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(response)
}
