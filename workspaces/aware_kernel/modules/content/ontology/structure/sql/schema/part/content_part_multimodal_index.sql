-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_part_multimodal_index (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  content_part_id UUID UNIQUE,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  embedding TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key),
  FOREIGN KEY (branch_id, projection_hash, content_part_id) REFERENCES content_part(branch_id, projection_hash, id)
);
