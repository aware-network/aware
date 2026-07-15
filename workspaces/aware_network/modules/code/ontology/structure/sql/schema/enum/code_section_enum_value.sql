-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_enum_value (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_enum_id UUID NOT NULL,
  code_section_id UUID UNIQUE,
  value_segment_id UUID NOT NULL,
  -- ATTRIBUTES
  value TEXT NOT NULL,
  description TEXT,
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_section_enum_id, value),
  FOREIGN KEY (branch_id, projection_hash, code_section_enum_id) REFERENCES code_section_enum(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
