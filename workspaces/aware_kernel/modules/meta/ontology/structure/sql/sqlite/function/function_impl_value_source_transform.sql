-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_value_source_transform (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_impl_value_source_id TEXT UNIQUE,
  output_primitive_config_id TEXT,
  -- ATTRIBUTES
  operation TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_impl_value_source_id) REFERENCES function_impl_value_source(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, output_primitive_config_id) REFERENCES primitive_config(branch_id, projection_hash, id)
);
