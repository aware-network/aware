-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_graph (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  api_id UUID NOT NULL,
  object_config_graph_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_id, object_config_graph_id),
  FOREIGN KEY (branch_id, projection_hash, api_id) REFERENCES api(branch_id, projection_hash, id)
);
