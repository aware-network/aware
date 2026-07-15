-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_config_object_projection_graph (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  thread_config_id UUID NOT NULL,
  object_projection_graph_id UUID NOT NULL,
  -- ATTRIBUTES
  narrative TEXT,
  intent TEXT,
  view_key TEXT,
  position INTEGER,
  is_default BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, thread_config_id, object_projection_graph_id),
  FOREIGN KEY (branch_id, projection_hash, thread_config_id) REFERENCES thread_config(branch_id, projection_hash, id)
);
