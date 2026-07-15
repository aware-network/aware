-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_operation_quota_policy (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_operation_grant_id UUID UNIQUE,
  -- ATTRIBUTES
  burst_limit INTEGER,
  fail_closed BOOLEAN NOT NULL,
  limit_amount INTEGER,
  over_limit_behavior service_contract_operation_quota_over_limit_behavior NOT NULL,
  unit service_contract_operation_quota_unit NOT NULL,
  window_ service_contract_operation_quota_window NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_operation_grant_id) REFERENCES service_contract_config_operation_grant(branch_id, projection_hash, id)
);
