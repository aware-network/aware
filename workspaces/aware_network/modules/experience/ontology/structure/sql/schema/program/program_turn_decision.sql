-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_decision (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_id UUID NOT NULL,
  -- ATTRIBUTES
  transition program_turn_transition NOT NULL,
  reason program_turn_decision_reason NOT NULL,
  step_index INTEGER NOT NULL,
  total_steps INTEGER NOT NULL,
  invokes_in_turn INTEGER NOT NULL,
  elapsed_ms_in_turn INTEGER NOT NULL,
  awaiting_external_signal BOOLEAN NOT NULL,
  instruction_failed BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_id) REFERENCES program_turn_instruction(branch_id, projection_hash, id)
);
