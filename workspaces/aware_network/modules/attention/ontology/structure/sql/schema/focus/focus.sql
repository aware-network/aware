-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE focus (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  id UUID NOT NULL,
  projection_hash TEXT,
  -- RELATIONSHIPS
  object_instance_graph_branch_id UUID,
  object_projection_graph_identity_id UUID NOT NULL,
  -- ATTRIBUTES
  focus_scope_id UUID NOT NULL,
  target_id UUID,
  target_type TEXT,
  description TEXT,
  expires_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL,
  last_accessed TIMESTAMPTZ,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, focus_scope_id, object_projection_graph_identity_id)
);
