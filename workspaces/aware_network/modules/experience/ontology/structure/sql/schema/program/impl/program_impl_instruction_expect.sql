-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_impl_instruction_expect (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_impl_instruction_id UUID UNIQUE,
  event_config_id UUID NOT NULL,
  -- ATTRIBUTES
  required BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_impl_instruction_id) REFERENCES program_impl_instruction(branch_id, projection_hash, id)
);
