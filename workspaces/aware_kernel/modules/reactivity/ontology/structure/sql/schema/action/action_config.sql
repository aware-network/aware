-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- ATTRIBUTES
  action_schema JSONB NOT NULL,
  action_type TEXT NOT NULL,
  allowed_roles TEXT[] NOT NULL,
  description TEXT NOT NULL,
  is_enabled BOOLEAN NOT NULL,
  is_system BOOLEAN NOT NULL,
  name TEXT NOT NULL,
  require_authentication BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
