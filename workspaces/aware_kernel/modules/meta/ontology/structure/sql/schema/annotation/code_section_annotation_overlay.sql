-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_annotation_overlay (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_annotation_id UUID,
  -- ATTRIBUTES
  source_path TEXT NOT NULL,
  language code_language NOT NULL,
  entity code_section_annotation_overlay_entity NOT NULL,
  fqn_prefix TEXT NOT NULL,
  namespace TEXT NOT NULL,
  class_name TEXT,
  attribute_name TEXT,
  enum_name TEXT,
  enum_option_name TEXT,
  function_name TEXT,
  rename TEXT,
  wire_name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, source_path, language, entity, fqn_prefix, namespace)
);
