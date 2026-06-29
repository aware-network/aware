-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_function_attribute (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_attribute_id TEXT NOT NULL,
  code_section_function_id TEXT NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  is_output INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_attribute_id) REFERENCES code_section_attribute(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_function_id) REFERENCES code_section_function(branch_id, projection_hash, id)
);
