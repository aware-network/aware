-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_instance_graph_relationship (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_relationship_id UUID NOT NULL,
  target_object_instance_graph_id UUID NOT NULL,
  source_class_instance_id UUID NOT NULL,
  target_class_instance_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_relationship_id, target_object_instance_graph_id, source_class_instance_id, target_class_instance_id)
);
