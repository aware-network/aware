-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_ontology (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_id TEXT NOT NULL,
  ontology_id TEXT NOT NULL,
  -- ATTRIBUTES
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_id, ontology_id),
  FOREIGN KEY (branch_id, projection_hash, environment_id) REFERENCES environment(branch_id, projection_hash, id)
);
