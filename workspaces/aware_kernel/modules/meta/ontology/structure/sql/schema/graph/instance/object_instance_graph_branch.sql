-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_instance_graph_branch (
  -- PRIMARY KEY
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  branch_id UUID NOT NULL UNIQUE,
  -- RELATIONSHIPS
  object_instance_graph_identity_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (projection_hash, id, branch_id),
  FOREIGN KEY (branch_id, projection_hash, object_instance_graph_identity_id) REFERENCES object_instance_graph_identity(branch_id, projection_hash, id)
);
