-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_part_text_segment (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  content_part_text_id UUID NOT NULL,
  parent_id UUID,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  byte_end INTEGER,
  byte_start INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, content_part_text_id, key),
  FOREIGN KEY (branch_id, projection_hash, content_part_text_id) REFERENCES content_part_text(branch_id, projection_hash, id)
);
