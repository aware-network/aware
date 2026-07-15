-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE wallet_balance (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  wallet_id TEXT NOT NULL,
  coin_id TEXT NOT NULL,
  -- ATTRIBUTES
  balance TEXT NOT NULL,
  held_balance TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, wallet_id, coin_id),
  FOREIGN KEY (branch_id, projection_hash, wallet_id) REFERENCES wallet(branch_id, projection_hash, id)
);
