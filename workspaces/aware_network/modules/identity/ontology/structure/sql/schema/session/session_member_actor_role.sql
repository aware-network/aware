-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_member_actor_role (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  session_member_id UUID NOT NULL,
  actor_role_id UUID NOT NULL,
  -- ATTRIBUTES
  source_kind TEXT NOT NULL,
  status TEXT NOT NULL,
  evidence_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_member_id, actor_role_id),
  FOREIGN KEY (branch_id, projection_hash, session_member_id) REFERENCES session_member(branch_id, projection_hash, id)
);
