-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_impl_instruction_invoke (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_impl_instruction_id UUID UNIQUE,
  function_config_id UUID NOT NULL,
  program_config_actor_config_id UUID NOT NULL,
  program_config_port_projection_experience_node_id UUID NOT NULL,
  -- ATTRIBUTES
  target_kind program_impl_invoke_target_kind NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_impl_instruction_id) REFERENCES program_impl_instruction(branch_id, projection_hash, id)
);
