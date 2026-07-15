-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_economy_settlement (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_contract_id TEXT UNIQUE,
  coin_id TEXT NOT NULL,
  payer_wallet_id TEXT NOT NULL,
  payer_wallet_public_id TEXT NOT NULL,
  permit_id TEXT NOT NULL,
  receiver_wallet_id TEXT NOT NULL,
  receiver_wallet_public_id TEXT NOT NULL,
  -- ATTRIBUTES
  deadline TEXT NOT NULL,
  permit_nonce INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_id) REFERENCES service_contract(branch_id, projection_hash, id)
);
