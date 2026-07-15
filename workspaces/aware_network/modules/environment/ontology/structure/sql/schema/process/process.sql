-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE process (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_profile_id UUID NOT NULL,
  parent_id UUID,
  process_config_id UUID NOT NULL,
  image_id UUID UNIQUE,
  overview_content_id UUID,
  backlog_chain_id UUID,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  description TEXT,
  priority_level priority_level NOT NULL,
  status process_status NOT NULL,
  title TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_profile_id, key, process_config_id)
);
