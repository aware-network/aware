-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_graph_function (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  api_graph_id UUID NOT NULL,
  class_config_function_config_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_graph_id, class_config_function_config_id),
  FOREIGN KEY (branch_id, projection_hash, api_graph_id) REFERENCES api_graph(branch_id, projection_hash, id)
);
