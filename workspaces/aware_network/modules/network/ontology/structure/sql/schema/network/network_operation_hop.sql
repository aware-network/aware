-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_operation_hop (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  network_operation_id UUID NOT NULL,
  source_environment_id UUID,
  source_node_id UUID,
  target_environment_id UUID,
  target_node_id UUID,
  -- ATTRIBUTES
  source_interface_id UUID,
  target_interface_id UUID,
  hop_index INTEGER NOT NULL,
  source_app_type network_app_type NOT NULL,
  target_app_type network_app_type NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, network_operation_id, hop_index)
);
