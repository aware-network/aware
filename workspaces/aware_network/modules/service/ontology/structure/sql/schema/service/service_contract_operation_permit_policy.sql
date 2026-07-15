-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_operation_permit_policy (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_operation_grant_id UUID UNIQUE,
  -- ATTRIBUTES
  fail_closed BOOLEAN NOT NULL,
  idempotency_scope service_contract_operation_permit_idempotency_scope NOT NULL,
  permit_scope service_contract_operation_permit_scope NOT NULL,
  requires_active_contract BOOLEAN NOT NULL,
  requires_reservation_before_execute BOOLEAN NOT NULL,
  requires_smart_contract_permit BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_operation_grant_id) REFERENCES service_contract_config_operation_grant(branch_id, projection_hash, id)
);
