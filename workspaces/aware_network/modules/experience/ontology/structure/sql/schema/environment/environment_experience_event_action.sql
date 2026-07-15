-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_event_action (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_event_id UUID NOT NULL,
  action_experience_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_experience_event_id, action_experience_id),
  FOREIGN KEY (branch_id, projection_hash, environment_experience_event_id) REFERENCES environment_experience_event(branch_id, projection_hash, id)
);
