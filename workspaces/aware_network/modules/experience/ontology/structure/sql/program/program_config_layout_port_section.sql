-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_layout_port_section (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  program_config_port_id UUID NOT NULL,
  layout_section_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_config_layout_id UUID NOT NULL,
  -- ATTRIBUTES
  on_bind program_slot_on_bind NOT NULL,
  is_visible_default BOOLEAN,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, program_config_port_id, layout_section_id),
  FOREIGN KEY (branch_id, projection_hash, program_config_layout_id) REFERENCES program_config_layout(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_config_port_id) REFERENCES program_config_port(branch_id, projection_hash, id)
);
