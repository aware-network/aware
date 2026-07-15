-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE identity_pattern (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  identity_id TEXT NOT NULL,
  content_part_text_id TEXT NOT NULL,
  -- ATTRIBUTES
  category TEXT NOT NULL,
  confidence REAL NOT NULL,
  evidence_count INTEGER NOT NULL,
  last_applied TEXT,
  pattern_key TEXT NOT NULL,
  pattern_type TEXT NOT NULL,
  target_confidence REAL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, identity_id, pattern_key),
  FOREIGN KEY (branch_id, projection_hash, identity_id) REFERENCES identity(branch_id, projection_hash, id)
);
