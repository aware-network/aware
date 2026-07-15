-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_render_node (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  pane_render_spec_id TEXT NOT NULL,
  component_contract_id TEXT,
  -- ATTRIBUTES
  node_key TEXT NOT NULL,
  parent_node_key TEXT,
  node_kind TEXT NOT NULL,
  semantic_role TEXT,
  slot_key TEXT,
  order_ INTEGER NOT NULL,
  label TEXT,
  text TEXT,
  placeholder TEXT,
  component_ref TEXT,
  fallback_node_kind TEXT,
  fallback_text TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, pane_render_spec_id, node_key),
  FOREIGN KEY (branch_id, projection_hash, pane_render_spec_id) REFERENCES pane_render_spec(branch_id, projection_hash, id)
);
