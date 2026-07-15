-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_branch (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_id TEXT NOT NULL,
  service_config_api_projection_id TEXT NOT NULL,
  object_instance_graph_branch_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_id, service_config_api_projection_id, object_instance_graph_branch_id),
  FOREIGN KEY (branch_id, projection_hash, service_id) REFERENCES service(branch_id, projection_hash, id)
);
