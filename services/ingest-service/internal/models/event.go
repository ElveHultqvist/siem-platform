package models

// Event represents a security event in the canonical schema
type Event struct {
	TenantID   string                 `json:"tenant_id"`
	EventID    string                 `json:"event_id"`
	Timestamp  string                 `json:"timestamp"`
	Source     Source                 `json:"source"`
	Category   string                 `json:"category"`
	Severity   int                    `json:"severity"`
	Actor      *Actor                 `json:"actor,omitempty"`
	Target     *Target                `json:"target,omitempty"`
	Action     string                 `json:"action,omitempty"`
	Outcome    string                 `json:"outcome,omitempty"`
	Attributes map[string]interface{} `json:"attributes,omitempty"`
	RawRef     string                 `json:"raw_ref,omitempty"`
	Tags       []string               `json:"tags,omitempty"`
}

// Source contains event source information
type Source struct {
	System      string `json:"system"`
	Integration string `json:"integration,omitempty"`
	Host        string `json:"host,omitempty"`
}

// Actor represents the entity that performed the action
type Actor struct {
	Type  string `json:"type"` // user, service, device, unknown
	ID    string `json:"id"`
	Name  string `json:"name,omitempty"`
	Email string `json:"email,omitempty"`
}

// Target represents the entity that was acted upon
type Target struct {
	Type string `json:"type"` // asset, workload, service, data, unknown
	ID   string `json:"id"`
	Name string `json:"name,omitempty"`
}
