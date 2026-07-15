-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE role (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  role_config_id UUID NOT NULL,
  object_instance_graph_identity_id UUID NOT NULL,
  object_instance_graph_branch_id UUID,
  -- ATTRIBUTES
  object_instance_graph_branch_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_branch_key, role_config_id, object_instance_graph_identity_id)
);
