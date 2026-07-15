-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_subscription_cycle (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_subscription_id TEXT NOT NULL,
  invoice_id TEXT,
  -- ATTRIBUTES
  cycle_number INTEGER NOT NULL,
  period_end TEXT NOT NULL,
  period_start TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_subscription_id, cycle_number),
  FOREIGN KEY (branch_id, projection_hash, service_subscription_id) REFERENCES service_subscription(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, invoice_id) REFERENCES service_subscription_invoice(branch_id, projection_hash, id)
);
