-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_invocation_action_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  action_key TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id UUID NOT NULL,
  api_capability_endpoint_id UUID,
  sdk_operation_id UUID,
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
