-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE code_package_artifact_status AS ENUM ('available', 'failed', 'missing', 'optional', 'stale');

CREATE TYPE code_package_config_input_kind AS ENUM ('artifact', 'delta', 'graph', 'manifest', 'package');

CREATE TYPE code_package_config_output_kind AS ENUM ('artifact', 'code_package_delta', 'package');

CREATE TYPE code_package_config_runtime_context_kind AS ENUM ('environment', 'execution_context', 'ontology_package', 'projection');
