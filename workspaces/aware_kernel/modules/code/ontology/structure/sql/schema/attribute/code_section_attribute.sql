-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_attribute (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_id UUID UNIQUE,
  name_segment_id UUID,
  default_value_segment_id UUID,
  type_segment_id UUID,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  type_text TEXT,
  default_value_text TEXT,
  is_required BOOLEAN NOT NULL,
  is_public BOOLEAN NOT NULL,
  is_unique BOOLEAN NOT NULL,
  is_primary BOOLEAN NOT NULL,
  is_many_to_many BOOLEAN NOT NULL,
  edge_spec_name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
