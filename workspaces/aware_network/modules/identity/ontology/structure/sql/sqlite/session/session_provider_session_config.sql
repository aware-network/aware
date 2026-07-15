-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_provider_session_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  session_provider_id TEXT NOT NULL,
  session_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  config_key TEXT NOT NULL,
  title TEXT,
  status TEXT NOT NULL,
  provider_contract_ref TEXT,
  selection_policy TEXT NOT NULL,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_provider_id, config_key, session_config_id),
  FOREIGN KEY (branch_id, projection_hash, session_provider_id) REFERENCES session_provider(branch_id, projection_hash, id)
);
