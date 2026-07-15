-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_identity (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  interface_id TEXT NOT NULL,
  identity_id TEXT NOT NULL,
  -- ATTRIBUTES
  linked_at TEXT NOT NULL,
  last_confirmed_at TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, interface_id, identity_id)
);
