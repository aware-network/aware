-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_package_sdk_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  experience_package_id UUID NOT NULL,
  sdk_package_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_package_id, sdk_package_id),
  FOREIGN KEY (branch_id, projection_hash, experience_package_id) REFERENCES experience_package(branch_id, projection_hash, id)
);
