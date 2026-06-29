-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_value_link_change (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attribute_value_link_id TEXT NOT NULL,
  attribute_value_change_id TEXT NOT NULL,
  change_id TEXT NOT NULL,
  child_attribute_value_change_id TEXT UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attribute_value_change_id, attribute_value_link_id, change_id)
);
