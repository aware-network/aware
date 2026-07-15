-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_branch (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  object_instance_graph_branch_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  is_active BOOLEAN NOT NULL,
  view_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, object_instance_graph_branch_id),
  FOREIGN KEY (branch_id, projection_hash, program_id) REFERENCES program(branch_id, projection_hash, id)
);
