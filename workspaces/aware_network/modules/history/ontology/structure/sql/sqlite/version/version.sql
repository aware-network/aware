-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE version (
  -- PRIMARY KEY
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  branch_id TEXT NOT NULL,
  -- RELATIONSHIPS
  version_id TEXT,
  head_commit_id TEXT,
  -- ATTRIBUTES
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (projection_hash, id, branch_id),
  UNIQUE (branch_id, projection_hash, version_id, version_number)
);
