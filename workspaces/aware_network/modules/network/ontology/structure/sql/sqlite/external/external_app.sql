-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE external_app (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- ATTRIBUTES
  error_count INTEGER,
  last_error TEXT,
  last_error_at TEXT,
  last_sync_at TEXT,
  next_sync_at TEXT,
  oauth_access_token TEXT,
  oauth_expires_at TEXT,
  oauth_refresh_token TEXT,
  oauth_scope TEXT NOT NULL,
  provider TEXT NOT NULL,
  provider_email TEXT,
  provider_metadata TEXT,
  provider_user_id TEXT,
  rate_limit_remaining INTEGER,
  rate_limit_reset_at TEXT,
  status TEXT NOT NULL,
  webhook_expires_at TEXT,
  webhook_id TEXT,
  webhook_secret TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, provider)
);
