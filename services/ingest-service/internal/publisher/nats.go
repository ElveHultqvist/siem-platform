package publisher

import (
	"encoding/json"

	"github.com/nats-io/nats.go"
	"github.com/rs/zerolog/log"
	"github.com/siem-platform/ingest-service/internal/models"
)

// Publisher defines the interface for event publishing
type Publisher interface {
	Publish(topic string, event *models.Event) error
	Close()
}

// NATSPublisher publishes events to NATS JetStream
type NATSPublisher struct {
	conn *nats.Conn
	js   nats.JetStreamContext
}

// NewNATSPublisher creates a new NATS publisher
func NewNATSPublisher(url string) (*NATSPublisher, error) {
	// Connect to NATS
	conn, err := nats.Connect(url,
		nats.MaxReconnects(-1),
		nats.ReconnectWait(2),
		nats.DisconnectErrHandler(func(nc *nats.Conn, err error) {
			log.Warn().Err(err).Msg("NATS disconnected")
		}),
		nats.ReconnectHandler(func(nc *nats.Conn) {
			log.Info().Str("url", nc.ConnectedUrl()).Msg("NATS reconnected")
		}),
	)
	if err != nil {
		return nil, err
	}

	// Create JetStream context
	js, err := conn.JetStream()
	if err != nil {
		conn.Close()
		return nil, err
	}

	return &NATSPublisher{
		conn: conn,
		js:   js,
	}, nil
}

// Publish publishes an event to a NATS topic
func (p *NATSPublisher) Publish(topic string, event *models.Event) error {
	// Serialize event to JSON
	data, err := json.Marshal(event)
	if err != nil {
		return err
	}

	// Publish to JetStream
	_, err = p.js.Publish(topic, data)
	if err != nil {
		return err
	}

	log.Debug().
		Str("topic", topic).
		Str("event_id", event.EventID).
		Int("size_bytes", len(data)).
		Msg("Event published to NATS")

	return nil
}

// Close closes the NATS connection
func (p *NATSPublisher) Close() {
	if p.conn != nil {
		p.conn.Close()
		log.Info().Msg("NATS connection closed")
	}
}
