-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_instance_graph_change (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_identity_id UUID NOT NULL,
  object_instance_graph_id UUID NOT NULL,
  change_id UUID NOT NULL,
  -- ATTRIBUTES
  type_ object_instance_graph_change_type NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_identity_id, change_id)
);
