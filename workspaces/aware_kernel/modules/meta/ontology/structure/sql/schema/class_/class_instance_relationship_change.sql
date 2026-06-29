-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_instance_relationship_change (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  change_id UUID NOT NULL,
  class_config_relationship_id UUID NOT NULL,
  source_class_instance_id UUID NOT NULL,
  target_class_instance_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, change_id, class_config_relationship_id, source_class_instance_id, target_class_instance_id)
);
