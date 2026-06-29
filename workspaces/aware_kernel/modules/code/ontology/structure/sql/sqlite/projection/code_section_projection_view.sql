-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_projection_view (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_projection_id TEXT NOT NULL,
  key_segment_id TEXT NOT NULL,
  body_segment_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  kind TEXT NOT NULL,
  is_default INTEGER NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_projection_id) REFERENCES code_section_projection(branch_id, projection_hash, id)
);
