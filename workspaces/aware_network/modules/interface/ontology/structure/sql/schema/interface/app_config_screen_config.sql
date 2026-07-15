-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE app_config_screen_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  app_config_id UUID NOT NULL,
  projection_experience_id UUID NOT NULL,
  projection_experience_layout_graph_binding_id UUID NOT NULL,
  -- ATTRIBUTES
  screen_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, app_config_id, screen_key, projection_experience_id, projection_experience_layout_graph_binding_id),
  FOREIGN KEY (branch_id, projection_hash, app_config_id) REFERENCES app_config(branch_id, projection_hash, id)
);
