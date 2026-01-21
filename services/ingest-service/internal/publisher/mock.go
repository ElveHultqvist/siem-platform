package publisher

import (
	"testing"

	"github.com/siem-platform/ingest-service/internal/models"
)

// MockPublisher is a mock implementation for testing
type MockPublisher struct {
	published map[string][]*models.Event
}

func NewMockPublisher() *MockPublisher {
	return &MockPublisher{
		published: make(map[string][]*models.Event),
	}
}

func (m *MockPublisher) Publish(topic string, event *models.Event) error {
	m.published[topic] = append(m.published[topic], event)
	return nil
}

func (m *MockPublisher) Close() {
	// No-op for mock
}

func (m *MockPublisher) GetPublished(topic string) []*models.Event {
	return m.published[topic]
}

func TestMockPublisher(t *testing.T) {
	pub := NewMockPublisher()

	event := &models.Event{
		TenantID: "test-tenant",
		EventID:  "123",
		Category: "auth",
		Severity: 5,
	}

	err := pub.Publish("raw.events.test-tenant", event)
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	published := pub.GetPublished("raw.events.test-tenant")
	if len(published) != 1 {
		t.Errorf("Expected 1 published event, got %d", len(published))
	}

	if published[0].EventID != "123" {
		t.Errorf("Expected event ID 123, got %s", published[0].EventID)
	}
}
