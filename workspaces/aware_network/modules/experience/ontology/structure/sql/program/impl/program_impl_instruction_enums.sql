-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE program_impl_instruction_type AS ENUM ('bind', 'expect', 'input', 'intent', 'invoke', 'let');

CREATE TYPE program_impl_invoke_target_kind AS ENUM ('construct', 'instance');
