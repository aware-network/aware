-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_style_token_ref (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  pane_render_node_id UUID NOT NULL,
  -- ATTRIBUTES
  token_key TEXT NOT NULL,
  token_value TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, pane_render_node_id, token_key),
  FOREIGN KEY (branch_id, projection_hash, pane_render_node_id) REFERENCES pane_render_node(branch_id, projection_hash, id)
);
