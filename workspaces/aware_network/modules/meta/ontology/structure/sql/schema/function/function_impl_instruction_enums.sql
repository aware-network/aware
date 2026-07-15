-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE function_impl_delete_target_kind AS ENUM ('self');

CREATE TYPE function_impl_instruction_type AS ENUM ('construct', 'delete', 'invoke', 'let', 'require', 'set');

CREATE TYPE function_impl_invoke_kind AS ENUM ('call', 'construct');

CREATE TYPE function_impl_require_compare_operator AS ENUM ('eq', 'gt', 'gte', 'lt', 'lte', 'neq');

CREATE TYPE function_impl_require_kind AS ENUM ('all_or_none', 'cardinality', 'compare', 'equals', 'exists', 'member', 'text_matches_regex', 'unique');

CREATE TYPE function_impl_value_source_kind AS ENUM ('function_input_ref', 'let_ref', 'literal', 'read_path', 'transform');

CREATE TYPE function_impl_value_source_read_path_root_kind AS ENUM ('function_input', 'let_binding', 'target_attribute');

CREATE TYPE function_impl_value_transform_kind AS ENUM ('text_casefold', 'text_concat', 'text_default_if_blank', 'text_lower', 'text_slice', 'text_strip');
