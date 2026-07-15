-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_renderer_capability_requirement (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  capability_kind pane_render_capability_kind NOT NULL,
  capability_key TEXT NOT NULL,
  -- RELATIONSHIPS
  pane_render_spec_id UUID NOT NULL,
  -- ATTRIBUTES
  is_required BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, capability_kind, capability_key),
  FOREIGN KEY (branch_id, projection_hash, pane_render_spec_id) REFERENCES pane_render_spec(branch_id, projection_hash, id)
);
