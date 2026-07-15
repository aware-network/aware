-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE economy_analytic (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- ATTRIBUTES
  average_cost_base_amount TEXT,
  average_cost_final_amount TEXT,
  average_duration REAL,
  failure_count INTEGER,
  key TEXT NOT NULL,
  success_count INTEGER,
  success_rate REAL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key)
);
