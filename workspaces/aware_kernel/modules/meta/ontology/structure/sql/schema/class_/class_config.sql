-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_node_id UUID UNIQUE,
  parent_class_id UUID,
  code_section_class_id UUID,
  -- ATTRIBUTES
  class_fqn TEXT NOT NULL,
  description TEXT,
  name TEXT NOT NULL,
  is_base BOOLEAN NOT NULL,
  is_edge BOOLEAN NOT NULL,
  value_mode class_value_mode NOT NULL,
  identity_mode class_identity_mode NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_fqn),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_node_id) REFERENCES object_config_graph_node(branch_id, projection_hash, id)
);
