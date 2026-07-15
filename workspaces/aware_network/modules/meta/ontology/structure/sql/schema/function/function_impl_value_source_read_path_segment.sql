-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_value_source_read_path_segment (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_value_source_read_path_id UUID NOT NULL,
  attribute_config_id UUID NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_impl_value_source_read_path_id, position)
);
