-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_class_base (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_class_id UUID NOT NULL,
  segment_id UUID,
  -- ATTRIBUTES
  base_ref TEXT NOT NULL,
  is_augment BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_section_class_id, base_ref),
  FOREIGN KEY (branch_id, projection_hash, code_section_class_id) REFERENCES code_section_class(branch_id, projection_hash, id)
);
