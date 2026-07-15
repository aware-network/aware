-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_chain_section (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  content_chain_id TEXT UNIQUE,
  newest_content_chain_content_id TEXT,
  oldest_content_chain_content_id TEXT,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key),
  FOREIGN KEY (branch_id, projection_hash, content_chain_id) REFERENCES content_chain(branch_id, projection_hash, id)
);
