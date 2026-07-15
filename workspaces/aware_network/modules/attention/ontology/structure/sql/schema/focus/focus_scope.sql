-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE focus_scope (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  focus_id UUID,
  observable_id UUID,
  -- ATTRIBUTES
  title TEXT NOT NULL,
  description TEXT,
  rationale TEXT,
  expires_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL,
  last_accessed TIMESTAMPTZ,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, title)
);
