-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE external_capital_provider_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  provider_finance_entity_id UUID NOT NULL,
  -- ATTRIBUTES
  additional_metadata JSONB,
  label TEXT,
  provider_key TEXT NOT NULL,
  status external_capital_provider_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, provider_key, provider_finance_entity_id)
);
