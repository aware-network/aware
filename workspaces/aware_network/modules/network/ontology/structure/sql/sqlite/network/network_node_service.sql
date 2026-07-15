-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node_service (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  network_node_id TEXT NOT NULL,
  service_id TEXT NOT NULL,
  service_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  endpoint_refs TEXT NOT NULL,
  host_id TEXT NOT NULL,
  host_version TEXT,
  protocol_version TEXT NOT NULL,
  service_name TEXT NOT NULL,
  stream_endpoint_refs TEXT NOT NULL,
  supports_stream_events INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, network_node_id, service_package_id),
  FOREIGN KEY (branch_id, projection_hash, network_node_id) REFERENCES network_node(branch_id, projection_hash, id)
);
