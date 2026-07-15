-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_invoke_attribute_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_invoke_id TEXT NOT NULL,
  program_impl_instruction_invoke_attribute_config_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_turn_instruction_invoke_id, program_impl_instruction_invoke_attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_invoke_id) REFERENCES program_turn_instruction_invoke(branch_id, projection_hash, id)
);
