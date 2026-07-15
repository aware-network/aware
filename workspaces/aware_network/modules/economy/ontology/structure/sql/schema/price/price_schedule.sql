-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE price_schedule (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  price_id UUID NOT NULL,
  pricing_policy_id UUID NOT NULL,
  -- ATTRIBUTES
  additional_metadata JSONB,
  effective_from TIMESTAMPTZ NOT NULL,
  effective_until TIMESTAMPTZ,
  fixed_amount NUMERIC,
  markup_percentage NUMERIC,
  name TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, price_id, name, version, pricing_policy_id),
  FOREIGN KEY (branch_id, projection_hash, price_id) REFERENCES price(branch_id, projection_hash, id)
);
