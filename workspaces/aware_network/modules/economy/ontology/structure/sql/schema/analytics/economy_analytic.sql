-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE economy_analytic (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- ATTRIBUTES
  average_cost_base_amount NUMERIC,
  average_cost_final_amount NUMERIC,
  average_duration NUMERIC,
  failure_count INTEGER,
  key TEXT NOT NULL,
  success_count INTEGER,
  success_rate NUMERIC,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key)
);
