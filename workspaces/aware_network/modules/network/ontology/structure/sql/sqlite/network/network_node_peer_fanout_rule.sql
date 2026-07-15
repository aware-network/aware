-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node_peer_fanout_rule (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  network_node_peer_id TEXT NOT NULL,
  lane_branch_id TEXT NOT NULL,
  -- ATTRIBUTES
  lane_projection_hash TEXT NOT NULL,
  enabled INTEGER NOT NULL,
  mode TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, network_node_peer_id, lane_projection_hash, lane_branch_id),
  FOREIGN KEY (branch_id, projection_hash, network_node_peer_id) REFERENCES network_node_peer(branch_id, projection_hash, id)
);
