-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_index (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  content_id UUID UNIQUE,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  content_embedding TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key),
  FOREIGN KEY (branch_id, projection_hash, content_id) REFERENCES content(branch_id, projection_hash, id)
);
