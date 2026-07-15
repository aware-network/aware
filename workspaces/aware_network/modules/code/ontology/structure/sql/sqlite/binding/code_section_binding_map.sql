-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_binding_map (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_binding_id TEXT NOT NULL,
  name_segment_id TEXT NOT NULL,
  source_segment_id TEXT NOT NULL,
  target_segment_id TEXT NOT NULL,
  body_segment_id TEXT,
  template_segment_id TEXT,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  description TEXT,
  template_text TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_section_binding_id, name)
);
