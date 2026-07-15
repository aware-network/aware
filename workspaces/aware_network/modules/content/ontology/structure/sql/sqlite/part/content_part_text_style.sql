-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_part_text_style (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  content_part_text_segment_id TEXT UNIQUE,
  -- ATTRIBUTES
  background_color TEXT,
  block_semantic_type TEXT,
  bold INTEGER,
  color TEXT,
  font_family TEXT,
  font_size INTEGER,
  italic INTEGER,
  underline INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, background_color, block_semantic_type, bold, color, font_family, font_size, italic, underline),
  FOREIGN KEY (branch_id, projection_hash, content_part_text_segment_id) REFERENCES content_part_text_segment(branch_id, projection_hash, id)
);
