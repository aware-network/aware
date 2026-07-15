-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_annotation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_id UUID UNIQUE,
  -- ATTRIBUTES
  path TEXT NOT NULL,
  verb TEXT NOT NULL,
  args TEXT[] NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
