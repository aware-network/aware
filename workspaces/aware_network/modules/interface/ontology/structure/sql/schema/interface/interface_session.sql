-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_session (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  interface_id UUID NOT NULL,
  identity_session_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  state interface_session_state NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, interface_id, name, identity_session_id)
);
