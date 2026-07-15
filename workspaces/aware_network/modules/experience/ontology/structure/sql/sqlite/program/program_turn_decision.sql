-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_decision (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_id TEXT NOT NULL,
  -- ATTRIBUTES
  transition TEXT NOT NULL,
  reason TEXT NOT NULL,
  step_index INTEGER NOT NULL,
  total_steps INTEGER NOT NULL,
  invokes_in_turn INTEGER NOT NULL,
  elapsed_ms_in_turn INTEGER NOT NULL,
  awaiting_external_signal INTEGER NOT NULL,
  instruction_failed INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_id) REFERENCES program_turn_instruction(branch_id, projection_hash, id)
);
