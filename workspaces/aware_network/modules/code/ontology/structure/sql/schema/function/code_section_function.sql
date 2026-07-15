-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_function (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_id UUID UNIQUE,
  name_segment_id UUID,
  body_segment_id UUID,
  signature_segment_id UUID NOT NULL,
  return_type_segment_id UUID,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  is_async BOOLEAN NOT NULL,
  is_public BOOLEAN NOT NULL,
  is_static BOOLEAN NOT NULL,
  is_classmethod BOOLEAN NOT NULL,
  verb TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
