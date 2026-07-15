-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE economy_analytic_execution (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  economy_analytic_id UUID NOT NULL,
  -- ATTRIBUTES
  cost_base_amount NUMERIC NOT NULL,
  cost_final_amount NUMERIC NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  key TEXT NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  success BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, economy_analytic_id, key)
);
