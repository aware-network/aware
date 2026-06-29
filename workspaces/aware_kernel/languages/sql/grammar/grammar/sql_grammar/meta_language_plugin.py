"""
SQL meta language plugin for ObjectConfigGraph/code materialization.

This module aggregates all SQL-specific components into a unified MetaLanguagePlugin:
- Code-level parsing (via existing SQLLanguagePlugin)
- Graph generation (builders and transformers)
- Migration file generation (full-file renderers)
- File filtering and utilities

Key Difference: SQL renderers generate migration files instead of editing existing files.
"""

from aware_code_ontology.code.code_enums import CodeLanguage

# Meta plugin system
from aware_meta.language_plugin import MetaLanguagePlugin

# Existing SQL code plugin
from sql_grammar.code_language_plugin import SQL_CODE_PLUGIN

# Graph builders and transformers
from sql_grammar.file_filter_config import SQLFileFilterConfig
from sql_grammar.transformers.runtime_to_sql_transformer import RuntimeToSQLTransformer

# SQL layout strategy
from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace

# SQL full-file renderer
from sql_grammar.renderers.renderer import (
    SQLRenderer,
    SqliteSQLRenderer,
)
from sql_grammar.reserved_keywords import SQL_RESERVED_KEYWORD_POLICIES
from sql_grammar.package_strategy import SQLPackageStrategy
from sql_grammar.renderer_policy import SQLRenderPolicy
from sql_grammar.transformer_policy import SQLTransformPolicy
from sql_grammar.materialization_outputs import produce_sql_declared_outputs

# Create the SQL meta plugin
SQL_META_PLUGIN = MetaLanguagePlugin(
    language=CodeLanguage.sql,
    # ---------- Code-level parsing ----------
    code_plugin=SQL_CODE_PLUGIN,  # Reuse existing code plugin
    # ---------- Runtime IR -> SQL lowering ----------
    runtime_to_language_transformer=RuntimeToSQLTransformer,
    # ---------- Rendering ----------
    language_renderers={
        "default": SQLRenderer,
        "sqlite": SqliteSQLRenderer,
    },
    default_renderer_names=("default",),
    default_renderer_names_by_profile={
        "orm_runtime": ("default",),
        "orm_models": ("default",),
    },
    renderer_policies_by_profile={
        "orm_runtime": SQLRenderPolicy.projection_default(),
        "orm_models": SQLRenderPolicy.orm_models_default(),
    },
    transformer_policies_by_profile={
        "orm_runtime": SQLTransformPolicy.projection_default(),
        "orm_models": SQLTransformPolicy.orm_models_default(),
    },
    # ---------- Migration file generation ----------
    # Legacy entity-level renderer wiring is intentionally empty. The canonical
    # SQL lane is runtime->SQL lowering with full-file renderers.
    surgical_renderers={},
    # ---------- File system ----------
    file_filter_config_factory=SQLFileFilterConfig,
    # ---------- Layout strategy ----------
    layout_strategy=SQLLayoutStrategyNamespace,
    package_strategy_factory=SQLPackageStrategy,
    reserved_keyword_policies=SQL_RESERVED_KEYWORD_POLICIES,
    declared_output_producer=produce_sql_declared_outputs,
)
