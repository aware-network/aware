-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_comment (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_enum_id TEXT,
  code_section_expression_id TEXT,
  code_section_projection_id TEXT,
  code_section_attribute_id TEXT,
  code_section_enum_value_id TEXT,
  code_section_class_id TEXT,
  code_section_function_id TEXT,
  code_section_id TEXT UNIQUE,
  -- ATTRIBUTES
  type_ TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_enum_id) REFERENCES code_section_enum(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_projection_id) REFERENCES code_section_projection(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_attribute_id) REFERENCES code_section_attribute(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_enum_value_id) REFERENCES code_section_enum_value(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_class_id) REFERENCES code_section_class(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_function_id) REFERENCES code_section_function(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
