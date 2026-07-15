-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_config_api_projection (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_config_api_id UUID NOT NULL,
  api_graph_projection_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_config_api_id, api_graph_projection_id),
  FOREIGN KEY (branch_id, projection_hash, service_config_api_id) REFERENCES service_config_api(branch_id, projection_hash, id)
);
