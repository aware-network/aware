-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  config_id TEXT,
  system_actor_id TEXT,
  -- ATTRIBUTES
  base_url TEXT,
  hostname TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  port INTEGER NOT NULL,
  public_key TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, public_key)
);
