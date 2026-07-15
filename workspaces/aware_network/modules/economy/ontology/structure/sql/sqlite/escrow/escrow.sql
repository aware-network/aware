-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE escrow (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  wallet_public_id TEXT NOT NULL,
  coin_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  escrow_hash TEXT NOT NULL,
  locked_amount TEXT NOT NULL,
  op_nonce INTEGER NOT NULL,
  signature TEXT NOT NULL,
  smart_contract_reservation_id TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, wallet_public_id, op_nonce)
);
