-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_package_language_materialization (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  target_key TEXT NOT NULL,
  role TEXT NOT NULL,
  language TEXT NOT NULL,
  output_dir TEXT NOT NULL,
  import_root TEXT NOT NULL,
  package_name TEXT NOT NULL,
  materialization_source TEXT NOT NULL,
  renderer_kind TEXT,
  renderer_profile TEXT,
  stable_ids_import_root TEXT,
  source_is_runtime INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_package_id, target_key),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_package_id) REFERENCES object_config_graph_package(branch_id, projection_hash, id)
);
