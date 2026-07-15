-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE price_reservation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  rate_snapshot_id UUID NOT NULL,
  -- ATTRIBUTES
  actual_cost_basis_amount NUMERIC,
  actual_markup_amount NUMERIC,
  additional_metadata JSONB,
  final_amount NUMERIC,
  meter_evidence_ref TEXT,
  reservation_key TEXT NOT NULL,
  reserved_at TIMESTAMPTZ NOT NULL,
  status price_reservation_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, rate_snapshot_id, reservation_key),
  FOREIGN KEY (branch_id, projection_hash, rate_snapshot_id) REFERENCES rate_snapshot(branch_id, projection_hash, id)
);
