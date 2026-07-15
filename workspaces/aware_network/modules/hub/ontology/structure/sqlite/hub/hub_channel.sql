-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE hub_channel (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  channel_key TEXT NOT NULL,
  -- RELATIONSHIPS
  hub_authority_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  title TEXT,
  visibility TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, channel_key),
  FOREIGN KEY (branch_id, projection_hash, hub_authority_id) REFERENCES hub_authority(branch_id, projection_hash, id)
);

CREATE TABLE hub_channel_head (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  artifact_family TEXT NOT NULL,
  artifact_key TEXT NOT NULL,
  -- RELATIONSHIPS
  hub_channel_id TEXT NOT NULL,
  artifact_revision_id TEXT,
  code_package_publication_id TEXT,
  -- ATTRIBUTES
  revision_id TEXT NOT NULL,
  selector_key TEXT,
  updated_at_utc TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, artifact_family, artifact_key),
  FOREIGN KEY (branch_id, projection_hash, hub_channel_id) REFERENCES hub_channel(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, artifact_revision_id) REFERENCES hub_artifact_revision(branch_id, projection_hash, id)
);
