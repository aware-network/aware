-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_config_overlay (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_config_id TEXT NOT NULL,
  object_config_graph_overlay_id TEXT NOT NULL,
  -- ATTRIBUTES
  rendered_name TEXT,
  lang_flags TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_config_id) REFERENCES function_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_overlay_id) REFERENCES object_config_graph_overlay(branch_id, projection_hash, id)
);
