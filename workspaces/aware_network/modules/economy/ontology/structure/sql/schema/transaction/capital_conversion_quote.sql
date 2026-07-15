-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE capital_conversion_quote (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  provider_route_id UUID NOT NULL,
  target_coin_id UUID NOT NULL,
  -- ATTRIBUTES
  captured_at TIMESTAMPTZ NOT NULL,
  conversion_mode external_capital_conversion_mode NOT NULL,
  expires_at TIMESTAMPTZ,
  external_amount_minor INTEGER NOT NULL,
  external_currency TEXT NOT NULL,
  quote_hash TEXT NOT NULL,
  quote_key TEXT NOT NULL,
  source TEXT NOT NULL,
  target_amount NUMERIC NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, quote_key)
);
