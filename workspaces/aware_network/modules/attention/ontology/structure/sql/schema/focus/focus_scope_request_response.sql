-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE focus_scope_request_response (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  focus_scope_request_id UUID UNIQUE,
  -- ATTRIBUTES
  success BOOLEAN NOT NULL,
  message TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, focus_scope_request_id) REFERENCES focus_scope_request(branch_id, projection_hash, id)
);
