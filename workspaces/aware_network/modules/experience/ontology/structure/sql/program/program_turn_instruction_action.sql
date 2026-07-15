-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_turn_instruction_action (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  intent_key TEXT NOT NULL,
  program_impl_instruction_intent_id UUID NOT NULL,
  action_config_id UUID NOT NULL,
  event_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_turn_instruction_id UUID UNIQUE,
  -- ATTRIBUTES
  action_intent_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, intent_key, program_impl_instruction_intent_id, action_config_id, event_config_id),
  FOREIGN KEY (branch_id, projection_hash, program_turn_instruction_id) REFERENCES program_turn_instruction(branch_id, projection_hash, id)
);
