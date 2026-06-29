-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id TEXT,
  object_config_graph_id TEXT,
  object_config_graph_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  package_name TEXT NOT NULL,
  fqn_prefix TEXT NOT NULL,
  title TEXT,
  description TEXT,
  function_impl_ownership TEXT NOT NULL,
  function_impl_parity_policy TEXT NOT NULL,
  implementation_policy_source TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, package_name, fqn_prefix)
);
