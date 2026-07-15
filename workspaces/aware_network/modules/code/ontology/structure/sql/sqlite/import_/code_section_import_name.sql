-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_import_name (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_import_id TEXT NOT NULL,
  name_segment_id TEXT NOT NULL,
  alias_segment_id TEXT,
  -- ATTRIBUTES
  name_text TEXT NOT NULL,
  alias_text TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_section_import_id, name_text),
  FOREIGN KEY (branch_id, projection_hash, code_section_import_id) REFERENCES code_section_import(branch_id, projection_hash, id)
);
