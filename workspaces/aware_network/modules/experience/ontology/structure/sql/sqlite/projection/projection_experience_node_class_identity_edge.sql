-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_node_class_identity_edge (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_oigi_id TEXT NOT NULL,
  child_node_class_identity_id TEXT NOT NULL,
  parent_node_class_identity_id TEXT NOT NULL,
  class_instance_relationship_identity_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_oigi_id, child_node_class_identity_id, parent_node_class_identity_id, class_instance_relationship_identity_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_oigi_id) REFERENCES projection_experience_oigi(branch_id, projection_hash, id)
);
