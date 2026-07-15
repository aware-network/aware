-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_package_content (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  content_id UUID NOT NULL,
  content_package_id UUID NOT NULL,
  -- ATTRIBUTES
  relative_path TEXT NOT NULL,
  content_role TEXT NOT NULL,
  position INTEGER,
  media_type TEXT,
  title TEXT,
  source_ref TEXT,
  provider_payload JSONB,
  receipt_payload JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, content_id, content_package_id, relative_path, content_role),
  FOREIGN KEY (branch_id, projection_hash, content_id) REFERENCES content(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, content_package_id) REFERENCES content_package(branch_id, projection_hash, id)
);
