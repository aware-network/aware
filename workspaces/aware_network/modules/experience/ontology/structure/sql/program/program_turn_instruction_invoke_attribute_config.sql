-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_invoke_attribute_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  program_impl_instruction_invoke_attribute_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_invoke_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, program_impl_instruction_invoke_attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_invoke_id) REFERENCES program_turn_instruction_invoke(branch_id, projection_hash, id)
);
