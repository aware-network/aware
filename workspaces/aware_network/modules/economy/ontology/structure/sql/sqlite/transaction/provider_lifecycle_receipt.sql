-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE provider_lifecycle_receipt (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  coin_id TEXT NOT NULL,
  provider_finance_entity_id TEXT NOT NULL,
  transaction_id TEXT NOT NULL,
  transaction_external_id TEXT NOT NULL,
  wallet_id TEXT NOT NULL,
  wallet_finance_entity_id TEXT NOT NULL,
  wallet_public_id TEXT NOT NULL,
  -- ATTRIBUTES
  amount TEXT NOT NULL,
  event_kind TEXT NOT NULL,
  external_created_at TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  metadata_json TEXT,
  new_available_balance TEXT NOT NULL,
  new_balance TEXT NOT NULL,
  new_held_balance TEXT NOT NULL,
  previous_available_balance TEXT NOT NULL,
  previous_balance TEXT NOT NULL,
  previous_held_balance TEXT NOT NULL,
  processed_at TEXT NOT NULL,
  provider_event_id TEXT NOT NULL,
  provider_lifecycle_effect_key TEXT NOT NULL,
  provider_lifecycle_object_id TEXT NOT NULL,
  provider_payment_reference TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  provider_payload_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, provider_lifecycle_effect_key, provider_lifecycle_object_id, provider_key, provider_finance_entity_id)
);
