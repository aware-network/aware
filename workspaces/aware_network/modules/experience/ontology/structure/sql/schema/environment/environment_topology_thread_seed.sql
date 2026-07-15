-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_topology_thread_seed (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_topology_process_seed_id UUID NOT NULL,
  thread_config_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  is_main BOOLEAN NOT NULL,
  key TEXT,
  thread_key TEXT NOT NULL,
  position INTEGER,
  narrative TEXT,
  intent TEXT,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_topology_process_seed_id, thread_key, thread_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_topology_process_seed_id) REFERENCES environment_topology_process_seed(branch_id, projection_hash, id)
);
