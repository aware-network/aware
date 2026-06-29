-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_feedback (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  action_execution_id TEXT NOT NULL,
  payload_model_id TEXT UNIQUE,
  -- ATTRIBUTES
  created_at_unix_ms INTEGER NOT NULL,
  message TEXT,
  payload TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, action_execution_id, sequence),
  FOREIGN KEY (branch_id, projection_hash, action_execution_id) REFERENCES action_execution(branch_id, projection_hash, id)
);
