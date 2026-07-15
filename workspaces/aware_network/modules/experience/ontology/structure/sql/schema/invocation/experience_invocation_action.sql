-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_invocation_action (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  experience_invocation_action_config_id UUID NOT NULL,
  actor_id UUID,
  api_call_id UUID,
  sdk_operation_call_id UUID,
  -- ATTRIBUTES
  invocation_key UUID NOT NULL,
  request_ref TEXT,
  receipt_ref TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, invocation_key, experience_invocation_action_config_id)
);
