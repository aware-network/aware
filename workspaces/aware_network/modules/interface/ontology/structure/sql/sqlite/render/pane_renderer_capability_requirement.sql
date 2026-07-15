-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_renderer_capability_requirement (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  pane_render_spec_id TEXT NOT NULL,
  -- ATTRIBUTES
  capability_kind TEXT NOT NULL,
  capability_key TEXT NOT NULL,
  is_required INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, pane_render_spec_id, capability_kind, capability_key),
  FOREIGN KEY (branch_id, projection_hash, pane_render_spec_id) REFERENCES pane_render_spec(branch_id, projection_hash, id)
);
