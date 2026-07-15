-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE transaction_ (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  coin_id TEXT NOT NULL,
  source_wallet_public_id TEXT,
  target_wallet_public_id TEXT NOT NULL,
  -- ATTRIBUTES
  capital_origin_id TEXT NOT NULL,
  coin_amount TEXT NOT NULL,
  confirmed_at TEXT,
  description TEXT,
  gas_price TEXT NOT NULL,
  idempotency_key TEXT,
  kind TEXT NOT NULL,
  nonce INTEGER NOT NULL,
  receiver_signature TEXT,
  sender_signature TEXT,
  source_previous_coin_balance TEXT,
  status TEXT NOT NULL,
  target_previous_coin_balance TEXT,
  transaction_hash TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, capital_origin_id, nonce, coin_id, target_wallet_public_id)
);
