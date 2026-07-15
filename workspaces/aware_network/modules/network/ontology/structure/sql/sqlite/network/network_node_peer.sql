-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node_peer (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  source_peer_node_id TEXT NOT NULL,
  target_peer_node_id TEXT NOT NULL,
  -- ATTRIBUTES
  status TEXT NOT NULL,
  peer_http_base_url TEXT,
  connected_at TEXT NOT NULL,
  failed_interactions INTEGER NOT NULL,
  last_ping_at TEXT NOT NULL,
  latency_ms INTEGER,
  successful_interactions INTEGER NOT NULL,
  trust_score REAL NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, source_peer_node_id, target_peer_node_id)
);
