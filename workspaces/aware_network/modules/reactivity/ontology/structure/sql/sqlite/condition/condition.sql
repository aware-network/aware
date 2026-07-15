-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  config_id TEXT NOT NULL,
  trigger_object_instance_graph_commit_id TEXT NOT NULL,
  -- ATTRIBUTES
  activation_id TEXT NOT NULL,
  arguments TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, activation_id, config_id)
);
