-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_impl_instruction_intent_outcome_field_binding (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_impl_instruction_intent_id TEXT NOT NULL,
  source_program_impl_instruction_intent_id TEXT NOT NULL,
  source_response_attribute_config_id TEXT NOT NULL,
  target_request_attribute_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  required INTEGER NOT NULL,
  position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_impl_instruction_intent_id, source_program_impl_instruction_intent_id, source_response_attribute_config_id, target_request_attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, program_impl_instruction_intent_id) REFERENCES program_impl_instruction_intent(branch_id, projection_hash, id)
);
