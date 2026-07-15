-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_binding_formula_segment_reference (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_binding_formula_id UUID NOT NULL,
  content_part_text_segment_id UUID NOT NULL,
  source_class_config_attribute_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_binding_formula_id, content_part_text_segment_id, source_class_config_attribute_config_id)
);
