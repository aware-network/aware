-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE price_reservation (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  rate_snapshot_id TEXT NOT NULL,
  -- ATTRIBUTES
  actual_cost_basis_amount TEXT,
  actual_markup_amount TEXT,
  additional_metadata TEXT,
  final_amount TEXT,
  meter_evidence_ref TEXT,
  reservation_key TEXT NOT NULL,
  reserved_at TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, rate_snapshot_id, reservation_key),
  FOREIGN KEY (branch_id, projection_hash, rate_snapshot_id) REFERENCES rate_snapshot(branch_id, projection_hash, id)
);
