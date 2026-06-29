-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_delta_producer_code (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_package_code_id UUID NOT NULL,
  code_package_delta_producer_id UUID NOT NULL,
  -- ATTRIBUTES
  input_code_package_id UUID,
  input_object_instance_graph_commit_id UUID,
  input_digest TEXT,
  output_digest TEXT,
  emission_payload JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id)
);
