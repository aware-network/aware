-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  os interface_os NOT NULL,
  version TEXT NOT NULL,
  -- RELATIONSHIPS
  interface_config_id UUID NOT NULL,
  system_actor_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, os, version)
);
