-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_package_artifact (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  content_package_id UUID NOT NULL,
  -- ATTRIBUTES
  output_key TEXT NOT NULL,
  artifact_key TEXT NOT NULL,
  status content_package_artifact_status NOT NULL,
  artifact_family TEXT,
  artifact_role TEXT,
  required_for TEXT[] NOT NULL,
  producer_provider_key TEXT,
  producer_key TEXT,
  producer_kind TEXT,
  materialization_index INTEGER,
  source_content_package_id UUID,
  source_object_instance_graph_commit_id UUID,
  input_content_package_id UUID,
  input_object_instance_graph_commit_id UUID,
  digest TEXT,
  digest_algorithm TEXT,
  relative_path TEXT,
  uri TEXT,
  media_type TEXT,
  size_bytes INTEGER,
  runtime_contract_version TEXT,
  provider_payload JSONB,
  receipt_payload JSONB,
  error TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, content_package_id, output_key, artifact_key),
  FOREIGN KEY (branch_id, projection_hash, content_package_id) REFERENCES content_package(branch_id, projection_hash, id)
);
