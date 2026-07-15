-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actuator_config_state_node (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  actuator_config_id TEXT NOT NULL,
  object_projection_graph_node_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actuator_config_id, object_projection_graph_node_id),
  FOREIGN KEY (branch_id, projection_hash, actuator_config_id) REFERENCES actuator_config(branch_id, projection_hash, id)
);
