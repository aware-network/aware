-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_identity_id UUID,
  -- ATTRIBUTES
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  hash TEXT NOT NULL UNIQUE,
  layout_hash TEXT,
  fqn_prefix TEXT NOT NULL,
  language code_language NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, fqn_prefix, language)
);
