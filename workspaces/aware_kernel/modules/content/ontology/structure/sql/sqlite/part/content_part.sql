-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_part (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  content_part_content_id TEXT NOT NULL UNIQUE,
  -- ATTRIBUTES
  type_ TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, type_),
  FOREIGN KEY (branch_id, projection_hash, content_part_content_id) REFERENCES content_part_content(branch_id, projection_hash, id)
);
