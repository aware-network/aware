-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_identity_network_node (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  interface_identity_id TEXT NOT NULL,
  network_node_id TEXT NOT NULL,
  -- ATTRIBUTES
  connected_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  last_ack_at TEXT,
  disconnected_at TEXT,
  last_delivery_offset INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, interface_identity_id, network_node_id)
);
