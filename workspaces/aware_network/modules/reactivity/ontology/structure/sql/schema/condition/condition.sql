-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  config_id UUID NOT NULL,
  trigger_object_instance_graph_commit_id UUID NOT NULL,
  -- ATTRIBUTES
  activation_id UUID NOT NULL,
  arguments JSONB NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, activation_id, config_id)
);
