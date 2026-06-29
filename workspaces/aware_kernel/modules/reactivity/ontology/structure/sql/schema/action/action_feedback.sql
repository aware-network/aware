-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_feedback (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  action_execution_id UUID NOT NULL,
  payload_model_id UUID UNIQUE,
  -- ATTRIBUTES
  created_at_unix_ms INTEGER NOT NULL,
  message TEXT,
  payload JSONB NOT NULL,
  sequence INTEGER NOT NULL,
  stage action_feedback_stage NOT NULL,
  status action_feedback_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, action_execution_id, sequence),
  FOREIGN KEY (branch_id, projection_hash, action_execution_id) REFERENCES action_execution(branch_id, projection_hash, id)
);
