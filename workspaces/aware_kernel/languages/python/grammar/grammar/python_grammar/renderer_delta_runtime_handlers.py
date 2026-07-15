from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationActionBinding,
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedMaterializationEventRef,
    CodeGeneratedMaterializationTargetRef,
    CodeGeneratedRendererDeltaOperation,
    CodeGeneratedRendererDeltaOperationKind,
    CodeLanguage,
)
from aware_meta.materialization.deltas.feature_contracts import (
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderer,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationDeltaRenderResult,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_types import JsonObject

from python_grammar.layout_strategy import PythonLayoutStrategy
from python_grammar.renderer_runtime_handlers import (
    PythonRendererRuntimeHandlerImplStubs,
)
from python_grammar.renderer_runtime_handlers_meta import (
    PythonMetaRuntimeHandlersRenderer,
)


PYTHON_RUNTIME_HANDLER_GENERATED_DELTA_RENDERER_NAME = (
    "python_runtime_handler_source_artifact"
)
PYTHON_RUNTIME_HANDLER_ARTIFACT_PAYLOAD_KEY = "python_runtime_handler_source_artifact"
PYTHON_RUNTIME_HANDLER_ARTIFACT_PAYLOAD_CONTRACT_VERSION = (
    "aware.python.runtime-handler-source-artifact-payload.v0"
)
PYTHON_RUNTIME_HANDLER_IMPL_KIND = "runtime_handlers_impl"
PYTHON_RUNTIME_HANDLER_META_KIND = "runtime_handlers_meta"
PYTHON_RUNTIME_HANDLER_MATERIALIZATION_SOURCE = "runtime_handlers"
PYTHON_RUNTIME_HANDLER_RENDERER_KEY = "python.runtime_handler.source_artifact"
PYTHON_RUNTIME_HANDLER_ARTIFACT_FAMILY = "runtime_handler_materialization"
_SUPPORTED_RENDERER_KINDS = frozenset(
    {PYTHON_RUNTIME_HANDLER_IMPL_KIND, PYTHON_RUNTIME_HANDLER_META_KIND}
)


@dataclass(frozen=True, slots=True)
class PythonRuntimeHandlerSourceArtifactPayload:
    """Graph and authored-source truth for one runtime-handler artifact."""

    relative_path: str
    renderer_kind: str
    runtime_graph: ObjectConfigGraph
    language_graph: ObjectConfigGraph
    source_graph: ObjectConfigGraph | None = None
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    class_config: ClassConfig | None = None
    baseline_source_text: str | None = None
    import_root: str | None = None
    stable_ids_import_root: str | None = None
    function_impl_ownership: str = "authored"
    function_impl_parity_policy: str = "off"
    external_language_graphs: tuple[ObjectConfigGraph, ...] = ()
    import_overrides: tuple[tuple[str, str], ...] = ()
    contract_version: str = PYTHON_RUNTIME_HANDLER_ARTIFACT_PAYLOAD_CONTRACT_VERSION

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> "PythonRuntimeHandlerSourceArtifactPayload":
        runtime_graph = _model(value.get("runtime_graph"), ObjectConfigGraph)
        if runtime_graph is None:
            raise ValueError("Runtime-handler payload requires runtime_graph.")
        language_graph = _model(value.get("language_graph"), ObjectConfigGraph)
        if language_graph is None:
            raise ValueError("Runtime-handler payload requires language_graph.")
        return cls(
            contract_version=(
                _optional_text(value.get("contract_version"))
                or PYTHON_RUNTIME_HANDLER_ARTIFACT_PAYLOAD_CONTRACT_VERSION
            ),
            relative_path=_optional_text(value.get("relative_path")) or "",
            renderer_kind=_optional_text(value.get("renderer_kind")) or "",
            runtime_graph=runtime_graph,
            language_graph=language_graph,
            source_graph=_model(value.get("source_graph"), ObjectConfigGraph),
            generated_ocg_node_manifest=_model(
                value.get("generated_ocg_node_manifest"),
                GeneratedObjectConfigGraphNodeManifest,
            ),
            class_config=_model(value.get("class_config"), ClassConfig),
            baseline_source_text=_text(value.get("baseline_source_text")),
            import_root=_optional_text(value.get("import_root")),
            stable_ids_import_root=_optional_text(value.get("stable_ids_import_root")),
            function_impl_ownership=(
                _optional_text(value.get("function_impl_ownership")) or "authored"
            ),
            function_impl_parity_policy=(
                _optional_text(value.get("function_impl_parity_policy")) or "off"
            ),
            external_language_graphs=_models(
                value.get("external_language_graphs"),
                ObjectConfigGraph,
            ),
            import_overrides=_string_pairs(value.get("import_overrides")),
        )

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "contract_version": self.contract_version,
            "relative_path": self.relative_path,
            "renderer_kind": self.renderer_kind,
            "runtime_graph": self.runtime_graph.model_dump(
                mode="json",
                exclude_none=True,
            ),
            "language_graph": self.language_graph.model_dump(
                mode="json",
                exclude_none=True,
            ),
            "baseline_source_text": self.baseline_source_text,
            "import_root": self.import_root,
            "stable_ids_import_root": self.stable_ids_import_root,
            "function_impl_ownership": self.function_impl_ownership,
            "function_impl_parity_policy": self.function_impl_parity_policy,
            "external_language_graphs": _model_payloads(self.external_language_graphs),
            "import_overrides": self.import_overrides,
        }
        if self.source_graph is not None:
            payload["source_graph"] = self.source_graph.model_dump(
                mode="json",
                exclude_none=True,
            )
        if self.class_config is not None:
            payload["class_config"] = self.class_config.model_dump(
                mode="json",
                exclude_none=True,
            )
        if self.generated_ocg_node_manifest is not None:
            payload["generated_ocg_node_manifest"] = (
                self.generated_ocg_node_manifest.model_dump(
                    mode="json",
                    exclude_none=True,
                )
            )
        return payload


class PythonRuntimeHandlerGeneratedDeltaRenderer(
    MetaLanguageGeneratedMaterializationDeltaRenderer
):
    renderer_key = PYTHON_RUNTIME_HANDLER_GENERATED_DELTA_RENDERER_NAME
    renderer_profile = "runtime_handlers"
    materialization_source = PYTHON_RUNTIME_HANDLER_MATERIALIZATION_SOURCE

    def __init__(self) -> None:
        self._prepared_renderers: dict[
            tuple[object, ...],
            PythonRendererRuntimeHandlerImplStubs | PythonMetaRuntimeHandlersRenderer,
        ] = {}

    def supports_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> bool:
        payload = _artifact_payload(request.operation)
        requested_kind = request.renderer_kind or request.context.renderer_kind
        return (
            payload is not None
            and payload.renderer_kind in _SUPPORTED_RENDERER_KINDS
            and (requested_kind is None or requested_kind == payload.renderer_kind)
            and request.operation.ontology_subject_kind == "function_impl"
            and request.operation.operation_family in {"create", "update", "delete"}
        )

    def render_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
        payload = _artifact_payload(request.operation)
        if payload is None or not self.supports_generated_materialization_delta(
            request
        ):
            return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
                reason="python_runtime_handler_generated_delta_payload_not_supported",
            )
        source = _render_source_with_renderer(
            delta_renderer=self,
            payload=payload,
        )
        context = _context_with_payload(request.context, payload=payload)
        operation = request.operation
        event_key = meta_provider_delta_world_change_event_key(operation=operation)
        target = _target_ref(operation=operation, context=context, payload=payload)
        package_delta = _package_delta(
            operation=operation,
            context=context,
            payload=payload,
            target=target,
            source=source,
        )
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
            delta_request=_delta_request(
                operation=operation,
                context=context,
                event_key=event_key,
                target=target,
                payload=payload,
            ),
            result=_delta_result(
                operation=operation,
                context=context,
                event_key=event_key,
                target=target,
                payload=payload,
                source=source,
                package_delta=package_delta,
            ),
            reason="python_runtime_handler_source_artifact_generated_delta_rendered",
        )


def _render_source_with_renderer(
    *,
    delta_renderer: PythonRuntimeHandlerGeneratedDeltaRenderer,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
) -> str:
    renderer = _prepared_renderer(
        delta_renderer=delta_renderer,
        payload=payload,
    )
    if payload.renderer_kind == PYTHON_RUNTIME_HANDLER_IMPL_KIND:
        if payload.class_config is None:
            raise ValueError("Runtime handler impl payload requires class_config.")
        if not isinstance(renderer, PythonRendererRuntimeHandlerImplStubs):
            raise TypeError("Prepared runtime handler impl renderer has wrong kind.")
        return renderer.render_impl_source_artifact(
            class_config=payload.class_config,
            relative_path=Path(payload.relative_path),
            baseline_source_text=payload.baseline_source_text or "",
        )
    if not isinstance(renderer, PythonMetaRuntimeHandlersRenderer):
        raise TypeError("Prepared Meta runtime handler renderer has wrong kind.")
    return renderer.render_provider_source_artifact(
        relative_path=Path(payload.relative_path),
    )


def _prepared_renderer(
    *,
    delta_renderer: PythonRuntimeHandlerGeneratedDeltaRenderer,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
) -> PythonRendererRuntimeHandlerImplStubs | PythonMetaRuntimeHandlersRenderer:
    key = _prepared_renderer_key(payload=payload)
    cached = delta_renderer._prepared_renderers.get(key)
    if cached is not None:
        return cached
    layout = PythonLayoutStrategy(
        Path("."),
        generated_ocg_node_manifest=payload.generated_ocg_node_manifest,
        import_root=payload.import_root,
    )
    layout.bind_graph(payload.language_graph)
    policy: dict[str, object] = {
        "stable_ids_source_graph": payload.runtime_graph,
        "function_impl_ownership": payload.function_impl_ownership,
        "function_impl_parity_policy": payload.function_impl_parity_policy,
    }
    if payload.source_graph is not None:
        policy["function_impl_source_graph"] = payload.source_graph
    if payload.stable_ids_import_root is not None:
        policy["stable_ids_import_root"] = payload.stable_ids_import_root
    if payload.renderer_kind == PYTHON_RUNTIME_HANDLER_IMPL_KIND:
        if payload.class_config is None:
            raise ValueError("Runtime handler impl payload requires class_config.")
        renderer = PythonRendererRuntimeHandlerImplStubs(layout)
        renderer.set_policy(policy)
        _configure_renderer(renderer=renderer, payload=payload)
    else:
        renderer = PythonMetaRuntimeHandlersRenderer(layout)
        renderer.set_policy(policy)
        _configure_renderer(renderer=renderer, payload=payload)
    delta_renderer._prepared_renderers[key] = renderer
    return renderer


def _prepared_renderer_key(
    *,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
) -> tuple[object, ...]:
    return (
        payload.renderer_kind,
        _graph_instance_key(payload.runtime_graph),
        _graph_instance_key(payload.language_graph),
        _graph_instance_key(payload.source_graph),
        tuple(_graph_instance_key(graph) for graph in payload.external_language_graphs),
        (
            payload.generated_ocg_node_manifest.model_dump_json()
            if payload.generated_ocg_node_manifest is not None
            else None
        ),
        payload.import_root,
        payload.stable_ids_import_root,
        payload.function_impl_ownership,
        payload.function_impl_parity_policy,
        payload.import_overrides,
    )


def _configure_renderer(
    *,
    renderer: PythonRendererRuntimeHandlerImplStubs | PythonMetaRuntimeHandlersRenderer,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
) -> None:
    renderer.import_overrides = dict(payload.import_overrides)
    renderer.set_external_graphs(list(payload.external_language_graphs))
    renderer.set_external_class_lookup(
        {
            cls.id: cls
            for graph in payload.external_language_graphs
            for cls in _graph_classes(graph)
        }
    )
    renderer.bind_object_config_graph(payload.language_graph)


def _context_with_payload(
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    *,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root or ".",
        target_language=context.target_language or "python",
        target_language_plugin_id=context.target_language_plugin_id or "python",
        renderer_profile=context.renderer_profile,
        renderer_kind=payload.renderer_kind,
        materialization_source=PYTHON_RUNTIME_HANDLER_MATERIALIZATION_SOURCE,
        product_intent=context.product_intent or payload.renderer_kind,
        artifact_family=context.artifact_family
        or PYTHON_RUNTIME_HANDLER_ARTIFACT_FAMILY,
        artifact_role=context.artifact_role or _artifact_role(payload.renderer_kind),
        target_hints=context.target_hints,
    )


def _target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
) -> CodeGeneratedMaterializationTargetRef:
    return CodeGeneratedMaterializationTargetRef(
        target_key=f"python_runtime_handler:{payload.renderer_kind}:{operation.semantic_key}",
        provider_key="aware_meta",
        semantic_owner="aware_meta.function_impl",
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=PYTHON_RUNTIME_HANDLER_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        relative_path=payload.relative_path,
        metadata=_json_object(
            {
                "renderer_kind": payload.renderer_kind,
                "function_impl_ownership": payload.function_impl_ownership,
                "delta_form": "source_artifact",
            }
        ),
    )


def _delta_request(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
) -> CodeGeneratedMaterializationDeltaRequest:
    return CodeGeneratedMaterializationDeltaRequest(
        provider_key="aware_meta",
        semantic_owner="aware_meta.function_impl",
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        product_intent=context.product_intent,
        events=[
            CodeGeneratedMaterializationEventRef(
                event_key=event_key,
                semantic_key=operation.semantic_key,
                verb=operation.operation_family,
                subject_type=operation.ontology_subject_kind,
                source="aware_meta.provider_delta.semantic_world_change",
                source_refs=list(_sorted_unique(operation.source_refs)),
            )
        ],
        action_bindings=[
            CodeGeneratedMaterializationActionBinding(
                action_key=f"aware_meta.python_runtime_handler:{operation.operation_key}",
                event_key=event_key,
                target=target,
                policy_key="aware_meta.generated_materialization.python_runtime_handler",
                renderer_key=PYTHON_RUNTIME_HANDLER_RENDERER_KEY,
            )
        ],
        targets=[target],
        metadata=_json_object({"renderer_kind": payload.renderer_kind}),
    )


def _package_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
    target: CodeGeneratedMaterializationTargetRef,
    source: str,
) -> CodePackageDelta:
    baseline = payload.baseline_source_text
    return CodePackageDelta(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
        authority_kind=CodePackageDeltaAuthorityKind.semantic_materialization.value,
        paths=[
            CodePackageDeltaPath(
                relative_path=payload.relative_path,
                kind=(
                    CodePackageDeltaKind.create
                    if baseline is None
                    else CodePackageDeltaKind.update
                ),
                content_text=source,
                before_hash=_digest(baseline) if baseline is not None else None,
                after_hash=_digest(source),
                language=CodeLanguage.python,
                is_structural=True,
                path_role=CodePackagePathRole.generated_code,
                metadata=_json_object(
                    {
                        "semantic_key": operation.semantic_key,
                        "renderer_kind": payload.renderer_kind,
                        "function_impl_ownership": payload.function_impl_ownership,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "provider_key": "aware_meta",
                "renderer_kind": payload.renderer_kind,
                "materialization_source": context.materialization_source,
            }
        ),
    )


def _delta_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
    payload: PythonRuntimeHandlerSourceArtifactPayload,
    source: str,
    package_delta: CodePackageDelta,
) -> CodeGeneratedMaterializationDeltaResult:
    digest = _digest(source)
    baseline_digest = (
        _digest(payload.baseline_source_text)
        if payload.baseline_source_text is not None
        else None
    )
    renderer_operation = CodeGeneratedRendererDeltaOperation(
        operation_key=f"python_runtime_handler:{operation.operation_key}",
        kind=CodeGeneratedRendererDeltaOperationKind.replace_section,
        target=target,
        renderer_key=PYTHON_RUNTIME_HANDLER_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        before_hash=baseline_digest,
        after_hash=digest,
        content_text=source,
        replacement_text=source,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=["python_runtime_handler_render_equivalent"],
        metadata=_json_object({"renderer_kind": payload.renderer_kind}),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"python_runtime_handler:{operation.operation_key}",
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        target=target,
        package_delta=package_delta,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        before_hash=baseline_digest,
        after_hash=digest,
        renderer_operations=[renderer_operation],
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        metadata=_json_object({"renderer_kind": payload.renderer_kind}),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key="aware_meta",
        semantic_owner="aware_meta.function_impl",
        available=True,
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        entries=[entry],
        diagnostics=["python_runtime_handler_render_equivalent"],
        fingerprint=digest,
        metadata=_json_object({"renderer_kind": payload.renderer_kind}),
    )


def _artifact_payload(
    operation: MetaProviderDeltaTypedOperation,
) -> PythonRuntimeHandlerSourceArtifactPayload | None:
    for source in (operation.current, operation.baseline):
        value = source.get(PYTHON_RUNTIME_HANDLER_ARTIFACT_PAYLOAD_KEY)
        if isinstance(value, PythonRuntimeHandlerSourceArtifactPayload):
            return value
        if isinstance(value, Mapping):
            return PythonRuntimeHandlerSourceArtifactPayload.from_mapping(value)
    return None


def _graph_classes(graph: ObjectConfigGraph) -> tuple[ClassConfig, ...]:
    return tuple(
        node.class_config
        for node in graph.object_config_graph_nodes
        if node.class_config is not None
    )


def _graph_instance_key(graph: ObjectConfigGraph | None) -> tuple[str, str, int] | None:
    if graph is None:
        return None
    return (
        graph.hash or "",
        str(graph.id),
        len(graph.object_config_graph_nodes),
    )


def _artifact_role(renderer_kind: str) -> str:
    if renderer_kind == PYTHON_RUNTIME_HANDLER_META_KIND:
        return "meta_runtime_handler_provider"
    return "runtime_handler_impl"


def _model(value: object, model_type: type[Any]) -> Any | None:
    if isinstance(value, model_type):
        return value
    if isinstance(value, Mapping):
        return model_type.model_validate(value)
    return None


def _models(value: object, model_type: type[Any]) -> tuple[Any, ...]:
    if not isinstance(value, tuple | list):
        return ()
    return tuple(
        model for item in value if (model := _model(item, model_type)) is not None
    )


def _model_payloads(models: Iterable[object]) -> tuple[object, ...]:
    return tuple(
        cast(Any, model).model_dump(mode="json", exclude_none=True) for model in models
    )


def _string_pairs(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), str(item)) for key, item in value.items()))
    if not isinstance(value, tuple | list):
        return ()
    return tuple(
        sorted(
            (str(item[0]), str(item[1]))
            for item in value
            if isinstance(item, tuple | list) and len(item) == 2
        )
    )


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip() or None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _sorted_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "PYTHON_RUNTIME_HANDLER_ARTIFACT_PAYLOAD_KEY",
    "PYTHON_RUNTIME_HANDLER_GENERATED_DELTA_RENDERER_NAME",
    "PYTHON_RUNTIME_HANDLER_IMPL_KIND",
    "PYTHON_RUNTIME_HANDLER_META_KIND",
    "PythonRuntimeHandlerGeneratedDeltaRenderer",
    "PythonRuntimeHandlerSourceArtifactPayload",
]
