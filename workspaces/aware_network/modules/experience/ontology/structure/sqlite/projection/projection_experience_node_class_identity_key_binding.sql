-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_node_class_identity_key_binding (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  projection_experience_node_key_id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_node_class_identity_id TEXT NOT NULL,
  -- ATTRIBUTES
  value TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, projection_experience_node_key_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_node_class_identity_id) REFERENCES projection_experience_node_class_identity(branch_id, projection_hash, id)
);
