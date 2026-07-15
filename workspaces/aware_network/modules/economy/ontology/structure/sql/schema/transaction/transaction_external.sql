-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE transaction_external (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  capital_conversion_quote_id UUID NOT NULL,
  provider_config_id UUID NOT NULL,
  provider_finance_entity_id UUID NOT NULL,
  transaction_id UUID NOT NULL,
  transaction_intent_id UUID NOT NULL,
  -- ATTRIBUTES
  external_amount_minor INTEGER NOT NULL,
  external_created_at TIMESTAMPTZ NOT NULL,
  external_currency TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL,
  provider_event_id TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  provider_payload_hash TEXT NOT NULL,
  provider_public_reference TEXT NOT NULL,
  quote_hash TEXT NOT NULL,
  status transaction_external_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, provider_event_id, provider_config_id)
);
