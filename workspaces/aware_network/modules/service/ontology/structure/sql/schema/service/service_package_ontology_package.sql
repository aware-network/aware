-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_package_ontology_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_package_id UUID NOT NULL,
  ontology_package_id UUID NOT NULL,
  ontology_package_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  role TEXT NOT NULL,
  requirement_mode TEXT NOT NULL,
  package_name TEXT NOT NULL,
  fqn_prefix TEXT NOT NULL,
  expected_hash_sha256 TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_package_id, ontology_package_id),
  FOREIGN KEY (branch_id, projection_hash, service_package_id) REFERENCES service_package(branch_id, projection_hash, id)
);
