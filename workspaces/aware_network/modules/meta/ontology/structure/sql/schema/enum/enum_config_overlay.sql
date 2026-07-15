-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE enum_config_overlay (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  enum_config_id UUID NOT NULL,
  object_config_graph_overlay_id UUID NOT NULL,
  -- ATTRIBUTES
  rendered_name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, enum_config_id) REFERENCES enum_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_overlay_id) REFERENCES object_config_graph_overlay(branch_id, projection_hash, id)
);
