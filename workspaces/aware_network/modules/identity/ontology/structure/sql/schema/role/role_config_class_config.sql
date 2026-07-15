-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE role_config_class_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  role_config_id UUID NOT NULL,
  class_config_id UUID NOT NULL,
  -- ATTRIBUTES
  access_level access_level_type NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, role_config_id, class_config_id),
  FOREIGN KEY (branch_id, projection_hash, role_config_id) REFERENCES role_config(branch_id, projection_hash, id)
);
