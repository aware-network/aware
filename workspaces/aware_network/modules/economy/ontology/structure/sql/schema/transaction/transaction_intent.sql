-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE transaction_intent (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  capital_conversion_quote_id UUID UNIQUE,
  coin_id UUID NOT NULL,
  provider_config_id UUID NOT NULL,
  recipient_finance_entity_id UUID NOT NULL,
  recipient_wallet_id UUID NOT NULL,
  recipient_wallet_public_id UUID NOT NULL,
  -- ATTRIBUTES
  amount NUMERIC NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  funding_intent_key TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  metadata_json JSONB,
  provider_key TEXT NOT NULL,
  status transaction_intent_status NOT NULL,
  updated_at TIMESTAMPTZ,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, funding_intent_key, provider_config_id, recipient_finance_entity_id),
  FOREIGN KEY (branch_id, projection_hash, capital_conversion_quote_id) REFERENCES capital_conversion_quote(branch_id, projection_hash, id)
);
