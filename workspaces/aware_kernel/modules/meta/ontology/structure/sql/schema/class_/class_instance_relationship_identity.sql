-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_instance_relationship_identity (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_identity_id UUID NOT NULL,
  class_instance_relationship_id UUID NOT NULL,
  -- ATTRIBUTES
  label TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_identity_id, class_instance_relationship_id),
  FOREIGN KEY (branch_id, projection_hash, object_instance_graph_identity_id) REFERENCES object_instance_graph_identity(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, class_instance_relationship_id) REFERENCES class_instance_relationship(branch_id, projection_hash, id)
);
