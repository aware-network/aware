-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_projection (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_id UUID UNIQUE,
  name_segment_id UUID NOT NULL,
  root_type_segment_id UUID,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  projection_name TEXT NOT NULL,
  label TEXT,
  is_branchable BOOLEAN NOT NULL,
  root_type_ref TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
