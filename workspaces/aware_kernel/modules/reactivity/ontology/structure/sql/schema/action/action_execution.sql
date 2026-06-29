-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_execution (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  action_intent_id UUID NOT NULL,
  -- ATTRIBUTES
  execution_context JSONB NOT NULL,
  execution_key TEXT NOT NULL,
  executor_ref TEXT,
  result_info TEXT,
  status action_execution_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, action_intent_id, execution_key),
  FOREIGN KEY (branch_id, projection_hash, action_intent_id) REFERENCES action_intent(branch_id, projection_hash, id)
);
