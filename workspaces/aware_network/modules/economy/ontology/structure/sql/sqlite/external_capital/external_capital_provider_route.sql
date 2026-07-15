-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE external_capital_provider_route (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  external_capital_provider_config_id TEXT NOT NULL,
  target_coin_id TEXT NOT NULL,
  -- ATTRIBUTES
  additional_metadata TEXT,
  conversion_mode TEXT NOT NULL,
  external_currency TEXT NOT NULL,
  external_minor_unit_exponent INTEGER NOT NULL,
  max_external_amount_minor INTEGER,
  min_external_amount_minor INTEGER,
  route_key TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, external_capital_provider_config_id, route_key, target_coin_id),
  FOREIGN KEY (branch_id, projection_hash, external_capital_provider_config_id) REFERENCES external_capital_provider_config(branch_id, projection_hash, id)
);
