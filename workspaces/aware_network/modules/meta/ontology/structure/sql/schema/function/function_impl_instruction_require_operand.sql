-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_instruction_require_operand (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_instruction_require_id UUID NOT NULL,
  value_source_id UUID NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_impl_instruction_require_id, position),
  FOREIGN KEY (branch_id, projection_hash, function_impl_instruction_require_id) REFERENCES function_impl_instruction_require(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, value_source_id) REFERENCES function_impl_value_source(branch_id, projection_hash, id)
);
