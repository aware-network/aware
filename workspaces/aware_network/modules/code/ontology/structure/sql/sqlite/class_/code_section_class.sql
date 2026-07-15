-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_class (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_id TEXT UNIQUE,
  name_segment_id TEXT NOT NULL,
  keyword_segment_id TEXT,
  modifiers_segment_id TEXT,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  verb TEXT,
  verb_target TEXT,
  is_edge INTEGER NOT NULL,
  is_inline_value INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
