-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE external_capital_provider_route (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  external_capital_provider_config_id UUID NOT NULL,
  target_coin_id UUID NOT NULL,
  -- ATTRIBUTES
  additional_metadata JSONB,
  conversion_mode external_capital_conversion_mode NOT NULL,
  external_currency TEXT NOT NULL,
  external_minor_unit_exponent INTEGER NOT NULL,
  max_external_amount_minor INTEGER,
  min_external_amount_minor INTEGER,
  route_key TEXT NOT NULL,
  status external_capital_route_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, external_capital_provider_config_id, route_key, target_coin_id),
  FOREIGN KEY (branch_id, projection_hash, external_capital_provider_config_id) REFERENCES external_capital_provider_config(branch_id, projection_hash, id)
);
