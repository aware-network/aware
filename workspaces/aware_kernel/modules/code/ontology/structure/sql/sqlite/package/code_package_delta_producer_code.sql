-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_delta_producer_code (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_package_code_id TEXT NOT NULL,
  code_package_delta_producer_id TEXT NOT NULL,
  -- ATTRIBUTES
  input_code_package_id TEXT,
  input_object_instance_graph_commit_id TEXT,
  input_digest TEXT,
  output_digest TEXT,
  emission_payload TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id)
);
