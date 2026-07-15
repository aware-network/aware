-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE ontology (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  ontology_config_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  key TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, ontology_config_id, key),
  FOREIGN KEY (branch_id, projection_hash, ontology_config_id) REFERENCES ontology_config(branch_id, projection_hash, id)
);
