-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_part_text_segment_translation (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  content_part_text_segment_id TEXT NOT NULL,
  -- ATTRIBUTES
  language TEXT NOT NULL,
  text TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, content_part_text_segment_id, language),
  FOREIGN KEY (branch_id, projection_hash, content_part_text_segment_id) REFERENCES content_part_text_segment(branch_id, projection_hash, id)
);
