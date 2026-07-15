-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_window_navigation_context (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  interface_environment_id UUID NOT NULL,
  environment_navigation_context_id UUID NOT NULL,
  -- RELATIONSHIPS
  interface_window_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, interface_environment_id, environment_navigation_context_id),
  FOREIGN KEY (branch_id, projection_hash, interface_window_id) REFERENCES interface_window(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, interface_environment_id) REFERENCES interface_environment(branch_id, projection_hash, id)
);
