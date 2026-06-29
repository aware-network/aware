-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_mirror (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_id UUID NOT NULL,
  source_object_config_graph_id UUID NOT NULL,
  class_config_id UUID,
  enum_config_id UUID,
  code_section_mirror_id UUID NOT NULL,
  -- ATTRIBUTES
  fqn_prefix TEXT NOT NULL,
  namespace TEXT NOT NULL,
  target_text TEXT NOT NULL,
  layout_kind TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  source_position INTEGER,
  target_kind object_config_graph_mirror_target_kind NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_id, fqn_prefix, namespace, target_text, layout_kind, relative_path, target_kind, source_object_config_graph_id, code_section_mirror_id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_id) REFERENCES object_config_graph(branch_id, projection_hash, id)
);
