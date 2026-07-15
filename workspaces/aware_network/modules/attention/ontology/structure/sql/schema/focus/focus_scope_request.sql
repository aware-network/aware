-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE focus_scope_request (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  focus_scope_id UUID NOT NULL,
  focus_id UUID NOT NULL,
  -- ATTRIBUTES
  rationale TEXT,
  state focus_scope_request_status NOT NULL,
  response_rationale TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, focus_scope_id, focus_id),
  FOREIGN KEY (branch_id, projection_hash, focus_scope_id) REFERENCES focus_scope(branch_id, projection_hash, id)
);
