-- Career Intelligence Navigator — Database Schema
-- PostgreSQL 15+
-- Run: psql $DATABASE_URL -f schema.sql

-- ─────────────────────────────────────────
-- EXTENSIONS
-- ─────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_id            TEXT UNIQUE NOT NULL,           -- Clerk user ID
    email               TEXT NOT NULL,
    full_name           TEXT,
    plan                TEXT NOT NULL DEFAULT 'free',   -- free | pro | teams
    stripe_customer_id  TEXT,
    stripe_subscription_id TEXT,
    
    -- Usage tracking
    ats_analyses_used       INT NOT NULL DEFAULT 0,
    career_analyses_used    INT NOT NULL DEFAULT 0,
    ats_analyses_limit      INT NOT NULL DEFAULT 2,     -- free: 2, pro: -1 (unlimited)
    career_analyses_limit   INT NOT NULL DEFAULT 1,     -- free: 1, pro: -1
    usage_reset_at          TIMESTAMP,                  -- when limits reset
    
    -- Preferences
    target_role         TEXT,
    industry            TEXT,
    digest_enabled      BOOLEAN DEFAULT FALSE,
    
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_clerk_id ON users(clerk_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_plan ON users(plan);

-- ─────────────────────────────────────────
-- ANALYSES
-- ─────────────────────────────────────────
CREATE TABLE analyses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            TEXT NOT NULL,          -- 'ats' | 'career_gap' | 'full'
    
    -- Raw inputs (stored for reprocessing and debugging)
    resume_text     TEXT,
    job_description TEXT,                   -- ATS only
    target_role     TEXT,                   -- Career only
    
    -- Full structured result
    result          JSONB NOT NULL,
    
    -- Cost tracking
    tokens_used     INT,
    api_cost_usd    NUMERIC(10, 6),
    
    -- Status
    status          TEXT NOT NULL DEFAULT 'completed',  -- completed | failed | processing
    error_message   TEXT,
    
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_type ON analyses(type);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX idx_analyses_result ON analyses USING GIN (result);  -- fast JSONB queries

-- ─────────────────────────────────────────
-- MARKET DIGESTS (weekly email records)
-- ─────────────────────────────────────────
CREATE TABLE market_digests (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    digest      JSONB NOT NULL,             -- full digest content
    email_sent  BOOLEAN DEFAULT FALSE,
    sent_at     TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_digests_user_id ON market_digests(user_id);
CREATE INDEX idx_digests_sent_at ON market_digests(sent_at DESC);

-- ─────────────────────────────────────────
-- API COST TRACKING
-- ─────────────────────────────────────────
CREATE TABLE api_costs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES analyses(id),
    user_id     UUID REFERENCES users(id),
    provider    TEXT NOT NULL,              -- 'anthropic' | 'perplexity'
    model       TEXT NOT NULL,
    tokens_in   INT,
    tokens_out  INT,
    cost_usd    NUMERIC(10, 6),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_costs_user_id ON api_costs(user_id);
CREATE INDEX idx_costs_created_at ON api_costs(created_at DESC);

-- ─────────────────────────────────────────
-- TRIGGERS
-- ─────────────────────────────────────────

-- Auto-update updated_at on users
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-increment usage count on new analysis
CREATE OR REPLACE FUNCTION increment_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.type = 'ats' THEN
        UPDATE users SET ats_analyses_used = ats_analyses_used + 1
        WHERE id = NEW.user_id;
    ELSIF NEW.type = 'career_gap' THEN
        UPDATE users SET career_analyses_used = career_analyses_used + 1
        WHERE id = NEW.user_id;
    ELSIF NEW.type = 'full' THEN
        UPDATE users 
        SET ats_analyses_used = ats_analyses_used + 1,
            career_analyses_used = career_analyses_used + 1
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER analyses_increment_usage
    AFTER INSERT ON analyses
    FOR EACH ROW EXECUTE FUNCTION increment_usage_count();

-- ─────────────────────────────────────────
-- VIEWS
-- ─────────────────────────────────────────

-- Daily revenue + usage summary (for dashboard)
CREATE VIEW daily_summary AS
SELECT 
    DATE(a.created_at) as date,
    COUNT(*) as total_analyses,
    COUNT(CASE WHEN a.type = 'ats' THEN 1 END) as ats_analyses,
    COUNT(CASE WHEN a.type = 'career_gap' THEN 1 END) as career_analyses,
    SUM(a.api_cost_usd) as total_api_cost,
    COUNT(DISTINCT a.user_id) as unique_users
FROM analyses a
GROUP BY DATE(a.created_at)
ORDER BY date DESC;

-- User plan distribution
CREATE VIEW plan_distribution AS
SELECT 
    plan,
    COUNT(*) as user_count,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as new_last_30d
FROM users
GROUP BY plan;
