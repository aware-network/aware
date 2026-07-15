-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_focus_evidence (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  actor_focus_id UUID NOT NULL,
  -- ATTRIBUTES
  evidence_key TEXT NOT NULL,
  kind TEXT NOT NULL,
  source_type TEXT,
  source_id UUID,
  source_key TEXT,
  weight_delta NUMERIC NOT NULL,
  confidence NUMERIC,
  observed_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  rationale TEXT,
  metadata JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_focus_id, evidence_key),
  FOREIGN KEY (branch_id, projection_hash, actor_focus_id) REFERENCES actor_focus(branch_id, projection_hash, id)
);
