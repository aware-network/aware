-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_annotation_load (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_annotation_id UUID,
  -- ATTRIBUTES
  fqn_prefix TEXT NOT NULL,
  namespace TEXT NOT NULL,
  class_name TEXT NOT NULL,
  attribute_name TEXT NOT NULL,
  edge_name TEXT,
  forward_strategy class_config_relationship_side_loading_strategy,
  reverse_strategy class_config_relationship_side_loading_strategy,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, fqn_prefix, namespace, class_name, attribute_name)
);
