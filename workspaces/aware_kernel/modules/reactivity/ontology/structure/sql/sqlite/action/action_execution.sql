-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_execution (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  action_intent_id TEXT NOT NULL,
  -- ATTRIBUTES
  execution_context TEXT NOT NULL,
  execution_key TEXT NOT NULL,
  executor_ref TEXT,
  result_info TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, action_intent_id, execution_key),
  FOREIGN KEY (branch_id, projection_hash, action_intent_id) REFERENCES action_intent(branch_id, projection_hash, id)
);
