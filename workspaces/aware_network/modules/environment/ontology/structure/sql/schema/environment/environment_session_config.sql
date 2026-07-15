-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_session_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_config_id UUID NOT NULL,
  identity_session_config_id UUID NOT NULL,
  default_profile_config_id UUID,
  default_process_config_id UUID,
  default_thread_config_id UUID,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  title TEXT,
  description TEXT,
  purpose TEXT,
  status TEXT NOT NULL,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_config_id, key)
);
