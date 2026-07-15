-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE auth_token (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  auth_token_registry_id TEXT NOT NULL,
  -- ATTRIBUTES
  token_type TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  public_key TEXT NOT NULL,
  issued_by_actor_id TEXT NOT NULL,
  issued_at TEXT NOT NULL,
  label TEXT,
  scopes TEXT NOT NULL,
  context_environment_id TEXT,
  context_process_id TEXT,
  context_thread_id TEXT,
  expires_at TEXT,
  revoked_at TEXT,
  sha256 TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, auth_token_registry_id) REFERENCES auth_token_registry(branch_id, projection_hash, id)
);
