-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE hub_authority (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  authority_key TEXT NOT NULL,
  -- ATTRIBUTES
  base_url TEXT,
  description TEXT,
  title TEXT,
  visibility hub_authority_visibility NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, authority_key)
);
