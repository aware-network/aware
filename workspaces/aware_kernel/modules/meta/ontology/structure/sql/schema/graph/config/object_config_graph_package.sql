-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id UUID,
  object_config_graph_id UUID,
  object_config_graph_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  package_name TEXT NOT NULL,
  fqn_prefix TEXT NOT NULL,
  title TEXT,
  description TEXT,
  function_impl_ownership object_config_graph_package_function_impl_ownership NOT NULL,
  function_impl_parity_policy object_config_graph_package_function_impl_parity_policy NOT NULL,
  implementation_policy_source TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, package_name, fqn_prefix)
);
