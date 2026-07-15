-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE rate_snapshot (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  price_schedule_id TEXT NOT NULL,
  -- ATTRIBUTES
  additional_metadata TEXT,
  captured_at TEXT NOT NULL,
  cost_basis_amount TEXT,
  markup_amount TEXT,
  markup_percentage TEXT,
  meter_evidence_ref TEXT,
  quoted_amount TEXT NOT NULL,
  snapshot_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, price_schedule_id, snapshot_key),
  FOREIGN KEY (branch_id, projection_hash, price_schedule_id) REFERENCES price_schedule(branch_id, projection_hash, id)
);
