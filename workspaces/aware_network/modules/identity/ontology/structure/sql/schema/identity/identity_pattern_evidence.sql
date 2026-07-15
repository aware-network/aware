-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE identity_pattern_evidence (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  identity_pattern_id UUID NOT NULL,
  observer_id UUID,
  content_part_text_id UUID NOT NULL,
  -- ATTRIBUTES
  confidence_impact NUMERIC NOT NULL,
  context_summary TEXT NOT NULL,
  evidence_type TEXT NOT NULL,
  outcome TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, identity_pattern_id, evidence_type, content_part_text_id)
);
