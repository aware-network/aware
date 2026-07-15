-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_window (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  interface_id TEXT NOT NULL,
  window_id TEXT NOT NULL,
  active_navigation_context_id TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, interface_id, window_id),
  FOREIGN KEY (branch_id, projection_hash, interface_id) REFERENCES interface(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, active_navigation_context_id) REFERENCES interface_window_navigation_context(branch_id, projection_hash, id)
);
