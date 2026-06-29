"""Dart meta language plugin for code graph and transformations."""

from aware_code_ontology.code.code_enums import CodeLanguage

# Meta language plugin
from aware_meta.language_plugin import MetaLanguagePlugin, RendererProfileInputContract

# File system config
from aware_file_system.config import CodeIntrospectionFilterConfig, regex_include

# Dart code language plugin
from dart_grammar.code_language_plugin import DART_CODE_PLUGIN

# Dart layout strategy
from dart_grammar.layout_strategy import DartLayoutStrategyTemplateMixin
from dart_grammar.package_strategy import DartPackageStrategy

# Dart renderers
from dart_grammar.renderer_model import DartModelRenderer
from dart_grammar.renderer_barrel import DartApiBarrelRenderer
from dart_grammar.renderer_api_public_package import (
    DartApiPublicPackageBindingsRendererLanguage,
    DartApiPublicPackageClientRendererLanguage,
    DartApiPublicPackageLibraryRendererLanguage,
)
from dart_grammar.renderer_functions import DartFunctionsRenderer
from dart_grammar.renderer_materialization import DartMaterializationRenderer
from dart_grammar.renderer_materialization_opg import DartMaterializationOpgRenderer
from dart_grammar.renderer_materialization_registry import DartMaterializationRegistryRenderer
from dart_grammar.renderer_materialization_support import DartMaterializationSupportRenderer
from dart_grammar.renderer_sqlite_schema import DartSqliteSchemaRenderer
from dart_grammar.renderer_sqlite_projection_plan import DartSqliteProjectionPlanRenderer
from dart_grammar.renderer_policy import DartRenderPolicy
from dart_grammar.renderer_stable_ids import DartStableIdsRendererLanguage

from dart_grammar.reserved_keywords import DART_RESERVED_KEYWORD_POLICIES
from dart_grammar.transformers.runtime_to_dart_transformer import RuntimeToDartTransformer

ONTOLOGY_DTO_RENDERER_PROFILE = "ontology_dto"


def _dart_filter_config_factory() -> CodeIntrospectionFilterConfig:
    cfg = CodeIntrospectionFilterConfig()
    # Ensure Dart files are included
    cfg.regex.append(regex_include(r".*\.dart$"))
    return cfg


DART_META_PLUGIN = MetaLanguagePlugin(
    language=CodeLanguage.dart,
    code_plugin=DART_CODE_PLUGIN,
    # Dart requires a runtime->dart lowering step to flatten parent_class/augment semantics
    # into concrete data model fields (renderers remain emit-only).
    runtime_to_language_transformer=RuntimeToDartTransformer,
    language_renderers={
        "model": DartModelRenderer,
        "api": DartApiBarrelRenderer,
        "api_public_package_bindings": DartApiPublicPackageBindingsRendererLanguage,
        "api_public_package_client": DartApiPublicPackageClientRendererLanguage,
        "api_public_package_library": DartApiPublicPackageLibraryRendererLanguage,
        "functions": DartFunctionsRenderer,
        "materialization": DartMaterializationRenderer,
        "materialization_support": DartMaterializationSupportRenderer,
        "materialization_registry": DartMaterializationRegistryRenderer,
        "materialization_opg": DartMaterializationOpgRenderer,
        "sqlite_schema": DartSqliteSchemaRenderer,
        "sqlite_projection_plan": DartSqliteProjectionPlanRenderer,
        # Compiler-owned stable-id library (driven by module `stable_ids.toml`).
        "stable_ids": DartStableIdsRendererLanguage,
    },
    default_renderer_names=(
        "model",
        "api",
        "functions",
    ),
    default_renderer_names_by_profile={
        "orm_runtime": (
            "model",
            "api",
            "functions",
            "stable_ids",
        ),
        "api_runtime": (
            "model",
            "api",
            "functions",
        ),
        "api_public_package": (
            "model",
            "api",
            "api_public_package_bindings",
            "api_public_package_client",
            "api_public_package_library",
        ),
        "api_service_protocol": (
            "model",
            "api",
            "functions",
        ),
        "ontology_dto": (
            "model",
            "stable_ids",
        ),
    },
    renderer_policies_by_profile={
        "orm_runtime": DartRenderPolicy.orm_default(),
        "api_runtime": DartRenderPolicy.api_default(),
        "api_public_package": DartRenderPolicy.api_default(),
        "api_service_protocol": DartRenderPolicy.api_default(),
        "ontology_dto": DartRenderPolicy.ontology_dto_default(),
    },
    renderer_profile_input_contracts={
        "orm_runtime": RendererProfileInputContract(input_mode="graph_only"),
        "api_runtime": RendererProfileInputContract(input_mode="graph_only"),
        "ontology_dto": RendererProfileInputContract(input_mode="graph_only"),
        "api_public_package": RendererProfileInputContract(
            input_mode="graph_plus_profile_inputs",
            required_keys=(
                "api.interface_spec",
                "api.invocation_manifest",
                "api.public_package_plan",
            ),
        ),
        "api_service_protocol": RendererProfileInputContract(input_mode="graph_plus_profile_inputs"),
    },
    # Legacy entity-level renderer wiring is intentionally empty. Dart uses
    # runtime->Dart lowering plus full-file/product renderers.
    surgical_renderers={},
    file_filter_config_factory=_dart_filter_config_factory,
    # ---------- Layout strategy ----------
    layout_strategy=DartLayoutStrategyTemplateMixin,
    package_strategy_factory=DartPackageStrategy,
    reserved_keyword_policies=DART_RESERVED_KEYWORD_POLICIES,
)
