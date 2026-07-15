-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_config_id TEXT NOT NULL,
  projection_experience_id TEXT,
  -- ATTRIBUTES
  default_kind TEXT NOT NULL,
  description TEXT,
  metadata_json TEXT,
  name TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_config_id, name),
  FOREIGN KEY (branch_id, projection_hash, service_config_id) REFERENCES service_config(branch_id, projection_hash, id)
);
