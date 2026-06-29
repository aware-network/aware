-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_package_dependency (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_package_id UUID NOT NULL,
  target_object_config_graph_package_id UUID NOT NULL,
  target_version_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_package_id, target_object_config_graph_package_id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_package_id) REFERENCES object_config_graph_package(branch_id, projection_hash, id)
);
