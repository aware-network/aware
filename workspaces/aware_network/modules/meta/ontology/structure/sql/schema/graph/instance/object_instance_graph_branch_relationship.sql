-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_instance_graph_branch_relationship (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_branch_id UUID NOT NULL,
  target_object_instance_graph_branch_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_branch_id, target_object_instance_graph_branch_id),
  FOREIGN KEY (branch_id, projection_hash, object_instance_graph_branch_id) REFERENCES object_instance_graph_branch(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, target_object_instance_graph_branch_id) REFERENCES object_instance_graph_branch(branch_id, projection_hash, id)
);
