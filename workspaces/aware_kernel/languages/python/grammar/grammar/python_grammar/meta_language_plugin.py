"""
Python meta language plugin for ObjectConfigGraph/code materialization.

This module aggregates all Python-specific components into a unified MetaLanguagePlugin:
- Code-level parsing (via existing PythonLanguagePlugin)
- Graph generation (builders and transformers)
- Canonical ObjectConfigGraph rendering (full-file and product renderers)
- File filtering and utilities
"""

from typing import cast

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology

# Meta plugin system
from aware_meta.language_plugin import (
    MetaLanguagePackageStrategyConfigurationRequest,
    MetaLanguagePlugin,
    RendererProfileInputContract,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
)
from python_grammar.reserved_keywords import PYTHON_RESERVED_KEYWORD_POLICIES

# Existing Python code plugin
from python_grammar.code_language_plugin import PYTHON_CODE_PLUGIN

# Graph builders and transformers
from python_grammar.file_filter_config import PythonFileFilterConfig

# Transformers (language -> runtime IR / runtime IR -> Python)
from python_grammar.transformers.python_to_runtime_transformer import (
    PythonToRuntimeTransformer,
)
from python_grammar.transformers.runtime_to_python_transformer import (
    RuntimeToPythonTransformer,
)

# Python layout strategy
from python_grammar.layout_strategy import PythonLayoutStrategyTemplateMixin
from python_grammar.package_strategy import PythonPackageStrategy
from python_grammar.package_policy import PythonPackagePolicy
from python_grammar.materialization_outputs import produce_python_declared_outputs

# Python renderer
from python_grammar.renderer import PythonRenderer
from python_grammar.renderer_runtime_handlers_composed import (
    PythonRendererRuntimeHandlersComposed,
)
from python_grammar.renderer_runtime_handlers import (
    PythonRendererRuntimeHandlerImplStubs,
    PythonRendererRuntimeHandlers,
)
from python_grammar.renderer_runtime_handlers_aware import (
    PythonRendererRuntimeHandlersAware,
)
from python_grammar.renderer_runtime_handlers_meta import (
    PythonMetaRuntimeHandlersRenderer,
)
from python_grammar.renderer_stable_ids import PythonStableIdsRendererLanguage
from python_grammar.renderer_api_public_package import (
    PythonApiPublicPackageBindingsRendererLanguage,
    PythonApiPublicPackageClientRendererLanguage,
)
from python_grammar.renderer_api_service_protocol import (
    PythonApiServiceProtocolRendererLanguage,
)
from python_grammar.renderer_policy import PythonRenderPolicy
from python_grammar.renderer_delta_orm_runtime import (
    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,
    PythonOrmRuntimeGeneratedDeltaRenderer,
)

ONTOLOGY_DTO_RENDERER_PROFILE = "ontology_dto"
ONTOLOGY_ORM_MODELS_RENDERER_PROFILE = "orm_models"
ONTOLOGY_ORM_MODELS_MATERIALIZATION_SOURCE = "ontology_orm_models"
API_DTO_RENDERER_PROFILE = "api_dto"

_PYTHON_LANGUAGE_RENDERERS = cast(
    dict[str, type[ObjectConfigGraphRendererLanguage]],
    {
        "default": PythonRenderer,
        # Runtime handlers default rail (manual/dev-owned). Uses composition shell so
        # backend can be switched safely without changing default behavior.
        "runtime_handlers": PythonRendererRuntimeHandlersComposed,
        # Explicit rails for workflows that need deterministic backend pinning.
        "runtime_handlers_manual": PythonRendererRuntimeHandlers,
        "runtime_handlers_impl": PythonRendererRuntimeHandlerImplStubs,
        "runtime_handlers_aware": PythonRendererRuntimeHandlersAware,
        "runtime_handlers_meta": PythonMetaRuntimeHandlersRenderer,
        # Compiler-owned stable-id library (driven by module `stable_ids.toml`).
        "stable_ids": PythonStableIdsRendererLanguage,
        # Product A compiled SDK support rails over the shared API client/backend.
        "api_public_package_bindings": PythonApiPublicPackageBindingsRendererLanguage,
        "api_public_package_client": PythonApiPublicPackageClientRendererLanguage,
        # Product B compiled service protocol rail over Product A DTO truth.
        "api_service_protocol": PythonApiServiceProtocolRendererLanguage,
    },
)


def _configure_python_package_strategy(
    request: MetaLanguagePackageStrategyConfigurationRequest,
) -> None:
    source = (request.materialization_source or "").strip().lower()
    package_kind = (request.package_kind or "").strip().lower()
    renderer_profile = (request.renderer_profile or "").strip().lower()
    if (
        source == ONTOLOGY_DTO_RENDERER_PROFILE
        or package_kind == ONTOLOGY_DTO_RENDERER_PROFILE
        or renderer_profile == ONTOLOGY_DTO_RENDERER_PROFILE
        or package_kind == API_DTO_RENDERER_PROFILE
        or renderer_profile == API_DTO_RENDERER_PROFILE
    ):
        request.strategy.set_policy(PythonPackagePolicy.ontology_dto_default())
        return
    if (
        source == ONTOLOGY_ORM_MODELS_MATERIALIZATION_SOURCE
        or package_kind == ONTOLOGY_ORM_MODELS_MATERIALIZATION_SOURCE
        or renderer_profile == ONTOLOGY_ORM_MODELS_RENDERER_PROFILE
    ):
        request.strategy.set_policy(PythonPackagePolicy.orm_default())
        return
    if source == "api":
        request.strategy.set_policy(PythonPackagePolicy.api_default())
        return
    request.strategy.set_policy(PythonPackagePolicy.orm_default())


# Create the Python meta plugin
PYTHON_META_PLUGIN = MetaLanguagePlugin(
    language=CodeLanguage.python,
    # ---------- Code-level parsing ----------
    code_plugin=PYTHON_CODE_PLUGIN,  # Reuse existing code plugin
    # Python -> runtime IR (used for future bidirectional workflows / migrations).
    language_to_runtime_transformer=PythonToRuntimeTransformer,
    # Runtime IR -> Python (language-specific facade lowering; renderer stays emit-only).
    runtime_to_language_transformer=RuntimeToPythonTransformer,
    # ---------- Rendering ----------
    language_renderers=_PYTHON_LANGUAGE_RENDERERS,
    default_renderer_names=("default",),
    default_renderer_names_by_profile={
        # Ontology materializations must include stable-id libraries.
        "orm_runtime": ("default", "stable_ids"),
        # Model-only ORM packages preserve storage bindings without generated invocation facades.
        "orm_models": ("default", "stable_ids"),
        # API/interface-db package rails must stay schema-only (no stable_ids/event catalog side artifacts).
        "api_runtime": ("default",),
        # API compiled product rails reuse the shared API renderer policy until a stricter product-specific
        # delta is needed.
        "api_public_package": (
            "default",
            "api_public_package_bindings",
            "api_public_package_client",
        ),
        "api_service_protocol": ("api_service_protocol",),
        "api_dto": ("default",),
        "ontology_dto": ("default", "stable_ids"),
    },
    renderer_policies_by_profile={
        "orm_runtime": PythonRenderPolicy.orm_default(),
        "orm_models": PythonRenderPolicy.orm_models_default(),
        "api_runtime": PythonRenderPolicy.api_default(),
        "api_public_package": PythonRenderPolicy.api_default(),
        "api_service_protocol": PythonRenderPolicy.api_default(),
        "api_dto": PythonRenderPolicy.api_default(),
        "ontology_dto": PythonRenderPolicy.ontology_dto_default(),
    },
    renderer_profile_input_contracts={
        "orm_runtime": RendererProfileInputContract(input_mode="graph_only"),
        "orm_models": RendererProfileInputContract(input_mode="graph_only"),
        "api_runtime": RendererProfileInputContract(input_mode="graph_only"),
        "api_dto": RendererProfileInputContract(input_mode="graph_only"),
        "ontology_dto": RendererProfileInputContract(input_mode="graph_only"),
        "api_public_package": RendererProfileInputContract(
            input_mode="graph_plus_profile_inputs",
            required_keys=(
                "api.interface_spec",
                "api.invocation_manifest",
                "api.public_package_plan",
            ),
            optional_keys=("api.external_python_type_index",),
        ),
        "api_service_protocol": RendererProfileInputContract(
            input_mode="graph_plus_profile_inputs",
            required_keys=(
                "api.interface_spec",
                "api.invocation_manifest",
                "api.public_package_plan",
                "api.service_protocol_plan",
                "api.external_python_type_index",
            ),
        ),
    },
    declared_output_producer=produce_python_declared_outputs,
    generated_delta_renderers={
        PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME: (
            PythonOrmRuntimeGeneratedDeltaRenderer
        ),
    },
    default_generated_delta_renderer_names_by_profile={
        "orm_runtime": (PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,),
    },
    # Legacy entity-level renderer wiring is intentionally empty.
    # Forward graph->code projection should be a shared Code API contract:
    # semantic event -> CodeSection/segment delta -> CodePackageDelta ->
    # FileSystem SDK apply, not per-renderer entity patch classes.
    surgical_renderers={},
    # ---------- File system ----------
    file_filter_config_factory=PythonFileFilterConfig,
    # ---------- Layout strategy ----------
    layout_strategy=PythonLayoutStrategyTemplateMixin,
    package_strategy_factory=PythonPackageStrategy,
    package_strategy_configurator=_configure_python_package_strategy,
    reserved_keyword_policies=PYTHON_RESERVED_KEYWORD_POLICIES,
)
