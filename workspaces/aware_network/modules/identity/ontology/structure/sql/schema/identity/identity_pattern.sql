-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE identity_pattern (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  identity_id UUID NOT NULL,
  content_part_text_id UUID NOT NULL,
  -- ATTRIBUTES
  category TEXT NOT NULL,
  confidence NUMERIC NOT NULL,
  evidence_count INTEGER NOT NULL,
  last_applied TIMESTAMPTZ,
  pattern_key TEXT NOT NULL,
  pattern_type identity_pattern_type NOT NULL,
  target_confidence NUMERIC,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, identity_id, pattern_key),
  FOREIGN KEY (branch_id, projection_hash, identity_id) REFERENCES identity(branch_id, projection_hash, id)
);
