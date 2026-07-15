-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_package_attention_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  experience_package_id TEXT NOT NULL,
  attention_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_package_id, attention_package_id),
  FOREIGN KEY (branch_id, projection_hash, experience_package_id) REFERENCES experience_package(branch_id, projection_hash, id)
);
