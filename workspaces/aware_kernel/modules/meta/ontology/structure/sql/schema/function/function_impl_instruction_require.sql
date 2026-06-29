-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_instruction_require (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_instruction_id UUID UNIQUE,
  -- ATTRIBUTES
  kind function_impl_require_kind NOT NULL,
  compare_operator function_impl_require_compare_operator,
  expected_count INTEGER,
  message TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_impl_instruction_id) REFERENCES function_impl_instruction(branch_id, projection_hash, id)
);
