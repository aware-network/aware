-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_value_source_read_path (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_value_source_id UUID UNIQUE,
  root_function_config_attribute_config_id UUID,
  root_instruction_let_id UUID,
  root_class_config_attribute_config_id UUID,
  -- ATTRIBUTES
  root_kind function_impl_value_source_read_path_root_kind NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id)
);
