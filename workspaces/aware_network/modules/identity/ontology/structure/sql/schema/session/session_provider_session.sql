-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_provider_session (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  session_id UUID NOT NULL,
  provider_session_config_id UUID NOT NULL,
  provider_object_instance_graph_identity_id UUID,
  provider_class_instance_identity_id UUID,
  provider_object_instance_graph_branch_id UUID,
  -- ATTRIBUTES
  provider_session_key TEXT NOT NULL,
  provider_session_ref TEXT,
  status TEXT NOT NULL,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_id, provider_session_key, provider_session_config_id),
  FOREIGN KEY (branch_id, projection_hash, session_id) REFERENCES session(branch_id, projection_hash, id)
);
