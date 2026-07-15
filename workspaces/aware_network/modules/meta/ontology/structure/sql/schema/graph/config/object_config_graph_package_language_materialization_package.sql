-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_package_language_materialization_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_package_language_materialization_id UUID NOT NULL,
  code_package_id UUID NOT NULL,
  -- ATTRIBUTES
  package_output_key TEXT NOT NULL,
  package_name TEXT NOT NULL,
  language code_language NOT NULL,
  output_dir TEXT NOT NULL,
  package_root TEXT NOT NULL,
  sources_root TEXT,
  import_root TEXT,
  materialization_source TEXT NOT NULL,
  renderer_kind TEXT,
  renderer_profile TEXT,
  object_config_graph_object_instance_graph_commit_id UUID,
  code_package_object_instance_graph_commit_id UUID,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_package_language_materialization_id, code_package_id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_package_language_materialization_id) REFERENCES object_config_graph_package_language_materialization(branch_id, projection_hash, id)
);
