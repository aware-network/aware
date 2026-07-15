-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE economy_analytic_execution (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  economy_analytic_id TEXT NOT NULL,
  -- ATTRIBUTES
  cost_base_amount TEXT NOT NULL,
  cost_final_amount TEXT NOT NULL,
  end_time TEXT NOT NULL,
  key TEXT NOT NULL,
  start_time TEXT NOT NULL,
  success INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, economy_analytic_id, key)
);
