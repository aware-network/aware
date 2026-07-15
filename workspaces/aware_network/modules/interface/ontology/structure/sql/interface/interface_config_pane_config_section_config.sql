-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_config_pane_config_section_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  layout_config_section_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  interface_config_pane_config_id UUID NOT NULL,
  -- ATTRIBUTES
  is_default BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, layout_config_section_config_id),
  UNIQUE (branch_id, projection_hash, interface_config_pane_config_id, layout_config_section_config_id),
  FOREIGN KEY (branch_id, projection_hash, interface_config_pane_config_id) REFERENCES interface_config_pane_config(branch_id, projection_hash, id)
);
