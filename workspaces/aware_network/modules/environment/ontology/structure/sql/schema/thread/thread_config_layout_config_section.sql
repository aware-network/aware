-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_config_layout_config_section (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  thread_config_layout_config_id UUID NOT NULL,
  layout_config_section_config_id UUID NOT NULL,
  object_projection_graph_id UUID,
  -- ATTRIBUTES
  key TEXT,
  position INTEGER,
  is_default BOOLEAN NOT NULL,
  narrative TEXT,
  intent TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, thread_config_layout_config_id, layout_config_section_config_id),
  FOREIGN KEY (branch_id, projection_hash, thread_config_layout_config_id) REFERENCES thread_config_layout_config(branch_id, projection_hash, id)
);
