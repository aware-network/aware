-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_topology_thread_layout_seed (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_topology_thread_seed_id UUID NOT NULL,
  layout_config_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  position INTEGER,
  activate_on_seed BOOLEAN NOT NULL,
  narrative TEXT,
  intent TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_topology_thread_seed_id, layout_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_topology_thread_seed_id) REFERENCES environment_topology_thread_seed(branch_id, projection_hash, id)
);
