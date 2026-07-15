-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node_member (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  network_node_id TEXT NOT NULL,
  -- ATTRIBUTES
  identity_id TEXT NOT NULL,
  is_primary INTEGER NOT NULL,
  last_sync_at TEXT NOT NULL,
  managed_since TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, network_node_id, identity_id)
);
