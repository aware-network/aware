-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_annotation_reference (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_annotation_id TEXT,
  -- ATTRIBUTES
  fqn_prefix TEXT NOT NULL,
  namespace TEXT NOT NULL,
  class_name TEXT NOT NULL,
  attribute_name TEXT NOT NULL,
  mode TEXT NOT NULL,
  target_fqn_prefix TEXT,
  target_namespace TEXT,
  target_class_name TEXT,
  target_attribute_name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, fqn_prefix, namespace, class_name, attribute_name, mode)
);
