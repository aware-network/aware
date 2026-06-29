-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  attribute_config_id UUID NOT NULL,
  value_root_id UUID NOT NULL,
  -- ATTRIBUTES
  owner_key UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, owner_key, attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, value_root_id) REFERENCES attribute_value(branch_id, projection_hash, id)
);
