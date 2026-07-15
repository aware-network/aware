-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE economy_analytic_metric (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  economy_analytic_id UUID NOT NULL,
  -- ATTRIBUTES
  cost_per_unit NUMERIC,
  description TEXT,
  name TEXT NOT NULL,
  unit TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, economy_analytic_id, name)
);
