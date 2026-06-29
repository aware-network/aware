-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_id TEXT NOT NULL,
  content_part_text_segment_id TEXT NOT NULL,
  -- ATTRIBUTES
  identity_hash TEXT NOT NULL,
  metadata TEXT,
  qualname TEXT NOT NULL,
  section_key TEXT NOT NULL,
  type_ TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_id, section_key, type_),
  FOREIGN KEY (branch_id, projection_hash, code_id) REFERENCES code(branch_id, projection_hash, id)
);
