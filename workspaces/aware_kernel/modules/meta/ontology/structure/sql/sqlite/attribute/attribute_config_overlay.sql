-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_config_overlay (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attribute_config_id TEXT NOT NULL,
  object_config_graph_overlay_id TEXT NOT NULL,
  -- ATTRIBUTES
  rendered_name TEXT,
  wire_name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, attribute_config_id) REFERENCES attribute_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_overlay_id) REFERENCES object_config_graph_overlay(branch_id, projection_hash, id)
);
