-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE connector_session (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  session_key TEXT NOT NULL,
  connector_id TEXT NOT NULL,
  -- RELATIONSHIPS
  connector_provider_id TEXT NOT NULL,
  -- ATTRIBUTES
  session_ref TEXT,
  host_ref TEXT,
  principal_ref TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, session_key, connector_id)
);
