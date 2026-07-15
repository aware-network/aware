-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE rate_snapshot (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  price_schedule_id UUID NOT NULL,
  -- ATTRIBUTES
  additional_metadata JSONB,
  captured_at TIMESTAMPTZ NOT NULL,
  cost_basis_amount NUMERIC,
  markup_amount NUMERIC,
  markup_percentage NUMERIC,
  meter_evidence_ref TEXT,
  quoted_amount NUMERIC NOT NULL,
  snapshot_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, price_schedule_id, snapshot_key),
  FOREIGN KEY (branch_id, projection_hash, price_schedule_id) REFERENCES price_schedule(branch_id, projection_hash, id)
);
