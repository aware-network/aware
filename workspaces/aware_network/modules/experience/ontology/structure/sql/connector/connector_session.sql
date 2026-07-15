-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE connector_session (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  session_key TEXT NOT NULL,
  connector_id UUID NOT NULL,
  -- RELATIONSHIPS
  connector_provider_id UUID NOT NULL,
  -- ATTRIBUTES
  session_ref TEXT,
  host_ref TEXT,
  principal_ref TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, session_key, connector_id)
);
