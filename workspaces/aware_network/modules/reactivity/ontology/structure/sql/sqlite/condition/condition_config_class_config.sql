-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition_config_class_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  condition_config_id TEXT NOT NULL,
  class_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  class_logic TEXT NOT NULL,
  class_selection TEXT NOT NULL,
  require_existence INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, condition_config_id, class_config_id),
  FOREIGN KEY (branch_id, projection_hash, condition_config_id) REFERENCES condition_config(branch_id, projection_hash, id)
);
