-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE enum_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_node_id TEXT UNIQUE,
  code_section_enum_id TEXT,
  -- ATTRIBUTES
  enum_fqn TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, enum_fqn),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_node_id) REFERENCES object_config_graph_node(branch_id, projection_hash, id)
);
