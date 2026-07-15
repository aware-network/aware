-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract_permit (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  smart_contract_id UUID NOT NULL,
  smart_contract_permit_id UUID,
  coin_id UUID NOT NULL,
  finance_entity_id UUID NOT NULL,
  price_schedule_id UUID NOT NULL,
  -- ATTRIBUTES
  cap_amount NUMERIC NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  nonce INTEGER NOT NULL,
  permit_nonce INTEGER NOT NULL,
  status smart_contract_permit_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, smart_contract_permit_id, smart_contract_id, permit_nonce, finance_entity_id),
  FOREIGN KEY (branch_id, projection_hash, smart_contract_id) REFERENCES smart_contract(branch_id, projection_hash, id)
);
