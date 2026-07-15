-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE hub_producer_provenance (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- ATTRIBUTES
  build_ref TEXT,
  materialization_ref TEXT,
  metadata JSONB NOT NULL,
  producer_key TEXT NOT NULL,
  producer_kind TEXT NOT NULL,
  producer_revision_id TEXT,
  provenance_key TEXT NOT NULL,
  source_revision_id TEXT,
  source_revision_kind TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, producer_key, producer_kind, provenance_key)
);
