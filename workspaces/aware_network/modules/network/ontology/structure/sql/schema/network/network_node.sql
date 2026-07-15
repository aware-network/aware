-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  config_id UUID,
  system_actor_id UUID,
  -- ATTRIBUTES
  base_url TEXT,
  hostname TEXT NOT NULL,
  last_seen_at TIMESTAMPTZ NOT NULL,
  port INTEGER NOT NULL,
  public_key TEXT NOT NULL,
  status network_node_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, public_key)
);
