-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_change (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  class_instance_change_id TEXT NOT NULL,
  attribute_id TEXT NOT NULL,
  change_id TEXT NOT NULL,
  value_root_change_id TEXT UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_instance_change_id, attribute_id, change_id)
);
