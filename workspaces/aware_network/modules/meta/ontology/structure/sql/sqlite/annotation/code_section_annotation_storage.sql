-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_annotation_storage (
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
  name TEXT NOT NULL,
  operation TEXT NOT NULL,
  member_names TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, fqn_prefix, namespace, class_name, name, operation)
);
