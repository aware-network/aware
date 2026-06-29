-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_observable (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_identity_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL UNIQUE,
  observable_key TEXT NOT NULL,
  kind TEXT,
  label TEXT,
  description TEXT,
  position INTEGER,
  is_default BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_identity_id, observable_key),
  FOREIGN KEY (branch_id, projection_hash, object_projection_graph_identity_id) REFERENCES object_projection_graph_identity(branch_id, projection_hash, id)
);
