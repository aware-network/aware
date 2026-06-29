-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  content_part_text_id UUID NOT NULL,
  code_package_code_id UUID NOT NULL UNIQUE,
  -- ATTRIBUTES
  relative_path TEXT NOT NULL,
  language code_language,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, relative_path),
  FOREIGN KEY (branch_id, projection_hash, code_package_code_id) REFERENCES code_package_code(branch_id, projection_hash, id)
);
