-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_identity (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  interface_id UUID NOT NULL,
  identity_id UUID NOT NULL,
  -- ATTRIBUTES
  linked_at TIMESTAMPTZ NOT NULL,
  last_confirmed_at TIMESTAMPTZ,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, interface_id, identity_id)
);
