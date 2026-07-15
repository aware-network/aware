-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE wallet_balance (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  wallet_id UUID NOT NULL,
  coin_id UUID NOT NULL,
  -- ATTRIBUTES
  balance NUMERIC NOT NULL,
  held_balance NUMERIC NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, wallet_id, coin_id),
  FOREIGN KEY (branch_id, projection_hash, wallet_id) REFERENCES wallet(branch_id, projection_hash, id)
);
