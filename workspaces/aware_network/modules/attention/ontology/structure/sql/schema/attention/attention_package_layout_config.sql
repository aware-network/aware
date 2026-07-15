-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_package_layout_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  attention_package_id UUID NOT NULL,
  layout_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_package_id, layout_config_id),
  FOREIGN KEY (branch_id, projection_hash, attention_package_id) REFERENCES attention_package(branch_id, projection_hash, id)
);
