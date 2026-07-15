-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_impl_instruction_intent_activation_field_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_impl_instruction_intent_id UUID NOT NULL,
  source_class_config_id UUID NOT NULL,
  source_attribute_config_id UUID NOT NULL,
  target_request_attribute_config_id UUID NOT NULL,
  -- ATTRIBUTES
  source_input_key TEXT NOT NULL,
  required BOOLEAN NOT NULL,
  position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_impl_instruction_intent_id, source_input_key, source_class_config_id, source_attribute_config_id, target_request_attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, program_impl_instruction_intent_id) REFERENCES program_impl_instruction_intent(branch_id, projection_hash, id)
);
