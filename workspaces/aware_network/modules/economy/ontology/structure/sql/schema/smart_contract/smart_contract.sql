-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  smart_contract_config_id UUID NOT NULL,
  -- ATTRIBUTES
  arguments JSONB NOT NULL,
  blockchain_address TEXT NOT NULL,
  status smart_contract_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, smart_contract_config_id, blockchain_address)
);
