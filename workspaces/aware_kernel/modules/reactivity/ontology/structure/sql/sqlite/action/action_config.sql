-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- ATTRIBUTES
  action_schema TEXT NOT NULL,
  action_type TEXT NOT NULL,
  allowed_roles TEXT NOT NULL,
  description TEXT NOT NULL,
  is_enabled INTEGER NOT NULL,
  is_system INTEGER NOT NULL,
  name TEXT NOT NULL,
  require_authentication INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
