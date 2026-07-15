-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE transaction_ (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  coin_id UUID NOT NULL,
  source_wallet_public_id UUID,
  target_wallet_public_id UUID NOT NULL,
  -- ATTRIBUTES
  capital_origin_id UUID NOT NULL,
  coin_amount NUMERIC NOT NULL,
  confirmed_at TIMESTAMPTZ,
  description TEXT,
  gas_price NUMERIC NOT NULL,
  idempotency_key TEXT,
  kind transaction_kind NOT NULL,
  nonce INTEGER NOT NULL,
  receiver_signature TEXT,
  sender_signature TEXT,
  source_previous_coin_balance NUMERIC,
  status transaction_status NOT NULL,
  target_previous_coin_balance NUMERIC,
  transaction_hash TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, capital_origin_id, nonce, coin_id, target_wallet_public_id)
);
