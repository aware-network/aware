-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_graph_projection_experience_oigi (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_config_graph_id UUID NOT NULL,
  projection_experience_oigi_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_config_graph_id, projection_experience_oigi_id),
  FOREIGN KEY (branch_id, projection_hash, program_config_graph_id) REFERENCES program_config_graph(branch_id, projection_hash, id)
);
