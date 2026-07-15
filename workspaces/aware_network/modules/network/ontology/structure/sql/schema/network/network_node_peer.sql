-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node_peer (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  source_peer_node_id UUID NOT NULL,
  target_peer_node_id UUID NOT NULL,
  -- ATTRIBUTES
  status network_request_status NOT NULL,
  peer_http_base_url TEXT,
  connected_at TIMESTAMPTZ NOT NULL,
  failed_interactions INTEGER NOT NULL,
  last_ping_at TIMESTAMPTZ NOT NULL,
  latency_ms INTEGER,
  successful_interactions INTEGER NOT NULL,
  trust_score NUMERIC NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, source_peer_node_id, target_peer_node_id)
);
