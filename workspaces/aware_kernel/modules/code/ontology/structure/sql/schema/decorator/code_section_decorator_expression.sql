-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_decorator_expression (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_decorator_id UUID NOT NULL,
  code_section_expression_id UUID NOT NULL,
  name_segment_id UUID,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_section_decorator_id, position),
  FOREIGN KEY (branch_id, projection_hash, code_section_decorator_id) REFERENCES code_section_decorator(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_expression_id) REFERENCES code_section_expression(branch_id, projection_hash, id)
);
