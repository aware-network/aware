-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_value_source_read_path (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_impl_value_source_id TEXT UNIQUE,
  root_function_config_attribute_config_id TEXT,
  root_instruction_let_id TEXT,
  root_class_config_attribute_config_id TEXT,
  -- ATTRIBUTES
  root_kind TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id)
);
