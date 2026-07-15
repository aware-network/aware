-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_topology_process_seed (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  process_key TEXT NOT NULL,
  process_config_id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_topology_seed_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  key TEXT,
  position INTEGER,
  narrative TEXT,
  intent TEXT,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, process_key, process_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_topology_seed_id) REFERENCES environment_topology_seed(branch_id, projection_hash, id)
);
