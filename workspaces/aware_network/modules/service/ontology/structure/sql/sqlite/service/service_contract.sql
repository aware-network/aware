-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_id TEXT NOT NULL,
  commercial_profile_id TEXT NOT NULL,
  consumer_finance_entity_id TEXT NOT NULL,
  producer_finance_entity_id TEXT NOT NULL,
  service_contract_config_id TEXT NOT NULL,
  smart_contract_id TEXT NOT NULL,
  -- ATTRIBUTES
  effective_from TEXT NOT NULL,
  effective_until TEXT,
  kind TEXT NOT NULL,
  metadata_json TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_id, service_contract_config_id, smart_contract_id)
);
