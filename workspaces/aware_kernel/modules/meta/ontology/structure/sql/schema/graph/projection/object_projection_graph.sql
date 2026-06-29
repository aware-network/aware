-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  id UUID NOT NULL,
  projection_hash TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  object_config_graph_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  language code_language NOT NULL,
  name TEXT NOT NULL,
  supports_virtual_build BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, object_config_graph_id, name)
);
