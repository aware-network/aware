-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE wallet_external_ingress_application (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  wallet_id TEXT NOT NULL,
  coin_id TEXT NOT NULL,
  transaction_id TEXT NOT NULL,
  -- ATTRIBUTES
  amount TEXT NOT NULL,
  applied_at TEXT NOT NULL,
  new_balance TEXT NOT NULL,
  previous_balance TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, wallet_id, transaction_id),
  FOREIGN KEY (branch_id, projection_hash, wallet_id) REFERENCES wallet(branch_id, projection_hash, id)
);
