-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition_config_enum_option (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  condition_config_enum_config_id TEXT NOT NULL,
  enum_option_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, condition_config_enum_config_id, enum_option_id),
  FOREIGN KEY (branch_id, projection_hash, condition_config_enum_config_id) REFERENCES condition_config_enum_config(branch_id, projection_hash, id)
);
