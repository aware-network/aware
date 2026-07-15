-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_window_navigation_context (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  interface_window_id TEXT NOT NULL,
  interface_environment_id TEXT NOT NULL,
  environment_navigation_context_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, interface_window_id, interface_environment_id, environment_navigation_context_id),
  FOREIGN KEY (branch_id, projection_hash, interface_window_id) REFERENCES interface_window(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, interface_environment_id) REFERENCES interface_environment(branch_id, projection_hash, id)
);
