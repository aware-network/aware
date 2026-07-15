-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_session_attention_session (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_session_id UUID NOT NULL,
  attention_session_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  title TEXT,
  status TEXT NOT NULL,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_session_id, attention_session_id)
);
