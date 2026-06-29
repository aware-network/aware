-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_instance_identity (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_identity_id TEXT NOT NULL,
  class_instance_id TEXT NOT NULL,
  -- ATTRIBUTES
  label TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_identity_id, class_instance_id),
  FOREIGN KEY (branch_id, projection_hash, object_instance_graph_identity_id) REFERENCES object_instance_graph_identity(branch_id, projection_hash, id)
);
