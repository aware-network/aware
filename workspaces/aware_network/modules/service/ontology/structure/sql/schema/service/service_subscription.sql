-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_subscription (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  consumer_finance_entity_id UUID NOT NULL,
  contract_id UUID NOT NULL,
  plan_id UUID NOT NULL,
  service_id UUID NOT NULL,
  -- ATTRIBUTES
  cancel_at_period_end BOOLEAN NOT NULL,
  current_period_end TIMESTAMPTZ,
  current_period_start TIMESTAMPTZ,
  external_subscription_handle TEXT,
  metadata_json JSONB,
  status service_subscription_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, consumer_finance_entity_id, service_id)
);
