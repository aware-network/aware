-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_config_operation_grant (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_id UUID NOT NULL,
  service_operation_config_id UUID NOT NULL,
  -- ATTRIBUTES
  access_scope TEXT NOT NULL,
  description TEXT,
  permit_policy_json JSONB,
  price_policy_json JSONB,
  quota_policy_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_contract_config_id, service_operation_config_id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_id) REFERENCES service_contract_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_operation_config_id) REFERENCES service_operation_config(branch_id, projection_hash, id)
);
