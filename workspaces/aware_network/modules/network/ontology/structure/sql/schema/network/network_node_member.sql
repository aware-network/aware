-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node_member (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  network_node_id UUID NOT NULL,
  -- ATTRIBUTES
  identity_id UUID NOT NULL,
  is_primary BOOLEAN NOT NULL,
  last_sync_at TIMESTAMPTZ NOT NULL,
  managed_since TIMESTAMPTZ NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, network_node_id, identity_id)
);
