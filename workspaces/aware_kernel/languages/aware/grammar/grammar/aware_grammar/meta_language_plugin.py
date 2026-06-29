"""
Aware meta language plugin for ObjectConfigGraph/code materialization.

This module aggregates all Aware-specific components into a unified MetaLanguagePlugin:
- Code-level parsing (via existing AwareLanguagePlugin)
- Graph generation (builders and transformers)
- Canonical ObjectConfigGraph rendering (full-file and product renderers)
- File filtering and utilities
"""

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta plugin system
from aware_meta.language_plugin import MetaLanguagePlugin

# Existing Aware code plugin
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Graph builders and transformers
from aware_grammar.file_filter_config import AwareFileFilterConfig

# Aware layout strategy
from aware_grammar.layout_strategy import AwareLayoutStrategy
from aware_grammar.renderer_stable_ids import AwareStableIdsRendererLanguage

# Canonical -> Runtime IR transformer (shared)
from aware_grammar.transformers import AwareToRuntimeTransformer

# Create the Aware meta plugin
AWARE_META_PLUGIN = MetaLanguagePlugin(
    language=CodeLanguage.aware,
    # ---------- Code-level parsing ----------
    code_plugin=AWARE_CODE_PLUGIN,  # Reuse existing code plugin
    # ---------- Graph generation ----------
    # Canonical AWARE -> runtime IR derivation.
    language_to_runtime_transformer=AwareToRuntimeTransformer,
    # ---------- Rendering ----------
    language_renderers={
        # Compiler-owned stable-id parity artifact (phase A).
        "stable_ids": AwareStableIdsRendererLanguage,
    },
    default_renderer_names=(),
    # Legacy entity-level renderer wiring is intentionally empty. Future
    # graph->source projection should use shared CodeSection/segment delta DTOs.
    surgical_renderers={},
    # ---------- File system ----------
    file_filter_config_factory=AwareFileFilterConfig,
    supports_full_file_recreation=True,
    imports_bind_unaliased_module_head=False,
    # ---------- Layout strategy ----------
    layout_strategy=AwareLayoutStrategy,
)
