-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE hub_code_package_publication (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  hub_authority_id TEXT NOT NULL,
  artifact_revision_id TEXT,
  code_package_id TEXT,
  producer_provenance_id TEXT,
  -- ATTRIBUTES
  artifact_sha256 TEXT NOT NULL,
  artifact_size_bytes INTEGER,
  artifact_url TEXT NOT NULL,
  channel_key TEXT NOT NULL,
  descriptor_digest TEXT,
  download_handle TEXT,
  fqn_prefix TEXT,
  language TEXT NOT NULL,
  manifest_kind TEXT,
  manifest_relative_path TEXT,
  media_type TEXT,
  metadata TEXT NOT NULL,
  package_name TEXT NOT NULL,
  package_root TEXT,
  published_at_utc TEXT,
  revision_id TEXT NOT NULL,
  sources_root TEXT,
  surface TEXT NOT NULL,
  version TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, hub_authority_id, channel_key, language, package_name, revision_id, surface),
  FOREIGN KEY (branch_id, projection_hash, hub_authority_id) REFERENCES hub_authority(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, artifact_revision_id) REFERENCES hub_artifact_revision(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, producer_provenance_id) REFERENCES hub_producer_provenance(branch_id, projection_hash, id)
);
