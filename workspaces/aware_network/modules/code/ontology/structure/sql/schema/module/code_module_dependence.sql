-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_module_dependence (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_module_id UUID NOT NULL,
  dependence_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_module_id, name),
  FOREIGN KEY (branch_id, projection_hash, code_module_id) REFERENCES code_module(branch_id, projection_hash, id)
);
