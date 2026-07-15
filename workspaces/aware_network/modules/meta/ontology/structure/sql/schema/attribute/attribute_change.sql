-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_change (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  class_instance_change_id UUID NOT NULL,
  attribute_id UUID NOT NULL,
  change_id UUID NOT NULL,
  value_root_change_id UUID UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_instance_change_id, attribute_id, change_id)
);
