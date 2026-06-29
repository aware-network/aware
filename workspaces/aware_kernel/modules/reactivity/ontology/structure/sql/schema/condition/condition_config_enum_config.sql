-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition_config_enum_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  condition_config_attribute_config_id UUID UNIQUE,
  enum_config_id UUID NOT NULL,
  -- ATTRIBUTES
  match_mode enum_match_mode NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, enum_config_id),
  FOREIGN KEY (branch_id, projection_hash, condition_config_attribute_config_id) REFERENCES condition_config_attribute_config(branch_id, projection_hash, id)
);
