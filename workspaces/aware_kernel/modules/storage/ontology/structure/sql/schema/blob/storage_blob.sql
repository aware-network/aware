-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE storage_blob (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  bucket_id UUID,
  -- ATTRIBUTES
  mime_type TEXT NOT NULL,
  object_key TEXT,
  path_local TEXT,
  sha TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sha)
);
