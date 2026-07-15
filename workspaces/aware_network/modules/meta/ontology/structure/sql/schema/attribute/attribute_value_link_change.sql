-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_value_link_change (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  attribute_value_link_id UUID NOT NULL,
  attribute_value_change_id UUID NOT NULL,
  change_id UUID NOT NULL,
  child_attribute_value_change_id UUID UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attribute_value_change_id, attribute_value_link_id, change_id)
);
