-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- ATTRIBUTES
  allowed_roles TEXT NOT NULL,
  batch_window_ms INTEGER,
  delivery_mode TEXT NOT NULL,
  description TEXT NOT NULL,
  event_schema TEXT NOT NULL,
  event_type TEXT NOT NULL,
  is_enabled INTEGER NOT NULL,
  is_system INTEGER NOT NULL,
  name TEXT NOT NULL,
  priority TEXT NOT NULL,
  require_authentication INTEGER NOT NULL,
  valid_sources TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
