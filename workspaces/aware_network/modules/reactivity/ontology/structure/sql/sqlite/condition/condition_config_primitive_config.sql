-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition_config_primitive_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  condition_config_attribute_config_id TEXT UNIQUE,
  primitive_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  primitive_value TEXT NOT NULL,
  range_max TEXT,
  range_min TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, primitive_config_id),
  FOREIGN KEY (branch_id, projection_hash, condition_config_attribute_config_id) REFERENCES condition_config_attribute_config(branch_id, projection_hash, id)
);
