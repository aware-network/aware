-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE capital_conversion_quote (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  provider_route_id TEXT NOT NULL,
  target_coin_id TEXT NOT NULL,
  -- ATTRIBUTES
  captured_at TEXT NOT NULL,
  conversion_mode TEXT NOT NULL,
  expires_at TEXT,
  external_amount_minor INTEGER NOT NULL,
  external_currency TEXT NOT NULL,
  quote_hash TEXT NOT NULL,
  quote_key TEXT NOT NULL,
  source TEXT NOT NULL,
  target_amount TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, quote_key)
);
