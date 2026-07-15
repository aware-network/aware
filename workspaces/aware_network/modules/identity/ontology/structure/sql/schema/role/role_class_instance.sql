-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE role_class_instance (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  role_id UUID NOT NULL,
  class_instance_identity_id UUID NOT NULL,
  role_config_class_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, role_id, class_instance_identity_id, role_config_class_config_id),
  FOREIGN KEY (branch_id, projection_hash, role_id) REFERENCES role(branch_id, projection_hash, id)
);
