-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  id TEXT NOT NULL,
  projection_hash TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  object_config_graph_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  language TEXT NOT NULL,
  name TEXT NOT NULL,
  supports_virtual_build INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, object_config_graph_id, name)
);
