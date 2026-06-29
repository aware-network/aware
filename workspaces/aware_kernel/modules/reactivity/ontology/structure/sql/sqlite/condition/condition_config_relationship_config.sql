-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition_config_relationship_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  condition_config_attribute_config_id TEXT UNIQUE,
  nested_condition_config_id TEXT,
  class_config_relationship_id TEXT NOT NULL,
  -- ATTRIBUTES
  count_threshold INTEGER,
  eval_mode TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_config_relationship_id),
  FOREIGN KEY (branch_id, projection_hash, condition_config_attribute_config_id) REFERENCES condition_config_attribute_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, nested_condition_config_id) REFERENCES condition_config(branch_id, projection_hash, id)
);
