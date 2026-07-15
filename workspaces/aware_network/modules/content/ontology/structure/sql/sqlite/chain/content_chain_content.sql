-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_chain_content (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  content_id TEXT NOT NULL,
  content_chain_id TEXT NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, content_id, content_chain_id, position),
  FOREIGN KEY (branch_id, projection_hash, content_id) REFERENCES content(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, content_chain_id) REFERENCES content_chain(branch_id, projection_hash, id)
);
