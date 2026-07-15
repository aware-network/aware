-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_identity (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_identity_id UUID NOT NULL,
  object_projection_graph_id UUID NOT NULL,
  -- ATTRIBUTES
  projection_name TEXT NOT NULL,
  label TEXT,
  is_branchable BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_identity_id, object_projection_graph_id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_identity_id) REFERENCES object_config_graph_identity(branch_id, projection_hash, id)
);
