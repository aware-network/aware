-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_subscription_invoice (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_subscription_id UUID NOT NULL,
  coin_id UUID NOT NULL,
  -- ATTRIBUTES
  amount NUMERIC NOT NULL,
  external_invoice_handle TEXT,
  status service_subscription_invoice_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_subscription_id, amount, coin_id),
  FOREIGN KEY (branch_id, projection_hash, service_subscription_id) REFERENCES service_subscription(branch_id, projection_hash, id)
);
