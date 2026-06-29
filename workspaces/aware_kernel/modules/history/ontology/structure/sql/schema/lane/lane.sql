-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE lane (
  -- PRIMARY KEY
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  branch_id UUID NOT NULL,
  -- RELATIONSHIPS
  head_commit_id UUID,
  -- ATTRIBUTES
  lane_hash TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (projection_hash, id, branch_id),
  UNIQUE (branch_id, projection_hash, lane_hash),
  FOREIGN KEY (branch_id, projection_hash, branch_id) REFERENCES branch(branch_id, projection_hash, id)
);
