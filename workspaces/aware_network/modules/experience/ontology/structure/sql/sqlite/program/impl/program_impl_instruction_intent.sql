-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_impl_instruction_intent (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_impl_instruction_id TEXT UNIQUE,
  action_config_id TEXT NOT NULL,
  event_config_id TEXT NOT NULL,
  api_capability_endpoint_id TEXT,
  request_class_config_id TEXT,
  response_class_config_id TEXT,
  -- ATTRIBUTES
  continuation_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_impl_instruction_id) REFERENCES program_impl_instruction(branch_id, projection_hash, id)
);
