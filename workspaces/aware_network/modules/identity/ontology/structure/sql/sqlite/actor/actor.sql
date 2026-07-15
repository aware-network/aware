-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  identity_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  type_ TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key, identity_id),
  FOREIGN KEY (branch_id, projection_hash, identity_id) REFERENCES identity(branch_id, projection_hash, id)
);
