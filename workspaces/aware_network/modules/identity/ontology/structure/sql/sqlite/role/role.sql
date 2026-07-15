-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE role (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  role_config_id TEXT NOT NULL,
  object_instance_graph_identity_id TEXT NOT NULL,
  object_instance_graph_branch_id TEXT,
  -- ATTRIBUTES
  object_instance_graph_branch_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_branch_key, role_config_id, object_instance_graph_identity_id)
);
