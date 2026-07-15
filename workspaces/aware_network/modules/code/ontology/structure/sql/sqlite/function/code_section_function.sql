-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_function (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_id TEXT UNIQUE,
  name_segment_id TEXT,
  body_segment_id TEXT,
  signature_segment_id TEXT NOT NULL,
  return_type_segment_id TEXT,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  is_async INTEGER NOT NULL,
  is_public INTEGER NOT NULL,
  is_static INTEGER NOT NULL,
  is_classmethod INTEGER NOT NULL,
  verb TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
