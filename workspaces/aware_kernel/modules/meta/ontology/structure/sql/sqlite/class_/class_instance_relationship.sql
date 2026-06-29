-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_instance_relationship (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_id TEXT NOT NULL,
  class_config_relationship_id TEXT NOT NULL,
  class_instance_relationship_identity_id TEXT,
  source_class_instance_id TEXT NOT NULL,
  target_class_instance_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_id, class_config_relationship_id, source_class_instance_id, target_class_instance_id)
);
