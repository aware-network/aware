-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_object_instance_graph_branch (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  thread_id UUID NOT NULL,
  object_instance_graph_branch_id UUID NOT NULL,
  object_instance_graph_identity_id UUID,
  -- ATTRIBUTES
  is_active BOOLEAN NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, thread_id, object_instance_graph_branch_id),
  FOREIGN KEY (branch_id, projection_hash, thread_id) REFERENCES thread(branch_id, projection_hash, id)
);
