-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_session (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  name TEXT NOT NULL,
  -- RELATIONSHIPS
  interface_id UUID NOT NULL,
  interface_identity_id UUID NOT NULL,
  -- ATTRIBUTES
  state interface_session_state NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name)
);
