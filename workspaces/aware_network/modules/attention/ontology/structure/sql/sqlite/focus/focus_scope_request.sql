-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE focus_scope_request (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  focus_scope_id TEXT NOT NULL,
  focus_id TEXT NOT NULL,
  -- ATTRIBUTES
  rationale TEXT,
  state TEXT NOT NULL,
  response_rationale TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, focus_scope_id, focus_id),
  FOREIGN KEY (branch_id, projection_hash, focus_scope_id) REFERENCES focus_scope(branch_id, projection_hash, id)
);
