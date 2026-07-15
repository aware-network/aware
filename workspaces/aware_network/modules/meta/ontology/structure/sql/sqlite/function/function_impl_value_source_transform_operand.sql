-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_value_source_transform_operand (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_impl_value_source_transform_id TEXT NOT NULL,
  value_source_id TEXT NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_impl_value_source_transform_id, position),
  FOREIGN KEY (branch_id, projection_hash, function_impl_value_source_transform_id) REFERENCES function_impl_value_source_transform(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, value_source_id) REFERENCES function_impl_value_source(branch_id, projection_hash, id)
);
