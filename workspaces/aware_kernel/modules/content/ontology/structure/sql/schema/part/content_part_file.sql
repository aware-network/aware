-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_part_file (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  storage_blob_id UUID NOT NULL,
  content_part_id UUID NOT NULL,
  -- ATTRIBUTES
  inline_data BYTEA,
  mime_type TEXT NOT NULL,
  modality_type modality_type NOT NULL,
  provider_id TEXT,
  raw_path TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, modality_type),
  FOREIGN KEY (branch_id, projection_hash, content_part_id) REFERENCES content_part(branch_id, projection_hash, id)
);
