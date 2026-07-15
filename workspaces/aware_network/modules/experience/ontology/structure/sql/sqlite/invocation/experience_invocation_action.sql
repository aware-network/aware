-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_invocation_action (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  experience_invocation_action_config_id TEXT NOT NULL,
  actor_id TEXT,
  api_call_id TEXT,
  sdk_operation_call_id TEXT,
  -- ATTRIBUTES
  invocation_key TEXT NOT NULL,
  request_ref TEXT,
  receipt_ref TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, invocation_key, experience_invocation_action_config_id)
);
