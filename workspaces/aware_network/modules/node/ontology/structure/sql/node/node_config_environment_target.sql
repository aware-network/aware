-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_environment_target (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  environment_handle TEXT NOT NULL,
  -- RELATIONSHIPS
  node_config_id UUID NOT NULL,
  environment_config_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, environment_handle),
  FOREIGN KEY (branch_id, projection_hash, node_config_id) REFERENCES node_config(branch_id, projection_hash, id)
);
