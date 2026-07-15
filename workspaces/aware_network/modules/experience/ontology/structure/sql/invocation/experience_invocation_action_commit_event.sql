-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_invocation_action_commit_event (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  event_id UUID NOT NULL,
  -- RELATIONSHIPS
  experience_invocation_action_commit_id UUID NOT NULL,
  -- ATTRIBUTES
  event_role TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, event_id),
  FOREIGN KEY (branch_id, projection_hash, experience_invocation_action_commit_id) REFERENCES experience_invocation_action_commit(branch_id, projection_hash, id)
);
