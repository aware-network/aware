-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_class (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_id UUID UNIQUE,
  name_segment_id UUID NOT NULL,
  keyword_segment_id UUID,
  modifiers_segment_id UUID,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  verb TEXT,
  verb_target TEXT,
  is_edge BOOLEAN NOT NULL,
  is_inline_value BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
