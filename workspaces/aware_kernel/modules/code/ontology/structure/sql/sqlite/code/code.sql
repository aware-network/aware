-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  content_part_text_id TEXT NOT NULL,
  code_package_code_id TEXT NOT NULL UNIQUE,
  -- ATTRIBUTES
  relative_path TEXT NOT NULL,
  language TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, relative_path),
  FOREIGN KEY (branch_id, projection_hash, code_package_code_id) REFERENCES code_package_code(branch_id, projection_hash, id)
);
