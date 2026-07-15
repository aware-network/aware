-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE economy_analytic_execution_metric (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  economy_analytic_metric_id TEXT NOT NULL,
  economy_analytic_execution_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  quantity REAL NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, economy_analytic_execution_id, key)
);
