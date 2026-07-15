-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_bind_identity (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  program_config_port_projection_experience_node_id UUID NOT NULL,
  projection_experience_node_class_identity_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_bind_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, program_config_port_projection_experience_node_id, projection_experience_node_class_identity_id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_bind_id) REFERENCES program_turn_instruction_bind(branch_id, projection_hash, id)
);
