from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage as OntologyCodeLanguage
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
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
from aware_meta.materialization.external_import_overrides import (
    language_external_import_overrides,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_types import JsonObject

from python_grammar.layout_strategy import PythonLayoutStrategy
from python_grammar.renderer import PythonRenderer
from python_grammar.renderer_policy import PythonRenderPolicy


PYTHON_STRUCTURAL_GENERATED_DELTA_RENDERER_NAME = "python_structural_source_artifact"
PYTHON_STRUCTURAL_SOURCE_ARTIFACT_PAYLOAD_KEY = "python_structural_source_artifact"
PYTHON_STRUCTURAL_SOURCE_ARTIFACT_PAYLOAD_CONTRACT_VERSION = (
    "aware.python.structural-source-artifact-payload.v1"
)
PYTHON_STRUCTURAL_RENDERER_KEY = "python.structural.source_artifact"
PYTHON_STRUCTURAL_ARTIFACT_FAMILY = "ocg_language_materialization"
PYTHON_STRUCTURAL_ARTIFACT_ROLE = "python_structural_source_artifact"
PYTHON_ORM_MODELS_RENDERER_PROFILE = "orm_models"
PYTHON_ONTOLOGY_DTO_RENDERER_PROFILE = "ontology_dto"
PYTHON_ORM_MODELS_MATERIALIZATION_SOURCE = "ontology_orm_models"
PYTHON_ONTOLOGY_DTO_MATERIALIZATION_SOURCE = "ontology_dto"
_SUPPORTED_PROFILES = frozenset(
    {
        PYTHON_ORM_MODELS_RENDERER_PROFILE,
        PYTHON_ONTOLOGY_DTO_RENDERER_PROFILE,
    }
)


@dataclass(frozen=True, slots=True)
class PythonStructuralSourceArtifactPayload:
    """Python-owned graph/layout input for one generated source file."""

    relative_path: str
    renderer_profile: str
    materialization_source: str
    import_root: str | None = None
    owner_key: str | None = None
    enums: tuple[EnumConfig, ...] = ()
    classes: tuple[ClassConfig, ...] = ()
    functions: tuple[FunctionConfig, ...] = ()
    relationships: tuple[ClassConfigRelationship, ...] = ()
    class_lookup: tuple[ClassConfig, ...] = ()
    language_graph: ObjectConfigGraph | None = None
    external_language_graphs: tuple[ObjectConfigGraph, ...] = ()
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    import_overrides: tuple[tuple[str, str], ...] = ()
    delete_source_artifact: bool = False
    contract_version: str = PYTHON_STRUCTURAL_SOURCE_ARTIFACT_PAYLOAD_CONTRACT_VERSION

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
    ) -> "PythonStructuralSourceArtifactPayload":
        source_container = _mapping(value.get("source_container"))
        return cls(
            contract_version=(
                _optional_text(value.get("contract_version"))
                or PYTHON_STRUCTURAL_SOURCE_ARTIFACT_PAYLOAD_CONTRACT_VERSION
            ),
            relative_path=_optional_text(value.get("relative_path")) or "",
            renderer_profile=(
                _optional_text(value.get("renderer_profile"))
                or PYTHON_ORM_MODELS_RENDERER_PROFILE
            ),
            materialization_source=(
                _optional_text(value.get("materialization_source"))
                or PYTHON_ORM_MODELS_MATERIALIZATION_SOURCE
            ),
            import_root=_optional_text(value.get("import_root")),
            owner_key=_optional_text(value.get("owner_key")),
            enums=_models(source_container.get("enums"), EnumConfig),
            classes=_models(source_container.get("classes"), ClassConfig),
            functions=_models(source_container.get("functions"), FunctionConfig),
            relationships=_models(
                source_container.get("relationships"),
                ClassConfigRelationship,
            ),
            class_lookup=_models(value.get("class_lookup"), ClassConfig),
            language_graph=_model(value.get("language_graph"), ObjectConfigGraph),
            external_language_graphs=_models(
                value.get("external_language_graphs"),
                ObjectConfigGraph,
            ),
            generated_ocg_node_manifest=_model(
                value.get("generated_ocg_node_manifest"),
                GeneratedObjectConfigGraphNodeManifest,
            ),
            import_overrides=_string_pairs(value.get("import_overrides")),
            delete_source_artifact=bool(value.get("delete_source_artifact", False)),
        )

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "contract_version": self.contract_version,
            "relative_path": self.relative_path,
            "renderer_profile": self.renderer_profile,
            "materialization_source": self.materialization_source,
            "import_root": self.import_root,
            "owner_key": self.owner_key,
            "delete_source_artifact": self.delete_source_artifact,
            "source_container": {
                "enums": _model_payloads(self.enums),
                "classes": _model_payloads(self.classes),
                "functions": _model_payloads(self.functions),
                "relationships": _model_payloads(self.relationships),
            },
            "class_lookup": _model_payloads(self.class_lookup),
            "import_overrides": self.import_overrides,
        }
        if self.language_graph is not None:
            payload["language_graph"] = self.language_graph.model_dump(
                mode="json",
                exclude_none=True,
            )
        if self.external_language_graphs:
            payload["external_language_graphs"] = _model_payloads(
                self.external_language_graphs
            )
        if self.generated_ocg_node_manifest is not None:
            payload["generated_ocg_node_manifest"] = (
                self.generated_ocg_node_manifest.model_dump(
                    mode="json",
                    exclude_none=True,
                )
            )
        return payload

    @property
    def meta_objects(
        self,
    ) -> tuple[
        EnumConfig | ClassConfig | FunctionConfig | ClassConfigRelationship,
        ...,
    ]:
        return (
            *self.enums,
            *self.classes,
            *self.relationships,
            *self.functions,
        )


def build_python_structural_source_artifact_payload(
    *,
    language_graph: ObjectConfigGraph,
    relative_path: str,
    renderer_profile: str,
    materialization_source: str,
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
    external_language_graphs: tuple[ObjectConfigGraph, ...] = (),
    import_root: str | None = None,
    owner_key: str | None = None,
) -> PythonStructuralSourceArtifactPayload | None:
    """Resolve one Python source container from language graph layout truth."""

    layout = PythonLayoutStrategy(
        Path("."),
        generated_ocg_node_manifest=generated_ocg_node_manifest,
        import_root=import_root,
    )
    layout.bind_graph(language_graph)
    target_path = Path(relative_path)
    class_lookup = _class_lookup_from_graphs(
        (language_graph, *external_language_graphs)
    )
    import_overrides = language_external_import_overrides(
        target_language_plugin_id=OntologyCodeLanguage.python,
        materialization_source=materialization_source,
        language_external_graphs=external_language_graphs,
    )
    classes = tuple(
        sorted(
            (
                cls
                for cls in _graph_classes(language_graph)
                if _same_path(layout.get_class_file_path(cls), target_path)
            ),
            key=lambda item: item.name,
        )
    )
    enums = tuple(
        sorted(
            (
                enum
                for enum in _graph_enums(language_graph)
                if _same_path(layout.get_enum_file_path(enum), target_path)
            ),
            key=lambda item: item.name,
        )
    )
    relationships = tuple(
        sorted(
            (
                relationship
                for relationship in _graph_relationships(language_graph)
                if (
                    (source_class := class_lookup.get(relationship.class_config_id))
                    is not None
                    and _same_path(
                        layout.get_class_file_path(source_class),
                        target_path,
                    )
                )
            ),
            key=lambda item: (str(item.class_config_id), str(item.id)),
        )
    )
    class_owned_function_ids = {
        function_id
        for cls in _graph_classes(language_graph)
        for link in cls.class_config_function_configs
        for function_id in (
            link.function_config_id
            or (link.function_config.id if link.function_config is not None else None),
        )
        if function_id is not None
    }
    functions = tuple(
        sorted(
            (
                function
                for function in _graph_functions(language_graph)
                if function.id not in class_owned_function_ids
                and _same_path(
                    layout.get_function_file_path(function),
                    target_path,
                )
            ),
            key=lambda item: item.name,
        )
    )
    if not enums and not classes and not functions and not relationships:
        return None
    return PythonStructuralSourceArtifactPayload(
        relative_path=relative_path,
        renderer_profile=renderer_profile,
        materialization_source=materialization_source,
        import_root=import_root,
        owner_key=owner_key,
        enums=enums,
        classes=classes,
        functions=functions,
        relationships=relationships,
        class_lookup=tuple(class_lookup.values()),
        language_graph=language_graph,
        external_language_graphs=external_language_graphs,
        generated_ocg_node_manifest=generated_ocg_node_manifest,
        import_overrides=tuple(sorted(import_overrides.items())),
    )


class PythonStructuralGeneratedDeltaRenderer(
    MetaLanguageGeneratedMaterializationDeltaRenderer
):
    renderer_key = PYTHON_STRUCTURAL_GENERATED_DELTA_RENDERER_NAME
    renderer_profile = PYTHON_ORM_MODELS_RENDERER_PROFILE
    materialization_source = PYTHON_ORM_MODELS_MATERIALIZATION_SOURCE

    def supports_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> bool:
        profile = request.renderer_profile or request.context.renderer_profile
        return (
            profile in _SUPPORTED_PROFILES
            and request.operation.operation_family in {"create", "update", "delete"}
            and _source_artifact_payload(request.operation) is not None
        )

    def render_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
        payload = _source_artifact_payload(request.operation)
        if payload is None or not self.supports_generated_materialization_delta(
            request
        ):
            return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
                reason="python_structural_generated_delta_payload_not_supported",
            )
        context = _context_with_payload(request.context, payload=payload)
        content_text = _source_artifact_text(payload=payload)
        if content_text is None and not payload.delete_source_artifact:
            return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
                reason="python_structural_generated_delta_source_container_empty",
            )
        operation = request.operation
        event_key = meta_provider_delta_world_change_event_key(operation=operation)
        target = _target_ref(operation=operation, context=context, payload=payload)
        package_delta = _package_delta(
            operation=operation,
            context=context,
            payload=payload,
            target=target,
            content_text=content_text,
        )
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
            delta_request=_delta_request(
                operation=operation,
                context=context,
                event_key=event_key,
                target=target,
            ),
            result=_delta_result(
                operation=operation,
                context=context,
                event_key=event_key,
                target=target,
                content_text=content_text,
                package_delta=package_delta,
            ),
            reason="python_structural_source_artifact_generated_delta_rendered",
        )


def _source_artifact_text(
    *,
    payload: PythonStructuralSourceArtifactPayload,
) -> str | None:
    if payload.delete_source_artifact:
        return None
    graph = payload.language_graph
    if graph is None or not payload.meta_objects:
        return None
    layout = PythonLayoutStrategy(
        Path("."),
        generated_ocg_node_manifest=payload.generated_ocg_node_manifest,
        import_root=payload.import_root,
    )
    layout.bind_graph(graph)
    renderer = PythonRenderer(layout, policy=_policy(payload.renderer_profile))
    renderer.import_overrides = dict(payload.import_overrides)
    renderer.set_external_graphs(list(payload.external_language_graphs))
    renderer.set_external_class_lookup(
        _class_lookup_from_graphs(payload.external_language_graphs)
    )
    overlay = next(
        (
            item
            for item in graph.object_config_graph_overlays
            if item.language == OntologyCodeLanguage.python
        ),
        None,
    )
    if overlay is not None:
        renderer.set_language_overlay(overlay)
    renderer.bind_object_config_graph(graph)
    class_lookup = {item.id: item for item in payload.class_lookup}
    return renderer.render_source_artifact(
        meta_objects=payload.meta_objects,
        relative_path=Path(payload.relative_path),
        class_lookup=class_lookup,
    )


def _policy(renderer_profile: str) -> PythonRenderPolicy:
    if renderer_profile == PYTHON_ORM_MODELS_RENDERER_PROFILE:
        return PythonRenderPolicy.orm_models_default()
    if renderer_profile == PYTHON_ONTOLOGY_DTO_RENDERER_PROFILE:
        return PythonRenderPolicy.ontology_dto_default()
    raise ValueError(
        f"Unsupported Python structural renderer profile: {renderer_profile}"
    )


def _context_with_payload(
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    *,
    payload: PythonStructuralSourceArtifactPayload,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root or ".",
        target_language=context.target_language or "python",
        target_language_plugin_id=context.target_language_plugin_id or "python",
        renderer_profile=payload.renderer_profile,
        materialization_source=payload.materialization_source,
        product_intent=context.product_intent or payload.renderer_profile,
        artifact_family=context.artifact_family or PYTHON_STRUCTURAL_ARTIFACT_FAMILY,
        artifact_role=context.artifact_role or PYTHON_STRUCTURAL_ARTIFACT_ROLE,
        target_hints=context.target_hints,
    )


def _target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    payload: PythonStructuralSourceArtifactPayload,
) -> CodeGeneratedMaterializationTargetRef:
    return CodeGeneratedMaterializationTargetRef(
        target_key=(
            f"python_structural:{payload.renderer_profile}:"
            f"{payload.owner_key or operation.semantic_key}"
        ),
        provider_key="aware_meta",
        semantic_owner="aware_meta.ocg",
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=PYTHON_STRUCTURAL_RENDERER_KEY,
        renderer_profile=payload.renderer_profile,
        materialization_source=payload.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        relative_path=payload.relative_path,
        metadata=_json_object(
            {
                "owner_key": payload.owner_key,
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
) -> CodeGeneratedMaterializationDeltaRequest:
    return CodeGeneratedMaterializationDeltaRequest(
        provider_key="aware_meta",
        semantic_owner="aware_meta.ocg",
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
                action_key=f"aware_meta.python_structural:{operation.operation_key}",
                event_key=event_key,
                target=target,
                policy_key="aware_meta.generated_materialization.python_structural",
                renderer_key=PYTHON_STRUCTURAL_RENDERER_KEY,
            )
        ],
        targets=[target],
        metadata=_json_object({"delta_form": "source_artifact"}),
    )


def _package_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    payload: PythonStructuralSourceArtifactPayload,
    target: CodeGeneratedMaterializationTargetRef,
    content_text: str | None,
) -> CodePackageDelta:
    deleting = payload.delete_source_artifact
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
                    CodePackageDeltaKind.delete
                    if deleting
                    else (
                        CodePackageDeltaKind.create
                        if operation.operation_family == "create"
                        else CodePackageDeltaKind.update
                    )
                ),
                content_text=content_text,
                after_hash=(
                    _digest(content_text) if content_text is not None else None
                ),
                language=CodeLanguage.python,
                is_structural=True,
                path_role=CodePackagePathRole.generated_code,
                metadata=_json_object(
                    {
                        "semantic_key": operation.semantic_key,
                        "renderer_key": PYTHON_STRUCTURAL_RENDERER_KEY,
                        "renderer_profile": payload.renderer_profile,
                        "delta_form": "source_artifact",
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "provider_key": "aware_meta",
                "renderer_profile": payload.renderer_profile,
                "materialization_source": payload.materialization_source,
                "delta_form": "source_artifact",
            }
        ),
    )


def _delta_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
    content_text: str | None,
    package_delta: CodePackageDelta,
) -> CodeGeneratedMaterializationDeltaResult:
    digest = _digest(content_text) if content_text is not None else None
    renderer_operation = CodeGeneratedRendererDeltaOperation(
        operation_key=f"python_structural:{operation.operation_key}",
        kind=CodeGeneratedRendererDeltaOperationKind.replace_section,
        target=target,
        renderer_key=PYTHON_STRUCTURAL_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        after_hash=digest,
        content_text=content_text,
        replacement_text=content_text,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=["python_structural_source_artifact_render_equivalent"],
        metadata=_json_object({"delta_form": "source_artifact"}),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"python_structural:{operation.operation_key}",
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        target=target,
        package_delta=package_delta,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        after_hash=digest,
        renderer_operations=[renderer_operation],
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        metadata=_json_object({"delta_form": "source_artifact"}),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key="aware_meta",
        semantic_owner="aware_meta.ocg",
        available=True,
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        entries=[entry],
        diagnostics=["python_structural_source_artifact_render_equivalent"],
        fingerprint=digest,
        metadata=_json_object({"delta_form": "source_artifact"}),
    )


def _source_artifact_payload(
    operation: MetaProviderDeltaTypedOperation,
) -> PythonStructuralSourceArtifactPayload | None:
    for source in (operation.current, operation.baseline):
        value = source.get(PYTHON_STRUCTURAL_SOURCE_ARTIFACT_PAYLOAD_KEY)
        if isinstance(value, PythonStructuralSourceArtifactPayload):
            return value
        if isinstance(value, Mapping):
            return PythonStructuralSourceArtifactPayload.from_mapping(value)
    return None


def _graph_classes(graph: ObjectConfigGraph) -> tuple[ClassConfig, ...]:
    return tuple(
        node.class_config
        for node in graph.object_config_graph_nodes
        if node.type == ObjectConfigGraphNodeType.class_
        and node.class_config is not None
    )


def _graph_enums(graph: ObjectConfigGraph) -> tuple[EnumConfig, ...]:
    return tuple(
        node.enum_config
        for node in graph.object_config_graph_nodes
        if node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None
    )


def _graph_functions(graph: ObjectConfigGraph) -> tuple[FunctionConfig, ...]:
    return tuple(
        function
        for node in graph.object_config_graph_nodes
        if node.type == ObjectConfigGraphNodeType.function
        if (function := get_node_function_config(node)) is not None
    )


def _graph_relationships(
    graph: ObjectConfigGraph,
) -> tuple[ClassConfigRelationship, ...]:
    relationships: list[ClassConfigRelationship] = []
    seen: set[UUID] = set()
    for node in graph.object_config_graph_nodes:
        relationship = node.class_config_relationship
        if (
            node.type == ObjectConfigGraphNodeType.relationship
            and relationship is not None
            and relationship.id not in seen
        ):
            relationships.append(relationship)
            seen.add(relationship.id)
    for graph_relationship in graph.object_config_graph_relationships:
        for relationship in graph_relationship.class_config_relationships:
            if relationship.id not in seen:
                relationships.append(relationship)
                seen.add(relationship.id)
    return tuple(relationships)


def _class_lookup_from_graphs(
    graphs: Iterable[ObjectConfigGraph],
) -> dict[UUID, ClassConfig]:
    return {cls.id: cls for graph in graphs for cls in _graph_classes(graph)}


def _same_path(left: Path, right: Path) -> bool:
    return left.as_posix().lstrip("./") == right.as_posix().lstrip("./")


def _model_payloads(models: Iterable[object]) -> tuple[object, ...]:
    return tuple(
        cast(Any, model).model_dump(mode="json", exclude_none=True) for model in models
    )


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


def _string_pairs(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), str(item)) for key, item in value.items()))
    if not isinstance(value, tuple | list):
        return ()
    pairs: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple | list) or len(item) != 2:
            continue
        left, right = item
        if isinstance(left, str) and isinstance(right, str):
            pairs.append((left, right))
    return tuple(sorted(pairs))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _sorted_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "PYTHON_ONTOLOGY_DTO_MATERIALIZATION_SOURCE",
    "PYTHON_ONTOLOGY_DTO_RENDERER_PROFILE",
    "PYTHON_ORM_MODELS_MATERIALIZATION_SOURCE",
    "PYTHON_ORM_MODELS_RENDERER_PROFILE",
    "PYTHON_STRUCTURAL_GENERATED_DELTA_RENDERER_NAME",
    "PYTHON_STRUCTURAL_SOURCE_ARTIFACT_PAYLOAD_KEY",
    "PythonStructuralGeneratedDeltaRenderer",
    "PythonStructuralSourceArtifactPayload",
    "build_python_structural_source_artifact_payload",
]
