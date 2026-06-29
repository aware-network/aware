-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE commit (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  lane_id UUID NOT NULL,
  -- ATTRIBUTES
  author_id UUID NOT NULL,
  key TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  status commit_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, lane_id, key)
);
