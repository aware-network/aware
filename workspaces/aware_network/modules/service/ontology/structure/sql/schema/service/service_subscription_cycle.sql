-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_subscription_cycle (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_subscription_id UUID NOT NULL,
  invoice_id UUID,
  -- ATTRIBUTES
  cycle_number INTEGER NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  period_start TIMESTAMPTZ NOT NULL,
  status service_subscription_cycle_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_subscription_id, cycle_number),
  FOREIGN KEY (branch_id, projection_hash, service_subscription_id) REFERENCES service_subscription(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, invoice_id) REFERENCES service_subscription_invoice(branch_id, projection_hash, id)
);
