-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_plan (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_id TEXT NOT NULL,
  coin_id TEXT NOT NULL,
  smart_contract_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  cycle TEXT NOT NULL,
  external_price_handle TEXT,
  policy_json TEXT NOT NULL,
  price_amount TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_id, cycle, price_amount, coin_id, smart_contract_config_id),
  FOREIGN KEY (branch_id, projection_hash, service_id) REFERENCES service(branch_id, projection_hash, id)
);
