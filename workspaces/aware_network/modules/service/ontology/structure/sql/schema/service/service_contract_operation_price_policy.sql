-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_operation_price_policy (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_operation_grant_id UUID UNIQUE,
  price_id UUID,
  pricing_policy_id UUID,
  -- ATTRIBUTES
  fail_closed BOOLEAN NOT NULL,
  max_cost_required BOOLEAN NOT NULL,
  price_ref TEXT,
  price_source service_contract_operation_price_source NOT NULL,
  pricing_policy_ref TEXT,
  quote_ttl_s INTEGER,
  settlement_policy_override service_operation_settlement_policy,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_operation_grant_id) REFERENCES service_contract_config_operation_grant(branch_id, projection_hash, id)
);
