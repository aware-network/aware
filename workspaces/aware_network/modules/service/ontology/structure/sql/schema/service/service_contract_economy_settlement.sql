-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_economy_settlement (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_contract_id UUID UNIQUE,
  coin_id UUID NOT NULL,
  payer_wallet_id UUID NOT NULL,
  payer_wallet_public_id UUID NOT NULL,
  permit_id UUID NOT NULL,
  receiver_wallet_id UUID NOT NULL,
  receiver_wallet_public_id UUID NOT NULL,
  -- ATTRIBUTES
  deadline TIMESTAMPTZ NOT NULL,
  permit_nonce INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_id) REFERENCES service_contract(branch_id, projection_hash, id)
);
