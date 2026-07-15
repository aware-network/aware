-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_node_class_identity (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  projection_experience_node_identity_id TEXT NOT NULL,
  class_instance_identity_id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_oigi_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key, projection_experience_node_identity_id, class_instance_identity_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_oigi_id) REFERENCES projection_experience_oigi(branch_id, projection_hash, id)
);
