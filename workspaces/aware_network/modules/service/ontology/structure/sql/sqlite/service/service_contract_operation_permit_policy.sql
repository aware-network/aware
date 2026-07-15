-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_operation_permit_policy (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_operation_grant_id TEXT UNIQUE,
  -- ATTRIBUTES
  fail_closed INTEGER NOT NULL,
  idempotency_scope TEXT NOT NULL,
  permit_scope TEXT NOT NULL,
  requires_active_contract INTEGER NOT NULL,
  requires_reservation_before_execute INTEGER NOT NULL,
  requires_smart_contract_permit INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_operation_grant_id) REFERENCES service_contract_config_operation_grant(branch_id, projection_hash, id)
);
