-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE change_delta (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  change_id UUID NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  property TEXT,
  kind change_delta_kind NOT NULL,
  payload JSONB NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, change_id, position)
);
