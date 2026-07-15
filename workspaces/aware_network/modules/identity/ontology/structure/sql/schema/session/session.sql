-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  session_config_id UUID NOT NULL,
  parent_session_id UUID,
  created_by_actor_id UUID,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  parent_session_scope_key TEXT NOT NULL,
  title TEXT,
  description TEXT,
  purpose TEXT,
  status TEXT NOT NULL,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_config_id, key, parent_session_scope_key)
);
