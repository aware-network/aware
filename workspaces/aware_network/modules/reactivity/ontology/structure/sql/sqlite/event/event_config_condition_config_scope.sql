-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_config_condition_config_scope (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  event_config_condition_config_id TEXT NOT NULL,
  object_instance_graph_identity_id TEXT NOT NULL,
  object_instance_graph_branch_id TEXT,
  class_instance_identity_id TEXT,
  -- ATTRIBUTES
  scope_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_config_condition_config_id, scope_key, object_instance_graph_identity_id)
);
