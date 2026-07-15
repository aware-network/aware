-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_provider_grant (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_provider_id UUID NOT NULL,
  process_config_id UUID,
  thread_config_id UUID,
  object_projection_graph_id UUID,
  -- ATTRIBUTES
  action_scope TEXT,
  description TEXT,
  grant_key TEXT NOT NULL,
  metadata_json JSONB,
  scope_kind TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_provider_id, grant_key),
  FOREIGN KEY (branch_id, projection_hash, environment_provider_id) REFERENCES environment_provider(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, process_config_id) REFERENCES process_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, thread_config_id) REFERENCES thread_config(branch_id, projection_hash, id)
);
