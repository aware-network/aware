-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_binding (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_declaration_id TEXT NOT NULL,
  -- ATTRIBUTES
  fqn_prefix TEXT NOT NULL,
  namespace TEXT NOT NULL,
  class_name TEXT NOT NULL,
  attribute_name TEXT,
  target_projection_name TEXT,
  side TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_declaration_id, fqn_prefix, namespace, class_name),
  FOREIGN KEY (branch_id, projection_hash, object_projection_graph_declaration_id) REFERENCES object_projection_graph_declaration(branch_id, projection_hash, id)
);
