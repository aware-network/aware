-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_class_base (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_class_id TEXT NOT NULL,
  segment_id TEXT,
  -- ATTRIBUTES
  base_ref TEXT NOT NULL,
  is_augment INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_section_class_id, base_ref),
  FOREIGN KEY (branch_id, projection_hash, code_section_class_id) REFERENCES code_section_class(branch_id, projection_hash, id)
);
