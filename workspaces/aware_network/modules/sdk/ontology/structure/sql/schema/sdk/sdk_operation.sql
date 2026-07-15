-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_operation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  sdk_config_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  title TEXT,
  description TEXT,
  implementation_ref TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_config_id, name),
  FOREIGN KEY (branch_id, projection_hash, sdk_config_id) REFERENCES sdk_config(branch_id, projection_hash, id)
);
