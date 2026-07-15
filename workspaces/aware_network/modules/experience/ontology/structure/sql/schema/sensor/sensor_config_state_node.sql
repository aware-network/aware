-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sensor_config_state_node (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  sensor_config_id UUID NOT NULL,
  object_projection_graph_node_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sensor_config_id, object_projection_graph_node_id),
  FOREIGN KEY (branch_id, projection_hash, sensor_config_id) REFERENCES sensor_config(branch_id, projection_hash, id)
);
