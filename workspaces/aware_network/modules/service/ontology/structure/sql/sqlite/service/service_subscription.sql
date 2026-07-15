-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_subscription (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  consumer_finance_entity_id TEXT NOT NULL,
  contract_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  service_id TEXT NOT NULL,
  -- ATTRIBUTES
  cancel_at_period_end INTEGER NOT NULL,
  current_period_end TEXT,
  current_period_start TEXT,
  external_subscription_handle TEXT,
  metadata_json TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, consumer_finance_entity_id, service_id)
);
