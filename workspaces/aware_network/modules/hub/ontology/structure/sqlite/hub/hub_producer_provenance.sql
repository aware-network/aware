-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE hub_producer_provenance (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  producer_key TEXT NOT NULL,
  producer_kind TEXT NOT NULL,
  provenance_key TEXT NOT NULL,
  -- ATTRIBUTES
  build_ref TEXT,
  materialization_ref TEXT,
  metadata TEXT NOT NULL,
  producer_revision_id TEXT,
  source_revision_id TEXT,
  source_revision_kind TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, producer_key, producer_kind, provenance_key)
);
