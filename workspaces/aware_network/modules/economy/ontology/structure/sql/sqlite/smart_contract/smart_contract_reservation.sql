-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract_reservation (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  smart_contract_permit_id TEXT NOT NULL,
  escrow_id TEXT,
  rate_snapshot_id TEXT NOT NULL,
  -- ATTRIBUTES
  args_hash TEXT NOT NULL,
  deadline TEXT NOT NULL,
  final_cost TEXT,
  max_cost TEXT NOT NULL,
  op_nonce INTEGER NOT NULL,
  reservation_signature TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, smart_contract_permit_id, op_nonce),
  FOREIGN KEY (branch_id, projection_hash, smart_contract_permit_id) REFERENCES smart_contract_permit(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, escrow_id) REFERENCES escrow(branch_id, projection_hash, id)
);
