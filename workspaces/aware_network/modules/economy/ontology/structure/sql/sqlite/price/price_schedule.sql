-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE price_schedule (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  price_id TEXT NOT NULL,
  pricing_policy_id TEXT NOT NULL,
  -- ATTRIBUTES
  additional_metadata TEXT,
  effective_from TEXT NOT NULL,
  effective_until TEXT,
  fixed_amount TEXT,
  markup_percentage TEXT,
  name TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, price_id, name, version, pricing_policy_id),
  FOREIGN KEY (branch_id, projection_hash, price_id) REFERENCES price(branch_id, projection_hash, id)
);
