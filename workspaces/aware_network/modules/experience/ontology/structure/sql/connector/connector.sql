-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE connector (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  connector_instance_key TEXT NOT NULL,
  -- RELATIONSHIPS
  connector_config_id UUID NOT NULL,
  -- ATTRIBUTES
  runtime_ref TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, connector_instance_key)
);
