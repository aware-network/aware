-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE transaction_intent (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  capital_conversion_quote_id TEXT UNIQUE,
  coin_id TEXT NOT NULL,
  provider_config_id TEXT NOT NULL,
  recipient_finance_entity_id TEXT NOT NULL,
  recipient_wallet_id TEXT NOT NULL,
  recipient_wallet_public_id TEXT NOT NULL,
  -- ATTRIBUTES
  amount TEXT NOT NULL,
  created_at TEXT NOT NULL,
  funding_intent_key TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  metadata_json TEXT,
  provider_key TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, funding_intent_key, provider_config_id, recipient_finance_entity_id),
  FOREIGN KEY (branch_id, projection_hash, capital_conversion_quote_id) REFERENCES capital_conversion_quote(branch_id, projection_hash, id)
);
