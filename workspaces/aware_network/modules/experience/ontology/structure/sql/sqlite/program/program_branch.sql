-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_branch (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_id TEXT NOT NULL,
  object_instance_graph_branch_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  is_active INTEGER NOT NULL,
  view_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_id, object_instance_graph_branch_id),
  FOREIGN KEY (branch_id, projection_hash, program_id) REFERENCES program(branch_id, projection_hash, id)
);
