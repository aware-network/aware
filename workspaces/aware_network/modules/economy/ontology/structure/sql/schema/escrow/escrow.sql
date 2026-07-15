-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE escrow (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  wallet_public_id UUID NOT NULL,
  coin_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  escrow_hash TEXT NOT NULL,
  locked_amount NUMERIC NOT NULL,
  op_nonce INTEGER NOT NULL,
  signature TEXT NOT NULL,
  smart_contract_reservation_id UUID NOT NULL,
  status escrow_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, wallet_public_id, op_nonce)
);
