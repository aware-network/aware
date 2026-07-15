-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_node_environment (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  network_node_id TEXT NOT NULL,
  environment_id TEXT NOT NULL,
  -- ATTRIBUTES
  is_active INTEGER NOT NULL,
  priority INTEGER NOT NULL,
  role TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, network_node_id, environment_id),
  FOREIGN KEY (branch_id, projection_hash, network_node_id) REFERENCES network_node(branch_id, projection_hash, id)
);
