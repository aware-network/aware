-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_plan (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_id UUID NOT NULL,
  coin_id UUID NOT NULL,
  smart_contract_config_id UUID NOT NULL,
  -- ATTRIBUTES
  cycle service_plan_cycle NOT NULL,
  external_price_handle TEXT,
  policy_json JSONB NOT NULL,
  price_amount NUMERIC NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_id, cycle, price_amount, coin_id, smart_contract_config_id),
  FOREIGN KEY (branch_id, projection_hash, service_id) REFERENCES service(branch_id, projection_hash, id)
);
