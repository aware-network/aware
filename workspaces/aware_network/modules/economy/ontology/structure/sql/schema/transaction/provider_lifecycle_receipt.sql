-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE provider_lifecycle_receipt (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  coin_id UUID NOT NULL,
  provider_finance_entity_id UUID NOT NULL,
  transaction_id UUID NOT NULL,
  transaction_external_id UUID NOT NULL,
  wallet_id UUID NOT NULL,
  wallet_finance_entity_id UUID NOT NULL,
  wallet_public_id UUID NOT NULL,
  -- ATTRIBUTES
  amount NUMERIC NOT NULL,
  event_kind provider_lifecycle_event_kind NOT NULL,
  external_created_at TIMESTAMPTZ NOT NULL,
  idempotency_key TEXT NOT NULL,
  metadata_json JSONB,
  new_available_balance NUMERIC NOT NULL,
  new_balance NUMERIC NOT NULL,
  new_held_balance NUMERIC NOT NULL,
  previous_available_balance NUMERIC NOT NULL,
  previous_balance NUMERIC NOT NULL,
  previous_held_balance NUMERIC NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL,
  provider_event_id TEXT NOT NULL,
  provider_lifecycle_effect_key TEXT NOT NULL,
  provider_lifecycle_object_id TEXT NOT NULL,
  provider_payment_reference TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  provider_payload_hash TEXT NOT NULL,
  status provider_lifecycle_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, provider_lifecycle_effect_key, provider_lifecycle_object_id, provider_key, provider_finance_entity_id)
);
