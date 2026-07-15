-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_operation_quota_policy (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_operation_grant_id TEXT UNIQUE,
  -- ATTRIBUTES
  burst_limit INTEGER,
  fail_closed INTEGER NOT NULL,
  limit_amount INTEGER,
  over_limit_behavior TEXT NOT NULL,
  unit TEXT NOT NULL,
  window_ TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_operation_grant_id) REFERENCES service_contract_config_operation_grant(branch_id, projection_hash, id)
);
