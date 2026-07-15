-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE credential_usage_receipt (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  credential_profile_id UUID NOT NULL,
  -- ATTRIBUTES
  receipt_key TEXT NOT NULL,
  status credential_usage_status NOT NULL,
  operation TEXT NOT NULL,
  used_at_utc TEXT,
  target_ref TEXT,
  secret_ref_key TEXT,
  request_ref TEXT,
  receipt JSONB,
  error TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, credential_profile_id, receipt_key),
  FOREIGN KEY (branch_id, projection_hash, credential_profile_id) REFERENCES credential_profile(branch_id, projection_hash, id)
);
