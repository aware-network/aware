-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_operation_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_config_id UUID NOT NULL,
  price_id UUID UNIQUE,
  -- ATTRIBUTES
  admission_mode service_operation_admission_mode NOT NULL,
  description TEXT,
  fulfillment_kind service_operation_fulfillment_kind NOT NULL,
  name TEXT NOT NULL,
  receipt_policy service_operation_receipt_policy NOT NULL,
  settlement_policy service_operation_settlement_policy NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_config_id, name),
  FOREIGN KEY (branch_id, projection_hash, service_config_id) REFERENCES service_config(branch_id, projection_hash, id)
);
