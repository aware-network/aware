-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_bind (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  program_impl_instruction_bind_id UUID NOT NULL,
  object_instance_graph_branch_id UUID NOT NULL,
  projection_experience_view_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_id UUID UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, program_impl_instruction_bind_id, object_instance_graph_branch_id, projection_experience_view_id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_id) REFERENCES program_turn_instruction(branch_id, projection_hash, id)
);
