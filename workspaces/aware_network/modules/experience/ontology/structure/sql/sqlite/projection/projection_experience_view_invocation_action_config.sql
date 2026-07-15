-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_view_invocation_action_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_view_id TEXT NOT NULL,
  api_view_capability_endpoint_id TEXT NOT NULL,
  sdk_operation_api_view_capability_endpoint_id TEXT,
  experience_invocation_action_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  action_key TEXT NOT NULL,
  label TEXT,
  receipt_policy TEXT,
  confirmation_policy TEXT,
  optimistic_policy TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_view_id, api_view_capability_endpoint_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_view_id) REFERENCES projection_experience_view(branch_id, projection_hash, id)
);
