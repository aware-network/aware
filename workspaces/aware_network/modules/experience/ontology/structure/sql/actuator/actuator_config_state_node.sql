-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actuator_config_state_node (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  object_projection_graph_node_id UUID NOT NULL,
  -- RELATIONSHIPS
  actuator_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, object_projection_graph_node_id),
  FOREIGN KEY (branch_id, projection_hash, actuator_config_id) REFERENCES actuator_config(branch_id, projection_hash, id)
);
