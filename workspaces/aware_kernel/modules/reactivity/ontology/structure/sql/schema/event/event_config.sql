-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- ATTRIBUTES
  allowed_roles TEXT[] NOT NULL,
  batch_window_ms INTEGER,
  delivery_mode event_delivery_mode NOT NULL,
  description TEXT NOT NULL,
  event_schema JSONB NOT NULL,
  event_type event_type NOT NULL,
  is_enabled BOOLEAN NOT NULL,
  is_system BOOLEAN NOT NULL,
  name TEXT NOT NULL,
  priority event_priority NOT NULL,
  require_authentication BOOLEAN NOT NULL,
  valid_sources TEXT[] NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
