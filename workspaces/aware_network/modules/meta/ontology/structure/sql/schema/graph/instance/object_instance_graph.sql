-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_instance_graph (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_id UUID NOT NULL,
  root_class_instance_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  hash TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_id, key)
);
