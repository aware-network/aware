-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_value_source_literal_primitive (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_value_source_id UUID UNIQUE,
  primitive_config_id UUID NOT NULL,
  -- ATTRIBUTES
  value JSONB NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_impl_value_source_id) REFERENCES function_impl_value_source(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, primitive_config_id) REFERENCES primitive_config(branch_id, projection_hash, id)
);
