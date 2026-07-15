-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_port_projection_experience_node_identity (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  projection_experience_node_identity_id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_config_port_projection_experience_node_id TEXT UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key, projection_experience_node_identity_id),
  FOREIGN KEY (branch_id, projection_hash, program_config_port_projection_experience_node_id) REFERENCES program_config_port_projection_experience_node(branch_id, projection_hash, id)
);
