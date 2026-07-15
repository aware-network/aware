-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_provider_action_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  experience_provider_id UUID NOT NULL,
  experience_invocation_action_config_id UUID NOT NULL,
  -- ATTRIBUTES
  binding_key TEXT NOT NULL,
  description TEXT,
  provider_action_ref TEXT,
  required_contract_scope TEXT NOT NULL,
  selection_policy TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_provider_id, binding_key, experience_invocation_action_config_id)
);
