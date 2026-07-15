-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_invoke (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  program_impl_instruction_invoke_id UUID NOT NULL,
  program_actor_role_id UUID NOT NULL,
  projection_experience_node_class_identity_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_id UUID UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, program_impl_instruction_invoke_id, program_actor_role_id, projection_experience_node_class_identity_id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_id) REFERENCES program_turn_instruction(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_actor_role_id) REFERENCES program_actor_role(branch_id, projection_hash, id)
);
