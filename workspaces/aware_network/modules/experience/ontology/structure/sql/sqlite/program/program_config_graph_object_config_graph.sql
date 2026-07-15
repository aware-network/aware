-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_graph_object_config_graph (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_config_graph_id TEXT NOT NULL,
  object_config_graph_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_config_graph_id, object_config_graph_id),
  FOREIGN KEY (branch_id, projection_hash, program_config_graph_id) REFERENCES program_config_graph(branch_id, projection_hash, id)
);
