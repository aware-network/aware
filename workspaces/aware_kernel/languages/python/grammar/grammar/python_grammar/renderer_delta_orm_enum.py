from __future__ import annotations

from aware_meta.enum.config.deltas.generated_materialization import (
    META_PYTHON_ORM_ENUM_MATERIALIZATION_SOURCE,
    META_PYTHON_ORM_ENUM_RENDERER_PROFILE,
    MetaPythonOrmEnumGeneratedMaterializationContext,
    python_orm_generated_materialization_delta_from_enum_config_typed_operation,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationDeltaRenderResult,
)


PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME = "python_orm_runtime"


def supports_python_orm_enum_generated_delta(
    request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
) -> bool:
    operation = request.operation
    if operation.ontology_subject_kind == "enum":
        return operation.operation_family in {"create", "delete", "update"}
    if operation.ontology_subject_kind == "enum_option":
        return operation.operation_family in {"create", "delete", "update"}
    return False


def render_python_orm_enum_generated_delta(
    request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
    if not supports_python_orm_enum_generated_delta(request):
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
            reason="python_orm_enum_generated_delta_operation_not_supported",
        )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            request.operation,
            context=_context_with_defaults(request.context),
            allow_language_plugin=False,
            language_plugin_delta_renderer=PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,
        )
    )
    return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
        delta_request=evidence.delta_request,
        result=evidence.result,
        reason="python_orm_runtime_enum_generated_delta_rendered",
    )


def _context_with_defaults(
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> MetaPythonOrmEnumGeneratedMaterializationContext:
    return MetaPythonOrmEnumGeneratedMaterializationContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        target_language=context.target_language or "python",
        renderer_profile=(
            context.renderer_profile or META_PYTHON_ORM_ENUM_RENDERER_PROFILE
        ),
        materialization_source=(
            context.materialization_source or META_PYTHON_ORM_ENUM_MATERIALIZATION_SOURCE
        ),
        artifact_family=context.artifact_family or "ocg_language_materialization",
        artifact_role=context.artifact_role or "python_orm_model",
    )


__all__ = [
    "render_python_orm_enum_generated_delta",
    "supports_python_orm_enum_generated_delta",
]
