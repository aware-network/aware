-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_port_projection_experience_node (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_config_port_id UUID NOT NULL,
  projection_experience_node_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_config_port_id, key, projection_experience_node_id),
  FOREIGN KEY (branch_id, projection_hash, program_config_port_id) REFERENCES program_config_port(branch_id, projection_hash, id)
);
