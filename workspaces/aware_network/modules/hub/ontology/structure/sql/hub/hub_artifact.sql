-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE hub_artifact (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  artifact_family TEXT NOT NULL,
  artifact_key TEXT NOT NULL,
  -- RELATIONSHIPS
  hub_authority_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  media_type TEXT,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, artifact_family, artifact_key)
);

CREATE TABLE hub_artifact_revision (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  revision_id TEXT NOT NULL,
  -- RELATIONSHIPS
  hub_artifact_id UUID NOT NULL,
  producer_provenance_id UUID UNIQUE,
  -- ATTRIBUTES
  metadata JSONB NOT NULL,
  media_type TEXT,
  payload_sha256 TEXT NOT NULL,
  payload_url TEXT NOT NULL,
  published_at_utc TEXT,
  selector_key TEXT,
  size_bytes INTEGER,
  status hub_artifact_status NOT NULL,
  target_ref TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, revision_id),
  FOREIGN KEY (branch_id, projection_hash, producer_provenance_id) REFERENCES hub_producer_provenance(branch_id, projection_hash, id)
);
