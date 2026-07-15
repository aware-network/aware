-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_provider_session (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  session_id TEXT NOT NULL,
  provider_session_config_id TEXT NOT NULL,
  provider_object_instance_graph_identity_id TEXT,
  provider_class_instance_identity_id TEXT,
  provider_object_instance_graph_branch_id TEXT,
  -- ATTRIBUTES
  provider_session_key TEXT NOT NULL,
  provider_session_ref TEXT,
  status TEXT NOT NULL,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_id, provider_session_key, provider_session_config_id),
  FOREIGN KEY (branch_id, projection_hash, session_id) REFERENCES session(branch_id, projection_hash, id)
);
