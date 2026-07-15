-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_declaration (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL UNIQUE,
  projection_name TEXT NOT NULL,
  label TEXT,
  description TEXT,
  is_branchable BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_id, projection_name),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_id) REFERENCES object_config_graph(branch_id, projection_hash, id)
);
