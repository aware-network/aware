-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  sequence INTEGER NOT NULL,
  program_instruction_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_turn_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, sequence, program_instruction_id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_id) REFERENCES program_turn(branch_id, projection_hash, id)
);
