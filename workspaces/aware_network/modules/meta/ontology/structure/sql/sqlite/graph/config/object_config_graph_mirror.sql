-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_mirror (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_id TEXT NOT NULL,
  source_object_config_graph_id TEXT NOT NULL,
  class_config_id TEXT,
  enum_config_id TEXT,
  code_section_mirror_id TEXT NOT NULL,
  -- ATTRIBUTES
  fqn_prefix TEXT NOT NULL,
  namespace TEXT NOT NULL,
  target_text TEXT NOT NULL,
  layout_kind TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  source_position INTEGER,
  target_kind TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_id, fqn_prefix, namespace, target_text, layout_kind, relative_path, target_kind, source_object_config_graph_id, code_section_mirror_id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_id) REFERENCES object_config_graph(branch_id, projection_hash, id)
);
