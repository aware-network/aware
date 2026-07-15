-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_focus (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  actor_id UUID NOT NULL,
  focus_id UUID NOT NULL,
  -- ATTRIBUTES
  level actor_focus_level_type,
  weight NUMERIC NOT NULL,
  weight_algorithm TEXT,
  weight_computed_at TIMESTAMPTZ,
  evidence_count INTEGER NOT NULL,
  last_evidence_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL,
  last_accessed TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_id, focus_id)
);
