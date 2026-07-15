-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_binding_class (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_binding_id TEXT NOT NULL,
  source_class_id TEXT NOT NULL,
  source_attr_id TEXT,
  target_class_id TEXT NOT NULL,
  target_attribute_id TEXT NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_binding_id, source_class_id, target_class_id, target_attribute_id)
);
