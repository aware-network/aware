-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_node_id TEXT UNIQUE,
  parent_class_id TEXT,
  code_section_class_id TEXT,
  -- ATTRIBUTES
  class_fqn TEXT NOT NULL,
  description TEXT,
  name TEXT NOT NULL,
  is_base INTEGER NOT NULL,
  is_edge INTEGER NOT NULL,
  value_mode TEXT NOT NULL,
  identity_mode TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_fqn),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_node_id) REFERENCES object_config_graph_node(branch_id, projection_hash, id)
);
