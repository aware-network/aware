-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_provider (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_profile_config_id UUID NOT NULL,
  -- ATTRIBUTES
  contract_ref TEXT,
  description TEXT,
  metadata_json JSONB,
  provider_key TEXT NOT NULL,
  provider_kind TEXT NOT NULL,
  selection_policy TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_profile_config_id, provider_key),
  FOREIGN KEY (branch_id, projection_hash, environment_profile_config_id) REFERENCES environment_profile_config(branch_id, projection_hash, id)
);
