-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_provider_session_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  session_provider_id UUID NOT NULL,
  session_config_id UUID NOT NULL,
  -- ATTRIBUTES
  config_key TEXT NOT NULL,
  title TEXT,
  status TEXT NOT NULL,
  provider_contract_ref TEXT,
  selection_policy TEXT NOT NULL,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_provider_id, config_key, session_config_id),
  FOREIGN KEY (branch_id, projection_hash, session_provider_id) REFERENCES session_provider(branch_id, projection_hash, id)
);
