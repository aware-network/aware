-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_session_profile (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  experience_session_id UUID NOT NULL,
  profile_id UUID NOT NULL,
  -- ATTRIBUTES
  status TEXT NOT NULL,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_session_id, profile_id)
);
