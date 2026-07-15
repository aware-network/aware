-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_operation_price_policy (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_operation_grant_id TEXT UNIQUE,
  price_id TEXT,
  pricing_policy_id TEXT,
  -- ATTRIBUTES
  fail_closed INTEGER NOT NULL,
  max_cost_required INTEGER NOT NULL,
  price_ref TEXT,
  price_source TEXT NOT NULL,
  pricing_policy_ref TEXT,
  quote_ttl_s INTEGER,
  settlement_policy_override TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_operation_grant_id) REFERENCES service_contract_config_operation_grant(branch_id, projection_hash, id)
);
