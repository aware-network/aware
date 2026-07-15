-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_input_attribute (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  config_id UUID NOT NULL,
  attribute_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, config_id, attribute_id)
);
