-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE auth_token (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  auth_token_registry_id UUID NOT NULL,
  -- ATTRIBUTES
  token_type auth_token_type NOT NULL,
  actor_id UUID NOT NULL,
  public_key TEXT NOT NULL,
  issued_by_actor_id UUID NOT NULL,
  issued_at TIMESTAMPTZ NOT NULL,
  label TEXT,
  scopes TEXT[] NOT NULL,
  context_environment_id UUID,
  context_process_id UUID,
  context_thread_id UUID,
  expires_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  sha256 TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, auth_token_registry_id) REFERENCES auth_token_registry(branch_id, projection_hash, id)
);
