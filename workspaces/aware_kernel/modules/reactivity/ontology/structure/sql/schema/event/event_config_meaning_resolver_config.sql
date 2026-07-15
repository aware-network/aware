-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_config_meaning_resolver_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  event_config_id UUID NOT NULL,
  action_config_id UUID NOT NULL,
  -- ATTRIBUTES
  resolver_key TEXT NOT NULL,
  priority INTEGER NOT NULL,
  is_enabled BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_config_id, resolver_key, action_config_id)
);
