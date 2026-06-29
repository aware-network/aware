-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE code_package_delta_authority_kind AS ENUM ('code_package_delta', 'local_fs_view', 'remote_workspace_view', 'semantic_materialization', 'tool_materialization');

CREATE TYPE code_package_delta_kind AS ENUM ('create', 'delete', 'update');

CREATE TYPE code_package_path_role AS ENUM ('authored_source', 'generated_code', 'generated_manifest', 'generated_metadata');
