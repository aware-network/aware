-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_id UUID NOT NULL,
  commercial_profile_id UUID NOT NULL,
  consumer_finance_entity_id UUID NOT NULL,
  producer_finance_entity_id UUID NOT NULL,
  service_contract_config_id UUID NOT NULL,
  smart_contract_id UUID NOT NULL,
  -- ATTRIBUTES
  effective_from TIMESTAMPTZ NOT NULL,
  effective_until TIMESTAMPTZ,
  kind service_contract_kind NOT NULL,
  metadata_json JSONB,
  status service_contract_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_id, service_contract_config_id, smart_contract_id)
);
