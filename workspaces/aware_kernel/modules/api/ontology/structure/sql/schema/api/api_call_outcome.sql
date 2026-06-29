-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_call_outcome (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  api_call_id UUID UNIQUE,
  response_model_id UUID UNIQUE,
  -- ATTRIBUTES
  error TEXT,
  status api_call_outcome_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, api_call_id) REFERENCES api_call(branch_id, projection_hash, id)
);
