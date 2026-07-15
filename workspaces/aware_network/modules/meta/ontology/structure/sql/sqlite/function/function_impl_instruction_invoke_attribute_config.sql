-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_instruction_invoke_attribute_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_impl_instruction_invoke_id TEXT NOT NULL,
  attribute_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  value_expr TEXT NOT NULL,
  position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_impl_instruction_invoke_id, attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, function_impl_instruction_invoke_id) REFERENCES function_impl_instruction_invoke(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, attribute_config_id) REFERENCES attribute_config(branch_id, projection_hash, id)
);
