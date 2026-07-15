-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE hub_publication_receipt (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  hub_authority_id UUID NOT NULL,
  artifact_revision_id UUID,
  code_package_publication_id UUID,
  -- ATTRIBUTES
  authority_source_url TEXT,
  detail JSONB NOT NULL,
  idempotency_key TEXT,
  message TEXT,
  operation TEXT NOT NULL,
  publisher_execution_id TEXT,
  receipt_key TEXT NOT NULL,
  recorded_at_utc TEXT,
  status hub_publication_receipt_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, hub_authority_id, receipt_key),
  FOREIGN KEY (branch_id, projection_hash, hub_authority_id) REFERENCES hub_authority(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, artifact_revision_id) REFERENCES hub_artifact_revision(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_package_publication_id) REFERENCES hub_code_package_publication(branch_id, projection_hash, id)
);
