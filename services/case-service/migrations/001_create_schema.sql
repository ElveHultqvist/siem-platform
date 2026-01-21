-- Database schema for case management
-- All tables include tenant_id for row-level tenant isolation

-- Cases table
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(63) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity INT NOT NULL CHECK (severity >= 0 AND severity <= 10),
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    assigned_to VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    modified_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_status CHECK (status IN ('open', 'investigating', 'contained', 'resolved', 'closed', 'false_positive'))
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_cases_tenant_id ON cases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_cases_severity ON cases(tenant_id, severity DESC);
CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(tenant_id, created_at DESC);

-- Case alerts link table (many-to-many between cases and alerts)
CREATE TABLE IF NOT EXISTS case_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(63) NOT NULL,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    alert_id VARCHAR(255) NOT NULL,
    linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    linked_by VARCHAR(255) NOT NULL,
    UNIQUE(tenant_id, case_id, alert_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_case_alerts_tenant_case ON case_alerts(tenant_id, case_id);
CREATE INDEX IF NOT EXISTS idx_case_alerts_alert ON case_alerts(tenant_id, alert_id);

-- Case comments table
CREATE TABLE IF NOT EXISTS case_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(63) NOT NULL,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_case_comments_case ON case_comments(tenant_id, case_id, created_at DESC);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for cases table
DROP TRIGGER IF EXISTS update_cases_updated_at ON cases;
CREATE TRIGGER update_cases_updated_at
    BEFORE UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) - to be configured per tenant
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_comments ENABLE ROW LEVEL SECURITY;

-- Note: RLS policies would be created per tenant in production
-- For MVP, application-level tenant filtering is sufficient
