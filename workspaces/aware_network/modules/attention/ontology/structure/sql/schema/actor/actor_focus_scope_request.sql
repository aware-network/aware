-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_focus_scope_request (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  actor_focus_scope_id UUID NOT NULL,
  focus_scope_request_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_focus_scope_id, focus_scope_request_id),
  FOREIGN KEY (branch_id, projection_hash, actor_focus_scope_id) REFERENCES actor_focus_scope(branch_id, projection_hash, id)
);
