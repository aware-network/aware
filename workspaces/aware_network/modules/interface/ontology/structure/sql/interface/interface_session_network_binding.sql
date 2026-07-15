-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_session_network_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  interface_session_id UUID NOT NULL,
  interface_identity_network_node_id UUID NOT NULL,
  -- ATTRIBUTES
  connected_at TIMESTAMPTZ NOT NULL,
  last_seen_at TIMESTAMPTZ NOT NULL,
  last_ack_at TIMESTAMPTZ,
  disconnected_at TIMESTAMPTZ,
  last_delivery_offset INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id)
);
