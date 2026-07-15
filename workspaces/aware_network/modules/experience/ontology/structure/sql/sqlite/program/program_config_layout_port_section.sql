-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_layout_port_section (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_config_layout_id TEXT NOT NULL,
  program_config_port_id TEXT NOT NULL,
  layout_section_id TEXT NOT NULL,
  -- ATTRIBUTES
  on_bind TEXT NOT NULL,
  is_visible_default INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_config_layout_id, program_config_port_id, layout_section_id),
  FOREIGN KEY (branch_id, projection_hash, program_config_layout_id) REFERENCES program_config_layout(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_config_port_id) REFERENCES program_config_port(branch_id, projection_hash, id)
);
