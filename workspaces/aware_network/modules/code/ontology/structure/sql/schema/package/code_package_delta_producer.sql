-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_delta_producer (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_package_id UUID NOT NULL,
  -- ATTRIBUTES
  provider_key TEXT NOT NULL,
  producer_key TEXT NOT NULL,
  producer_kind TEXT,
  provider_payload JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_id, provider_key, producer_key)
);
