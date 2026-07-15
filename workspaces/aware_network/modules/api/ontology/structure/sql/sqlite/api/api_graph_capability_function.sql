-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_graph_capability_function (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  api_graph_capability_id TEXT NOT NULL,
  api_graph_function_id TEXT NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_graph_capability_id, name, api_graph_function_id),
  FOREIGN KEY (branch_id, projection_hash, api_graph_capability_id) REFERENCES api_graph_capability(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, api_graph_function_id) REFERENCES api_graph_function(branch_id, projection_hash, id)
);
