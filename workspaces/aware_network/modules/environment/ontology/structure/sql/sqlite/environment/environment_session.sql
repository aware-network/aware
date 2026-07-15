-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_session (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_id TEXT NOT NULL,
  session_config_id TEXT,
  identity_session_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  title TEXT,
  description TEXT,
  purpose TEXT,
  status TEXT NOT NULL,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_id, identity_session_id)
);
