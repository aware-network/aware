-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE economy_analytic_execution_metric (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  economy_analytic_metric_id UUID NOT NULL,
  economy_analytic_execution_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  quantity NUMERIC NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, economy_analytic_execution_id, key)
);
