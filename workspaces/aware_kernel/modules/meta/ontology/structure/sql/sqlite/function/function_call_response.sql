-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_call_response (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_call_id TEXT NOT NULL,
  root_class_instance_identity_id TEXT,
  -- ATTRIBUTES
  graph_hash_post TEXT,
  error_message TEXT,
  execution_time_ms INTEGER NOT NULL,
  success INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_call_id),
  FOREIGN KEY (branch_id, projection_hash, function_call_id) REFERENCES function_call(branch_id, projection_hash, id)
);
