-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_render_node (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  pane_render_spec_id UUID NOT NULL,
  component_contract_id UUID,
  -- ATTRIBUTES
  node_key TEXT NOT NULL,
  parent_node_key TEXT,
  node_kind pane_render_node_kind NOT NULL,
  semantic_role pane_render_semantic_role,
  slot_key TEXT,
  order_ INTEGER NOT NULL,
  label TEXT,
  text TEXT,
  placeholder TEXT,
  component_ref TEXT,
  fallback_node_kind pane_render_node_kind,
  fallback_text TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, pane_render_spec_id, node_key),
  FOREIGN KEY (branch_id, projection_hash, pane_render_spec_id) REFERENCES pane_render_spec(branch_id, projection_hash, id)
);
