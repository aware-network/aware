-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_invocation_action_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  action_key TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id TEXT NOT NULL,
  api_capability_endpoint_id TEXT,
  sdk_operation_id TEXT,
  -- ATTRIBUTES
  action_kind TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  label TEXT,
  receipt_policy TEXT,
  confirmation_policy TEXT,
  optimistic_policy TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, action_key)
);
