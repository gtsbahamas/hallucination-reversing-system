-- LUCID API Database Schema
-- Run against Supabase (Postgres) instance

-- Drop existing tables if they exist (clean slate for v1 API)
DROP VIEW IF EXISTS monthly_usage CASCADE;
DROP TABLE IF EXISTS usage_logs CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS tiers CASCADE;

-- Tiers table
CREATE TABLE tiers (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  name TEXT UNIQUE NOT NULL,
  forward_monthly_limit INTEGER,  -- NULL = unlimited
  reverse_monthly_limit INTEGER,  -- NULL = unlimited
  requests_per_minute INTEGER NOT NULL DEFAULT 5,
  forward_price_cents INTEGER NOT NULL DEFAULT 0,
  reverse_price_cents INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed tier data
INSERT INTO tiers (name, forward_monthly_limit, reverse_monthly_limit, requests_per_minute, forward_price_cents, reverse_price_cents) VALUES
  ('free', 50, 20, 5, 0, 0),
  ('developer', NULL, NULL, 20, 5, 10),
  ('startup', NULL, NULL, 60, 3, 8),
  ('platform', NULL, NULL, 200, 1, 5);

-- API Keys table
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key_hash TEXT UNIQUE NOT NULL,
  key_prefix TEXT NOT NULL,
  name TEXT NOT NULL,
  tier_id TEXT NOT NULL REFERENCES tiers(id),
  email TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_email ON api_keys(email);

-- Usage logs table
CREATE TABLE usage_logs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  api_key_id UUID REFERENCES api_keys(id),
  endpoint TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  duration_ms INTEGER NOT NULL DEFAULT 0,
  pipeline_calls INTEGER NOT NULL DEFAULT 0,
  request_id TEXT NOT NULL,
  error_code TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usage_logs_key_date ON usage_logs(api_key_id, created_at);
CREATE INDEX idx_usage_logs_request ON usage_logs(request_id);

-- Monthly usage view
CREATE OR REPLACE VIEW monthly_usage AS
SELECT
  api_key_id,
  date_trunc('month', created_at) AS month,
  endpoint,
  COUNT(*) AS request_count,
  SUM(input_tokens) AS total_input_tokens,
  SUM(output_tokens) AS total_output_tokens,
  AVG(duration_ms)::integer AS avg_duration_ms
FROM usage_logs
WHERE status_code < 400
GROUP BY api_key_id, date_trunc('month', created_at), endpoint;
