-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE transaction_intent_external_expiration (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  transaction_intent_id UUID NOT NULL,
  capital_conversion_quote_id UUID NOT NULL,
  provider_config_id UUID NOT NULL,
  -- ATTRIBUTES
  external_created_at TIMESTAMPTZ NOT NULL,
  idempotency_key TEXT NOT NULL,
  provider_event_id TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  provider_payload_hash TEXT NOT NULL,
  provider_public_reference TEXT NOT NULL,
  quote_hash TEXT NOT NULL,
  recorded_at TIMESTAMPTZ NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, transaction_intent_id, provider_event_id, provider_config_id),
  FOREIGN KEY (branch_id, projection_hash, transaction_intent_id) REFERENCES transaction_intent(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, capital_conversion_quote_id) REFERENCES capital_conversion_quote(branch_id, projection_hash, id)
);
