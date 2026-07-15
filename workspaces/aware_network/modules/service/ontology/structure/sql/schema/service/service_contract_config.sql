-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_config_id UUID NOT NULL,
  projection_experience_id UUID,
  -- ATTRIBUTES
  default_kind service_contract_kind NOT NULL,
  description TEXT,
  metadata_json JSONB,
  name TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_config_id, name),
  FOREIGN KEY (branch_id, projection_hash, service_config_id) REFERENCES service_config(branch_id, projection_hash, id)
);
