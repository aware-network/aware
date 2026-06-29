-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_value_source (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_impl_instruction_id TEXT NOT NULL,
  source_function_config_attribute_config_id TEXT,
  source_instruction_let_id TEXT,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  kind TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_impl_instruction_id, key),
  FOREIGN KEY (branch_id, projection_hash, function_impl_instruction_id) REFERENCES function_impl_instruction(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, source_function_config_attribute_config_id) REFERENCES function_config_attribute_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, source_instruction_let_id) REFERENCES function_impl_instruction_let(branch_id, projection_hash, id)
);
