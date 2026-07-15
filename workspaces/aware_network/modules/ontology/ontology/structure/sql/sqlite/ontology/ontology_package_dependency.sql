-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE ontology_package_dependency (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  ontology_package_id TEXT NOT NULL,
  target_ontology_package_id TEXT NOT NULL,
  target_ontology_package_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  description TEXT,
  expected_hash_sha256 TEXT,
  target_package_name TEXT NOT NULL,
  target_version_number INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, ontology_package_id, target_ontology_package_id),
  FOREIGN KEY (branch_id, projection_hash, ontology_package_id) REFERENCES ontology_package(branch_id, projection_hash, id)
);
