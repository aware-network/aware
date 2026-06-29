-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_attribute (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_id TEXT UNIQUE,
  name_segment_id TEXT,
  default_value_segment_id TEXT,
  type_segment_id TEXT,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  type_text TEXT,
  default_value_text TEXT,
  is_required INTEGER NOT NULL,
  is_public INTEGER NOT NULL,
  is_unique INTEGER NOT NULL,
  is_primary INTEGER NOT NULL,
  is_many_to_many INTEGER NOT NULL,
  edge_spec_name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
