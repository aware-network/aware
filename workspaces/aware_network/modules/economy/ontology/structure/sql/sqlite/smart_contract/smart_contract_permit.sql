-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract_permit (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  smart_contract_id TEXT NOT NULL,
  smart_contract_permit_id TEXT,
  coin_id TEXT NOT NULL,
  finance_entity_id TEXT NOT NULL,
  price_schedule_id TEXT NOT NULL,
  -- ATTRIBUTES
  cap_amount TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  nonce INTEGER NOT NULL,
  permit_nonce INTEGER NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, smart_contract_permit_id, smart_contract_id, permit_nonce, finance_entity_id),
  FOREIGN KEY (branch_id, projection_hash, smart_contract_id) REFERENCES smart_contract(branch_id, projection_hash, id)
);
