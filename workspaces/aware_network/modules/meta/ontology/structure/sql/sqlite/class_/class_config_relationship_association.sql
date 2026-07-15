-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_config_relationship_association (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  class_config_id TEXT NOT NULL,
  class_config_relationship_id TEXT NOT NULL,
  -- ATTRIBUTES
  forward_loading_strategy TEXT,
  reverse_loading_strategy TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, class_config_id) REFERENCES class_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, class_config_relationship_id) REFERENCES class_config_relationship(branch_id, projection_hash, id)
);
