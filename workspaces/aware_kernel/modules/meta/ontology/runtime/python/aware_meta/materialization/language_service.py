from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Iterator, Literal, TypeAlias, cast
from uuid import UUID

from aware_code.language.quality import (
    CodeLanguageQualityGateRunRequest,
    CodeLanguageQualityGateRunResult,
    run_code_language_quality_gate,
)
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.language.plugin import CodeLanguageMaterializationOutputDescriptor
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.package_strategy import ObjectConfigGraphPackageSpec
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererPolicy,
)
from aware_meta.graph.config.runtime_derivation.clone import (
    clone_runtime_graph_for_language_transformer_handoff,
)
from aware_meta.graph.config.runtime_derivation.schemas import (
    RuntimeObjectConfigGraphDerivationRequest,
    RuntimeObjectConfigGraphDerivationResult,
)
from aware_meta.graph.config.runtime_derivation.service import (
    RuntimeObjectConfigGraphDerivationService,
    build_namespace_by_code_id_from_graph,
    derive_runtime_object_config_graphs,
)
from aware_meta.graph.config.runtime_derivation.timer import RuntimeDerivationStep
from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer
from aware_meta.graph.projection.portal_index import (
    ObjectProjectionGraphPortalClosureContext,
    build_portal_closure_context,
)
from aware_meta.language_plugin import (
    MetaLanguageDeclaredOutputProducedFile,
    MetaLanguageDeclaredOutputProducerRequest,
    MetaLanguagePlugin,
    MetaLanguageMaterializationDestination,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization.package_runner import (
    LanguageMaterializationPackageBuildRequest,
    build_language_materialization_packages,
)
from aware_meta.materialization.post_step_executor import (
    LanguageMaterializationPostStepExecutionRequest,
    execute_language_materialization_post_steps,
)
from aware_meta.materialization.post_step_target_result import (
    LanguageMaterializationPostStepExecutionResult,
    language_materialization_post_step_execution_path_hints,
)
from aware_meta.semantic_contract import (
    META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
    META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
    META_OBJECT_CONFIG_GRAPH_OWNER,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)


_META_PROVIDER_KEY = "aware_meta"
_META_LANGUAGE_MATERIALIZATION_MANIFEST_SNAPSHOT_KEY = (
    "language_materialization_manifest_snapshot"
)
_META_LANGUAGE_MATERIALIZATION_MANIFEST_SNAPSHOT_SCHEMA = (
    "aware.meta.language_materialization.manifest_snapshot.v1"
)
_META_LANGUAGE_MATERIALIZATION_MANIFEST_REQUIRED_FOR = (
    "workspace_revision",
    "runtime_index",
    "environment_config",
    "dependency_import_resolution",
)
_META_LANGUAGE_MATERIALIZATION_RUNTIME_CONTRACT_VERSION = (
    "aware.meta.language_materialization.v1"
)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationGeneratedFile:
    path: Path
    output_kind: str
    producer_step: str
    sha256: str
    size_bytes: int
    source_graph_ref: str | None = None
    renderer_name: str | None = None


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPackageOutput:
    package_name: str
    output_root: Path
    import_root: str | None = None
    generated_file_refs: tuple[Path, ...] = ()
    deleted_file_refs: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationArtifactOutput:
    provider_key: str
    semantic_owner: str
    producer_key: str
    output_key: str
    artifact_family: str
    artifact_role: str
    output_kind: str
    package_output_key: str | None = None
    generated_file_refs: tuple[Path, ...] = ()
    package_output_refs: tuple[str, ...] = ()
    required_for: tuple[str, ...] = ()
    status: str = "materialized"
    provider_payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPluginDeclaredOutput:
    language: CodeLanguage
    output_key: str
    output_kind: str
    artifact_role: str
    producer_step: str
    path_templates: tuple[str, ...] = ()
    resolved_paths: tuple[Path, ...] = ()
    generated_file_refs: tuple[Path, ...] = ()
    required_for: tuple[str, ...] = ()
    renderer_profiles: tuple[str, ...] = ()
    renderer_kinds: tuple[str, ...] = ()
    materialization_sources: tuple[str, ...] = ()
    required: bool = False
    status: str = "declared"
    provider_payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationOwnershipReceipt:
    """Provider-owned artifact ownership receipt for later Workspace projection."""

    producer_provider_key: str
    semantic_owner: str
    producer_key: str
    output_key: str
    artifact_key: str
    artifact_family: str
    artifact_role: str
    output_kind: str
    target_language_plugin_id: CodeLanguage
    status: str = "available"
    producer_kind: str | None = "semantic_materializer"
    producer_step: str | None = None
    package_name: str | None = None
    package_output_key: str | None = None
    required_for: tuple[str, ...] = ()
    path: Path | None = None
    digest: str | None = None
    digest_algorithm: str = "sha256"
    size_bytes: int | None = None
    source_code_package_id: UUID | None = None
    object_config_graph_package_id: UUID | None = None
    object_config_graph_commit_id: UUID | None = None
    source_object_instance_graph_commit_id: UUID | None = None
    input_object_instance_graph_commit_id: UUID | None = None
    source_graph_ref: str | None = None
    runtime_graph_ref: str | None = None
    language_graph_ref: str | None = None
    runtime_contract_version: str = (
        _META_LANGUAGE_MATERIALIZATION_RUNTIME_CONTRACT_VERSION
    )
    provider_payload: Mapping[str, object] = field(default_factory=dict)

    def as_payload(self) -> dict[str, object]:
        return {
            "producer_provider_key": self.producer_provider_key,
            "semantic_owner": self.semantic_owner,
            "producer_key": self.producer_key,
            "producer_kind": self.producer_kind,
            "output_key": self.output_key,
            "artifact_key": self.artifact_key,
            "artifact_family": self.artifact_family,
            "artifact_role": self.artifact_role,
            "output_kind": self.output_kind,
            "target_language_plugin_id": self.target_language_plugin_id.value,
            "status": self.status,
            "producer_step": self.producer_step,
            "package_name": self.package_name,
            "package_output_key": self.package_output_key,
            "required_for": sorted(self.required_for),
            "path": self.path.as_posix() if self.path is not None else None,
            "digest": self.digest,
            "digest_algorithm": self.digest_algorithm,
            "size_bytes": self.size_bytes,
            "source_code_package_id": _uuid_value(self.source_code_package_id),
            "object_config_graph_package_id": _uuid_value(
                self.object_config_graph_package_id
            ),
            "object_config_graph_commit_id": _uuid_value(
                self.object_config_graph_commit_id
            ),
            "source_object_instance_graph_commit_id": _uuid_value(
                self.source_object_instance_graph_commit_id
            ),
            "input_object_instance_graph_commit_id": _uuid_value(
                self.input_object_instance_graph_commit_id
            ),
            "source_graph_ref": self.source_graph_ref,
            "runtime_graph_ref": self.runtime_graph_ref,
            "language_graph_ref": self.language_graph_ref,
            "runtime_contract_version": self.runtime_contract_version,
            "provider_payload": _canonical_value(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class LanguageMaterializationManifestSnapshot:
    snapshot_key: str
    producer_key: str
    sha256: str
    payload: Mapping[str, object]
    source_graph_ref: str | None = None
    runtime_graph_ref: str | None = None
    language_graph_ref: str | None = None
    dependency_signature: str | None = None
    required_for: tuple[str, ...] = ()
    status: str = "materialized"


@dataclass(frozen=True, slots=True)
class LanguageMaterializationStep:
    name: str
    duration_s: float
    status: str = "succeeded"
    details: Mapping[str, object] = field(default_factory=dict)


GraphMaterializationStage: TypeAlias = Literal[
    "source_graph",
    "canonical_runtime_graph",
    "language_graph",
]

GraphMaterializationProfile: TypeAlias = Literal[
    "runtime_orm",
    "public_dto",
    "runtime_passthrough",
]
_PortalClosureContextFactory: TypeAlias = Callable[
    [],
    ObjectProjectionGraphPortalClosureContext | None,
]
LanguageMaterializationProgressCallback: TypeAlias = Callable[
    [Mapping[str, object]],
    object,
]


@dataclass(frozen=True, slots=True)
class GraphMaterializationTransformRequest:
    source_graph: ObjectConfigGraph
    target_language_plugin_id: CodeLanguage = CodeLanguage.aware
    source_stage: GraphMaterializationStage = "source_graph"
    target_stage: GraphMaterializationStage = "language_graph"
    graph_profile: GraphMaterializationProfile = "runtime_orm"
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = ()
    include_projection_graphs: bool = True


@dataclass(frozen=True, slots=True)
class GraphMaterializationTransformResult:
    source_graph: ObjectConfigGraph
    runtime_graph: ObjectConfigGraph
    language_graph: ObjectConfigGraph | None = None
    runtime_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    language_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    source_stage: GraphMaterializationStage = "source_graph"
    target_stage: GraphMaterializationStage = "language_graph"
    target_language_plugin_id: CodeLanguage = CodeLanguage.aware
    source_graph_ref: str | None = None
    runtime_graph_ref: str | None = None
    language_graph_ref: str | None = None
    tool_steps: tuple[LanguageMaterializationStep, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)

    def require_language_graph(self) -> ObjectConfigGraph:
        if self.language_graph is None:
            raise ValueError(
                "Graph materialization transform did not produce a language graph."
            )
        return self.language_graph


@dataclass(frozen=True, slots=True)
class GraphMaterializationRuntimeBatchRequest:
    source_graphs: tuple[ObjectConfigGraph, ...]
    target_object_config_graph_ids: frozenset[UUID] | None = None
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = ()
    include_projection_graphs: bool = True


@dataclass(frozen=True, slots=True)
class GraphMaterializationRuntimeBatchResult:
    runtime_graphs: tuple[ObjectConfigGraph, ...]
    target_runtime_graphs: tuple[ObjectConfigGraph, ...]
    source_graph_refs: Mapping[UUID, str]
    runtime_graph_refs: Mapping[UUID, str]


class GraphMaterializationTransformService:
    """Meta-owned graph-stage orchestration over language plugin transforms."""

    def transform(
        self,
        request: GraphMaterializationTransformRequest,
    ) -> GraphMaterializationTransformResult:
        _validate_graph_transform_request(request)
        if request.graph_profile == "public_dto":
            return _transform_public_dto_graph(request)

        steps: list[LanguageMaterializationStep] = []

        with _record_step(steps, "derive_runtime_graph"):
            runtime_result = RuntimeObjectConfigGraphDerivationService().derive(
                RuntimeObjectConfigGraphDerivationRequest(
                    source_graph=request.source_graph,
                    external_runtime_graphs=request.external_runtime_graphs,
                    include_projection_graphs=request.include_projection_graphs,
                    source_is_runtime=(
                        request.source_stage == "canonical_runtime_graph"
                    ),
                )
            )

        language_graph: ObjectConfigGraph | None = None
        language_external_graphs: tuple[ObjectConfigGraph, ...] = ()
        generated_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
        closure_lowering_metrics: Mapping[str, object] = {}
        if request.target_stage == "language_graph":
            runtime_to_language_cache = RuntimeToLanguageLoweringCache()
            with _record_step(steps, "runtime_to_language"):
                closure_result = RuntimeToLanguageClosureLoweringService().lower(
                    RuntimeToLanguageClosureLoweringRequest(
                        runtime_graph=runtime_result.runtime_graph,
                        target_language_plugin_id=request.target_language_plugin_id,
                        runtime_external_graphs=runtime_result.runtime_external_graphs,
                        runtime_to_language_cache=runtime_to_language_cache,
                        steps=steps,
                        step_prefix="runtime_to_language",
                    )
                )
                language_graph = closure_result.language_graph
                generated_manifest = closure_result.generated_ocg_node_manifest
                language_external_graphs = closure_result.language_external_graphs
                closure_lowering_metrics = closure_result.metrics

        all_steps = tuple(
            LanguageMaterializationStep(
                name=f"runtime_derivation:{step.name}",
                duration_s=step.duration_s,
            )
            for step in runtime_result.timings
        ) + tuple(steps)
        language_graph_ref = (
            _graph_ref(language_graph) if language_graph is not None else None
        )
        return GraphMaterializationTransformResult(
            source_graph=request.source_graph,
            runtime_graph=runtime_result.runtime_graph,
            language_graph=language_graph,
            runtime_external_graphs=runtime_result.runtime_external_graphs,
            language_external_graphs=language_external_graphs,
            generated_ocg_node_manifest=generated_manifest,
            source_stage=request.source_stage,
            target_stage=request.target_stage,
            target_language_plugin_id=request.target_language_plugin_id,
            source_graph_ref=_graph_ref(request.source_graph),
            runtime_graph_ref=_graph_ref(runtime_result.runtime_graph),
            language_graph_ref=language_graph_ref,
            tool_steps=all_steps,
            metrics={
                **runtime_result.metrics,
                "source_stage": request.source_stage,
                "target_stage": request.target_stage,
                "graph_profile": request.graph_profile,
                "target_language_plugin_id": request.target_language_plugin_id.value,
                "runtime_external_graph_count": len(
                    runtime_result.runtime_external_graphs
                ),
                "language_external_graph_count": len(language_external_graphs),
                **dict(closure_lowering_metrics),
            },
        )

    def transform_source_graphs_to_runtime(
        self,
        request: GraphMaterializationRuntimeBatchRequest,
    ) -> GraphMaterializationRuntimeBatchResult:
        source_graphs = tuple(request.source_graphs)
        runtime_graphs = derive_runtime_object_config_graphs(
            source_graphs,
            external_runtime_graphs=tuple(request.external_runtime_graphs),
            include_projection_graphs=request.include_projection_graphs,
        )
        if len(runtime_graphs) != len(source_graphs):
            raise ValueError(
                "Graph materialization runtime batch returned a graph count "
                "that does not match the source graph count."
            )
        targets = request.target_object_config_graph_ids
        target_runtime_graphs = tuple(
            runtime_graph
            for source_graph, runtime_graph in zip(source_graphs, runtime_graphs)
            if targets is None or source_graph.id in targets
        )
        return GraphMaterializationRuntimeBatchResult(
            runtime_graphs=runtime_graphs,
            target_runtime_graphs=target_runtime_graphs,
            source_graph_refs={
                source_graph.id: _graph_ref(source_graph)
                for source_graph in source_graphs
            },
            runtime_graph_refs={
                source_graph.id: _graph_ref(runtime_graph)
                for source_graph, runtime_graph in zip(
                    source_graphs,
                    runtime_graphs,
                )
            },
        )


def _validate_graph_transform_request(
    request: GraphMaterializationTransformRequest,
) -> None:
    if request.graph_profile == "public_dto":
        if (
            request.source_stage != "source_graph"
            or request.target_stage != "language_graph"
        ):
            raise ValueError(
                "public_dto graph materialization requires source_graph -> "
                "language_graph; DTO/public contract materialization must not "
                "derive canonical runtime ORM graph shape."
            )
        _ensure_target_language_plugin(request.target_language_plugin_id)
        return
    if request.source_stage == "language_graph":
        raise ValueError(
            "GraphMaterializationTransformService requires source or canonical "
            "runtime graph input; prepared language graph rendering must pass "
            "an explicit language graph to the render boundary."
        )
    if request.target_stage == "source_graph":
        raise ValueError(
            "GraphMaterializationTransformService cannot target source_graph; "
            "request canonical_runtime_graph or language_graph."
        )
    if request.source_stage == "canonical_runtime_graph":
        if request.source_graph.language != CodeLanguage.aware:
            raise ValueError(
                "canonical_runtime_graph source_stage requires a "
                "CodeLanguage.aware runtime ObjectConfigGraph."
            )
    if request.target_stage == "language_graph":
        _ensure_target_language_plugin(request.target_language_plugin_id)


def _transform_public_dto_graph(
    request: GraphMaterializationTransformRequest,
) -> GraphMaterializationTransformResult:
    steps: list[LanguageMaterializationStep] = []
    with _record_step(steps, "derive_public_dto_graph"):
        language_graph, public_dto_metrics = _derive_public_dto_language_graph(
            request.source_graph
        )
    graph_ref = _graph_ref(request.source_graph)
    runtime_external_graphs = tuple(request.external_runtime_graphs)
    language_external_graphs = tuple(
        _derive_public_dto_language_graph(external_graph)[0]
        for external_graph in runtime_external_graphs
    )
    return GraphMaterializationTransformResult(
        source_graph=request.source_graph,
        runtime_graph=request.source_graph,
        language_graph=language_graph,
        runtime_external_graphs=runtime_external_graphs,
        language_external_graphs=language_external_graphs,
        generated_ocg_node_manifest=None,
        source_stage=request.source_stage,
        target_stage=request.target_stage,
        target_language_plugin_id=request.target_language_plugin_id,
        source_graph_ref=graph_ref,
        runtime_graph_ref=None,
        language_graph_ref=graph_ref,
        tool_steps=tuple(steps),
        metrics={
            **public_dto_metrics,
            "source_stage": request.source_stage,
            "target_stage": request.target_stage,
            "graph_profile": request.graph_profile,
            "target_language_plugin_id": request.target_language_plugin_id.value,
            "runtime_external_graph_count": len(runtime_external_graphs),
            "language_external_graph_count": len(language_external_graphs),
            "canonical_runtime_graph_derived": False,
        },
    )


def _derive_public_dto_language_graph(
    source_graph: ObjectConfigGraph,
) -> tuple[ObjectConfigGraph, Mapping[str, object]]:
    """Derive DTO-ready graph shape without ORM runtime materialization."""

    language_graph = source_graph.model_copy(deep=True)
    relationship_attrs_seen = 0
    lazy_relationship_attrs_lowered = 0
    eager_relationship_attrs_preserved = 0

    attrs_by_id = _attribute_configs_by_id(language_graph)
    for relationship in _iter_graph_relationships(language_graph):
        strategy = (
            relationship.forward_loading_strategy
            or ClassConfigRelationshipSideLoadingStrategy.lazy
        )
        for rel_attr in relationship.class_config_relationship_attributes:
            if (
                rel_attr.direction != ClassConfigRelationshipDirection.forward
                or rel_attr.role != ClassConfigRelationshipAttributeRole.reference
            ):
                continue
            attr = attrs_by_id.get(rel_attr.attribute_config_id)
            if attr is None or not _is_single_object_reference_attribute(attr):
                continue
            relationship_attrs_seen += 1
            if strategy == ClassConfigRelationshipSideLoadingStrategy.lazy:
                attr.is_required = False
                attr.default_value = "null"
                attr.exclude_serialization = False
                lazy_relationship_attrs_lowered += 1
            else:
                eager_relationship_attrs_preserved += 1

    return language_graph, {
        "public_dto_relationship_attrs_seen": relationship_attrs_seen,
        "public_dto_lazy_relationship_attrs_lowered": lazy_relationship_attrs_lowered,
        "public_dto_eager_relationship_attrs_preserved": eager_relationship_attrs_preserved,
    }


def _attribute_configs_by_id(
    graph: ObjectConfigGraph,
) -> dict[UUID, AttributeConfig]:
    attrs: dict[UUID, AttributeConfig] = {}
    for node in graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None:
            continue
        for link in class_config.class_config_attribute_configs:
            attrs[link.attribute_config.id] = link.attribute_config
    return attrs


def _iter_graph_relationships(
    graph: ObjectConfigGraph,
) -> Iterator[ClassConfigRelationship]:
    seen: set[UUID] = set()
    for node in graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is not None:
            for relationship in class_config.class_config_relationships:
                if relationship.id not in seen:
                    seen.add(relationship.id)
                    yield relationship
        relationship = node.class_config_relationship
        if relationship is not None and relationship.id not in seen:
            seen.add(relationship.id)
            yield relationship
    for graph_relationship in graph.object_config_graph_relationships:
        for relationship in graph_relationship.class_config_relationships:
            if relationship.id not in seen:
                seen.add(relationship.id)
                yield relationship


def _is_single_object_reference_attribute(attribute: AttributeConfig) -> bool:
    descriptor = attribute.type_descriptor
    return (
        descriptor.kind == AttributeTypeDescriptorKind.class_
        and descriptor.collection_kind == AttributeCollectionType.single
    )


def _graph_ref(graph: ObjectConfigGraph) -> str:
    return graph.hash or str(graph.id)


@dataclass(frozen=True, slots=True)
class _RuntimeDerivationCacheKey:
    target_language: CodeLanguage
    source_graph_id: str
    source_graph_ref: str
    source_graph_fqn_prefix: str
    external_graph_refs: tuple[tuple[str, str, str], ...]
    include_projection_graphs: bool
    derive_external_projection_graphs: bool
    source_is_runtime: bool
    reuse_external_runtime_graphs: bool

    @property
    def digest(self) -> str:
        payload = (
            self.target_language.value,
            self.source_graph_id,
            self.source_graph_ref,
            self.source_graph_fqn_prefix,
            self.external_graph_refs,
            self.include_projection_graphs,
            self.derive_external_projection_graphs,
            self.source_is_runtime,
            self.reuse_external_runtime_graphs,
        )
        return sha256(repr(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class _RuntimeDerivationCacheEntry:
    runtime_graph: ObjectConfigGraph
    runtime_external_graphs: tuple[ObjectConfigGraph, ...]
    source_language: CodeLanguage
    runtime_language: CodeLanguage
    source_graph_hash: str | None
    runtime_graph_hash: str | None
    timings: tuple[RuntimeDerivationStep, ...]
    metrics: Mapping[str, object]

    def copy_result(
        self,
        *,
        source_graph: ObjectConfigGraph,
        deep_copy: bool = True,
        include_timings: bool = True,
    ) -> RuntimeObjectConfigGraphDerivationResult:
        return RuntimeObjectConfigGraphDerivationResult(
            source_graph=source_graph,
            runtime_graph=self.runtime_graph.model_copy(deep=deep_copy),
            runtime_external_graphs=tuple(
                graph.model_copy(deep=deep_copy)
                for graph in self.runtime_external_graphs
            ),
            source_language=self.source_language,
            runtime_language=self.runtime_language,
            source_graph_hash=self.source_graph_hash,
            runtime_graph_hash=self.runtime_graph_hash,
            timings=self.timings if include_timings else (),
            metrics=dict(self.metrics),
        )


@dataclass(slots=True)
class RuntimeObjectConfigGraphDerivationCache:
    """Request-scoped cache for source/runtime graph derivation.

    Provider-delta output materialization can render several target packages from
    the same source graph closure. This cache avoids repeating the runtime
    derivation step inside one request while returning fresh graph copies to each
    target renderer.
    """

    _entries: dict[_RuntimeDerivationCacheKey, _RuntimeDerivationCacheEntry] = field(
        default_factory=dict,
    )
    deep_copy_hits: bool = True
    deep_copy_stores: bool = True
    replay_hit_timings: bool = False
    hit_count: int = 0
    miss_count: int = 0
    store_count: int = 0

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def get(
        self,
        key: _RuntimeDerivationCacheKey,
        *,
        source_graph: ObjectConfigGraph,
    ) -> RuntimeObjectConfigGraphDerivationResult | None:
        entry = self._entries.get(key)
        if entry is None:
            self.miss_count += 1
            return None
        self.hit_count += 1
        return entry.copy_result(
            source_graph=source_graph,
            deep_copy=self.deep_copy_hits,
            include_timings=self.replay_hit_timings,
        )

    def store(
        self,
        key: _RuntimeDerivationCacheKey,
        *,
        result: RuntimeObjectConfigGraphDerivationResult,
    ) -> None:
        self._entries[key] = _RuntimeDerivationCacheEntry(
            runtime_graph=result.runtime_graph.model_copy(deep=self.deep_copy_stores),
            runtime_external_graphs=tuple(
                graph.model_copy(deep=self.deep_copy_stores)
                for graph in result.runtime_external_graphs
            ),
            source_language=result.source_language,
            runtime_language=result.runtime_language,
            source_graph_hash=result.source_graph_hash,
            runtime_graph_hash=result.runtime_graph_hash,
            timings=result.timings,
            metrics=dict(result.metrics),
        )
        self.store_count += 1

    def stats_payload(self) -> dict[str, int]:
        return {
            "entry_count": self.entry_count,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "store_count": self.store_count,
            "deep_copy_hits": self.deep_copy_hits,
        }


@dataclass(frozen=True, slots=True)
class _RuntimeToLanguageLoweringCacheKey:
    target_language_plugin_id: CodeLanguage
    renderer_profile: str | None
    runtime_graph_id: str
    runtime_graph_ref: str
    runtime_graph_fqn_prefix: str
    external_graph_refs: tuple[tuple[str, str, str], ...] = ()

    @property
    def digest(self) -> str:
        payload = (
            self.target_language_plugin_id.value,
            self.renderer_profile,
            self.runtime_graph_id,
            self.runtime_graph_ref,
            self.runtime_graph_fqn_prefix,
            self.external_graph_refs,
        )
        return sha256(repr(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class _RuntimeToLanguagePortalClosureContextCacheKey:
    runtime_graph_id: str
    runtime_graph_ref: str
    runtime_graph_fqn_prefix: str
    external_graph_refs: tuple[tuple[str, str, str], ...] = ()

    @property
    def digest(self) -> str:
        payload = (
            self.runtime_graph_id,
            self.runtime_graph_ref,
            self.runtime_graph_fqn_prefix,
            self.external_graph_refs,
        )
        return sha256(repr(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class _RuntimeToLanguageLoweringCacheEntry:
    language_graph: ObjectConfigGraph
    generated_manifest: GeneratedObjectConfigGraphNodeManifest | None = None

    def copy_result(
        self,
        *,
        deep_copy: bool = True,
    ) -> tuple[ObjectConfigGraph, GeneratedObjectConfigGraphNodeManifest | None]:
        manifest = (
            self.generated_manifest.model_copy(deep=deep_copy)
            if self.generated_manifest is not None
            else None
        )
        return self.language_graph.model_copy(deep=deep_copy), manifest


@dataclass(slots=True)
class RuntimeToLanguageLoweringCache:
    """Per-materialization cache for runtime graph -> language graph lowering.

    The cache is intentionally request-scoped. It avoids recomputing identical
    dependency-closure transforms across materialization targets without leaking
    graph/plugin state between workspace operations.
    """

    store_language_results: bool = True
    deep_copy_hits: bool = True
    deep_copy_stores: bool = True
    _entries: dict[
        _RuntimeToLanguageLoweringCacheKey,
        _RuntimeToLanguageLoweringCacheEntry,
    ] = field(default_factory=dict)
    _portal_closure_context_entries: dict[
        _RuntimeToLanguagePortalClosureContextCacheKey,
        ObjectProjectionGraphPortalClosureContext,
    ] = field(default_factory=dict)
    hit_count: int = 0
    miss_count: int = 0
    store_count: int = 0
    store_skipped_count: int = 0
    portal_closure_context_hit_count: int = 0
    portal_closure_context_miss_count: int = 0
    portal_closure_context_store_count: int = 0

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def portal_closure_context_entry_count(self) -> int:
        return len(self._portal_closure_context_entries)

    def get(
        self,
        key: _RuntimeToLanguageLoweringCacheKey,
    ) -> tuple[ObjectConfigGraph, GeneratedObjectConfigGraphNodeManifest | None] | None:
        entry = self._entries.get(key)
        if entry is None:
            self.miss_count += 1
            return None
        self.hit_count += 1
        return entry.copy_result(deep_copy=self.deep_copy_hits)

    def store(
        self,
        key: _RuntimeToLanguageLoweringCacheKey,
        *,
        language_graph: ObjectConfigGraph,
        generated_manifest: GeneratedObjectConfigGraphNodeManifest | None,
    ) -> None:
        if not self.store_language_results:
            self.store_skipped_count += 1
            return
        self._entries[key] = _RuntimeToLanguageLoweringCacheEntry(
            language_graph=language_graph.model_copy(deep=self.deep_copy_stores),
            generated_manifest=(
                generated_manifest.model_copy(deep=self.deep_copy_stores)
                if generated_manifest is not None
                else None
            ),
        )
        self.store_count += 1

    def get_portal_closure_context(
        self,
        key: _RuntimeToLanguagePortalClosureContextCacheKey,
    ) -> ObjectProjectionGraphPortalClosureContext | None:
        context = self._portal_closure_context_entries.get(key)
        if context is None:
            self.portal_closure_context_miss_count += 1
            return None
        self.portal_closure_context_hit_count += 1
        return context

    def store_portal_closure_context(
        self,
        key: _RuntimeToLanguagePortalClosureContextCacheKey,
        *,
        context: ObjectProjectionGraphPortalClosureContext,
    ) -> None:
        self._portal_closure_context_entries[key] = context
        self.portal_closure_context_store_count += 1

    def stats_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "entry_count": self.entry_count,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "store_count": self.store_count,
            "deep_copy_hits": self.deep_copy_hits,
        }
        if not self.store_language_results:
            payload["language_graph_store_enabled"] = False
        if self.store_skipped_count:
            payload["store_skipped_count"] = self.store_skipped_count
        if (
            self.portal_closure_context_entry_count
            or self.portal_closure_context_hit_count
            or self.portal_closure_context_miss_count
            or self.portal_closure_context_store_count
        ):
            payload["portal_closure_context"] = {
                "entry_count": self.portal_closure_context_entry_count,
                "hit_count": self.portal_closure_context_hit_count,
                "miss_count": self.portal_closure_context_miss_count,
                "store_count": self.portal_closure_context_store_count,
            }
        return payload


@dataclass(frozen=True, slots=True)
class RuntimeToLanguageClosureLoweringRequest:
    runtime_graph: ObjectConfigGraph
    target_language_plugin_id: CodeLanguage
    renderer_profile: str | None = None
    runtime_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    lower_external_graphs: bool = True
    runtime_to_language_cache: RuntimeToLanguageLoweringCache | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    steps: list[LanguageMaterializationStep] | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    step_prefix: str = "runtime_to_language"


@dataclass(frozen=True, slots=True)
class RuntimeToLanguageClosureLoweringResult:
    language_graph: ObjectConfigGraph
    language_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    metrics: Mapping[str, object] = field(default_factory=dict)


class RuntimeToLanguageClosureLoweringService:
    """Lower one runtime graph closure to a target language using Meta-owned context."""

    def lower(
        self,
        request: RuntimeToLanguageClosureLoweringRequest,
    ) -> RuntimeToLanguageClosureLoweringResult:
        closure_context: ObjectProjectionGraphPortalClosureContext | None = None
        closure_context_checked = False

        def _portal_closure_context_for_transform() -> (
            ObjectProjectionGraphPortalClosureContext | None
        ):
            nonlocal closure_context, closure_context_checked
            if closure_context_checked:
                return closure_context
            closure_context_checked = True
            cache_key = _runtime_to_language_portal_closure_context_cache_key(
                request=request,
            )
            if cache_key is not None and request.runtime_to_language_cache is not None:
                lookup_started_at = perf_counter()
                cached_context = (
                    request.runtime_to_language_cache.get_portal_closure_context(
                        cache_key,
                    )
                )
                cache_status = "hit" if cached_context is not None else "miss"
                _record_substep_duration(
                    request.steps,
                    f"{request.step_prefix}.closure_context_cache_{cache_status}",
                    duration_s=round(perf_counter() - lookup_started_at, 6),
                    parent_step=request.step_prefix,
                    graph_role="all",
                    details={
                        "cache_key": cache_key.digest,
                        "cache_entry_count": (
                            request.runtime_to_language_cache.portal_closure_context_entry_count
                        ),
                    },
                )
                if cached_context is not None:
                    closure_context = cached_context
                    return closure_context
            closure_context = _prepare_runtime_to_language_closure_context(
                request=request,
            )
            if (
                closure_context is not None
                and cache_key is not None
                and request.runtime_to_language_cache is not None
            ):
                store_started_at = perf_counter()
                request.runtime_to_language_cache.store_portal_closure_context(
                    cache_key,
                    context=closure_context,
                )
                _record_substep_duration(
                    request.steps,
                    f"{request.step_prefix}.closure_context_cache_store",
                    duration_s=round(perf_counter() - store_started_at, 6),
                    parent_step=request.step_prefix,
                    graph_role="all",
                    details={
                        "cache_key": cache_key.digest,
                        "cache_entry_count": (
                            request.runtime_to_language_cache.portal_closure_context_entry_count
                        ),
                    },
                )
            return closure_context

        language_graph, generated_manifest = _lower_runtime_graph_to_language(
            request.runtime_graph,
            request.target_language_plugin_id,
            renderer_profile=request.renderer_profile,
            external_runtime_graphs=request.runtime_external_graphs,
            runtime_to_language_cache=request.runtime_to_language_cache,
            portal_closure_context_factory=_portal_closure_context_for_transform,
            steps=request.steps,
            step_prefix=request.step_prefix,
            graph_role="primary",
        )
        language_external_graphs = tuple(
            request.runtime_external_graphs
            if not request.lower_external_graphs
            else (
                _lower_runtime_graph_to_language(
                    external_graph,
                    request.target_language_plugin_id,
                    renderer_profile=request.renderer_profile,
                    external_runtime_graphs=(
                        request.runtime_graph,
                        *(
                            sibling_graph
                            for sibling_graph in request.runtime_external_graphs
                            if sibling_graph.id != external_graph.id
                        ),
                    ),
                    runtime_to_language_cache=request.runtime_to_language_cache,
                    portal_closure_context_factory=_portal_closure_context_for_transform,
                    steps=request.steps,
                    step_prefix=request.step_prefix,
                    graph_role=f"external_{index}",
                )[0]
                for index, external_graph in enumerate(request.runtime_external_graphs)
            )
        )
        if request.runtime_external_graphs and not request.lower_external_graphs:
            _record_substep_duration(
                request.steps,
                f"{request.step_prefix}.external_graph_lowering_skipped",
                duration_s=0.0,
                parent_step=request.step_prefix,
                graph_role="external",
                details={
                    "runtime_external_graph_count": len(
                        request.runtime_external_graphs
                    ),
                    "target_language_plugin_id": (
                        request.target_language_plugin_id.value
                    ),
                },
            )
        return RuntimeToLanguageClosureLoweringResult(
            language_graph=language_graph,
            language_external_graphs=language_external_graphs,
            generated_ocg_node_manifest=generated_manifest,
            metrics={
                "runtime_to_language_closure_context_prepared": closure_context
                is not None,
                "runtime_to_language_closure_context_graph_count": (
                    closure_context.graph_count if closure_context is not None else 0
                ),
                "runtime_to_language_external_graph_lowering_skipped_count": (
                    len(request.runtime_external_graphs)
                    if not request.lower_external_graphs
                    else 0
                ),
            },
        )


@dataclass(frozen=True, slots=True)
class LanguagePluginMaterializationRequest:
    source_graph: ObjectConfigGraph
    target_language_plugin_id: CodeLanguage
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = ()
    package_dependency_graphs: tuple[ObjectConfigGraph, ...] = ()
    lower_language_external_graphs: bool = True
    output_root: Path | None = None
    object_config_graph_package_id: UUID | None = None
    object_config_graph_commit_id: UUID | None = None
    source_code_package_id: UUID | None = None
    package_name: str | None = None
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    materialization_source: str | None = None
    import_root: str | None = None
    stable_ids_import_root: str | None = None
    stable_ids_ownership: str | None = None
    stable_ids_resolution_policy: str | None = None
    function_impl_ownership: str | None = None
    function_impl_parity_policy: str | None = None
    profile_inputs: Mapping[str, object] = field(default_factory=dict)
    import_overrides: Mapping[str, str] = field(default_factory=dict)
    declared_output_destinations: tuple[
        MetaLanguageMaterializationDestination, ...
    ] = ()
    include_projection_graphs: bool = True
    derive_external_projection_graphs: bool = True
    source_is_runtime: bool = False
    reuse_external_runtime_graphs: bool = False
    emit_files: bool = False
    overwrite: bool = True
    quality_gate_ids: tuple[str, ...] = ()
    quality_gate_timeout_s: float | None = None
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] = field(
        default_factory=dict
    )
    post_step_executable_overrides_by_tool_id: Mapping[
        str,
        Mapping[str, str],
    ] = field(default_factory=dict)
    runtime_to_language_cache: RuntimeToLanguageLoweringCache | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    runtime_derivation_cache: RuntimeObjectConfigGraphDerivationCache | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    progress_callback: LanguageMaterializationProgressCallback | None = field(
        default=None,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, slots=True)
class LanguagePluginMaterializationResult:
    target_language_plugin_id: CodeLanguage
    source_graph: ObjectConfigGraph
    runtime_graph: ObjectConfigGraph
    language_graph: ObjectConfigGraph
    language_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    object_config_graph_package_id: UUID | None = None
    object_config_graph_id: UUID | None = None
    object_config_graph_commit_id: UUID | None = None
    source_code_package_id: UUID | None = None
    package_name: str | None = None
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    materialization_source: str | None = None
    import_root: str | None = None
    output_root: Path | None = None
    source_graph_hash: str | None = None
    runtime_graph_hash: str | None = None
    language_graph_hash: str | None = None
    dependency_signature: str | None = None
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...] = ()
    package_outputs: tuple[LanguageMaterializationPackageOutput, ...] = ()
    artifact_outputs: tuple[LanguageMaterializationArtifactOutput, ...] = ()
    plugin_declared_outputs: tuple[
        LanguageMaterializationPluginDeclaredOutput, ...
    ] = ()
    ownership_receipts: tuple[LanguageMaterializationOwnershipReceipt, ...] = ()
    manifest_snapshots: tuple[LanguageMaterializationManifestSnapshot, ...] = ()
    post_step_receipts: tuple[Mapping[str, object], ...] = ()
    tool_steps: tuple[LanguageMaterializationStep, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "succeeded"
    metrics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguagePluginDeclaredOutputProductionRequest:
    target_language_plugin_id: CodeLanguage
    output_root: Path
    source_graph: ObjectConfigGraph
    runtime_graph: ObjectConfigGraph
    language_graph: ObjectConfigGraph
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    language_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    generated_file_paths: tuple[Path, ...] = ()
    package_name: str | None = None
    import_root: str | None = None
    package_dependency_import_roots: tuple[str, ...] = ()
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    materialization_source: str | None = None
    entity_file_paths: Mapping[str, Path] = field(default_factory=dict)
    profile_inputs: Mapping[str, object] = field(default_factory=dict)
    import_overrides: Mapping[str, str] = field(default_factory=dict)
    destinations: tuple[MetaLanguageMaterializationDestination, ...] = ()
    object_config_graph_package_id: UUID | None = None
    object_config_graph_commit_id: UUID | None = None
    source_code_package_id: UUID | None = None
    source_object_instance_graph_commit_id: UUID | None = None
    input_object_instance_graph_commit_id: UUID | None = None
    source_graph_ref: str | None = None
    runtime_graph_ref: str | None = None
    language_graph_ref: str | None = None


@dataclass(frozen=True, slots=True)
class LanguagePluginDeclaredOutputProductionResult:
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...] = ()
    produced_files: tuple[MetaLanguageDeclaredOutputProducedFile, ...] = ()
    ownership_receipts: tuple[LanguageMaterializationOwnershipReceipt, ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationRenderRequest:
    """Prepared language-render request owned by Meta.

    Callers may still resolve graphs/package context, but renderer
    execution and language-plugin dispatch belong here.
    """

    target_language_plugin_id: CodeLanguage
    language_graph: ObjectConfigGraph
    output_root: Path
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    source_graph: ObjectConfigGraph | None = None
    language_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    profile_inputs: Mapping[str, object] = field(default_factory=dict)
    import_overrides: Mapping[str, str] = field(default_factory=dict)
    renderer_policies: Mapping[str, Mapping[str, object | None]] = field(
        default_factory=dict
    )
    fail_on_renderer_warnings: tuple[str, ...] = ()
    overwrite: bool = True
    candidate_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationRenderResult:
    written_files: tuple[Path, ...] = ()
    changed_files: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
    renderer_names: tuple[str, ...] = ()
    renderer_file_counts: Mapping[str, int] = field(default_factory=dict)
    renderer_warning_counts: Mapping[str, int] = field(default_factory=dict)
    renderer_warnings: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    renderer_phase_timings: Mapping[str, Mapping[str, float]] = field(
        default_factory=dict
    )


class LanguagePluginMaterializationService:
    def materialize(
        self,
        request: LanguagePluginMaterializationRequest,
    ) -> LanguagePluginMaterializationResult:
        _ensure_target_language_plugin(request.target_language_plugin_id)
        steps: list[LanguageMaterializationStep] = []
        warnings: list[str] = []

        with _record_language_materialization_subphase(
            request,
            "derive_runtime_graph",
        ):
            with _record_step(steps, "derive_runtime_graph"):
                runtime_result = _derive_runtime_graph_for_language_materialization(
                    request=request,
                    steps=steps,
                )

        runtime_to_language_cache = (
            request.runtime_to_language_cache or RuntimeToLanguageLoweringCache()
        )
        closure_lowering_metrics: Mapping[str, object] = {}
        with _record_language_materialization_subphase(
            request,
            "runtime_to_language",
        ):
            with _record_step(steps, "runtime_to_language"):
                closure_result = RuntimeToLanguageClosureLoweringService().lower(
                    RuntimeToLanguageClosureLoweringRequest(
                        runtime_graph=runtime_result.runtime_graph,
                        target_language_plugin_id=request.target_language_plugin_id,
                        renderer_profile=request.renderer_profile,
                        runtime_external_graphs=runtime_result.runtime_external_graphs,
                        lower_external_graphs=request.lower_language_external_graphs,
                        runtime_to_language_cache=runtime_to_language_cache,
                        steps=steps,
                        step_prefix="runtime_to_language",
                    )
                )
                language_graph = closure_result.language_graph
                generated_manifest = closure_result.generated_ocg_node_manifest
                language_external_graphs = closure_result.language_external_graphs
                closure_lowering_metrics = closure_result.metrics
                if request.emit_files:
                    with _record_language_materialization_subphase(
                        request,
                        "runtime_to_language.import_overrides",
                    ):
                        with _record_substep(
                            steps,
                            "runtime_to_language.import_overrides",
                            parent_step="runtime_to_language",
                            graph_role="all",
                        ):
                            request = _request_with_language_external_import_overrides(
                                request=request,
                                language_external_graphs=language_external_graphs,
                            )
                            request = (
                                _request_with_runtime_handler_local_import_overrides(
                                    request=request,
                                    language_graph=language_graph,
                                )
                            )

        generated_files: tuple[LanguageMaterializationGeneratedFile, ...] = ()
        package_build_metrics: Mapping[str, object] = {}
        deleted_package_file_refs: tuple[Path, ...] = ()
        deleted_unpacked_file_refs: tuple[Path, ...] = ()
        post_step_candidate_paths: set[Path] | None = None
        if request.emit_files:
            with _language_render_output_root(request=request) as render_output_root:
                with _record_language_materialization_subphase(request, "render"):
                    with _record_step(steps, "render"):
                        (
                            generated_files,
                            render_warnings,
                            render_changed_paths,
                            render_phase_timings,
                        ) = _render_language_graph(
                            request=request,
                            output_root=render_output_root,
                            runtime_graph=runtime_result.runtime_graph,
                            language_graph=language_graph,
                            language_external_graphs=language_external_graphs,
                            generated_ocg_node_manifest=generated_manifest,
                        )
                        _record_language_materialization_render_phase_timings(
                            request=request,
                            steps=steps,
                            renderer_phase_timings=render_phase_timings,
                        )
                        post_step_candidate_paths = set(render_changed_paths)
                        warnings.extend(render_warnings)

                if _should_build_language_package(request=request):
                    with _record_language_materialization_subphase(
                        request,
                        "package_build",
                    ):
                        with _record_step(steps, "package_build"):
                            (
                                generated_files,
                                package_warnings,
                                package_build_metrics,
                                deleted_package_file_refs,
                                package_changed_file_refs,
                            ) = _build_packaged_language_files(
                                request=request,
                                render_output_root=render_output_root,
                                generated_files=generated_files,
                            )
                            post_step_candidate_paths = set(package_changed_file_refs)
                            warnings.extend(package_warnings)

        quality_gate_steps: tuple[LanguageMaterializationStep, ...] = ()
        if request.quality_gate_ids:
            with _record_language_materialization_subphase(
                request,
                "quality_gates",
            ):
                quality_gate_steps, quality_warnings = _run_quality_gates(
                    request=request,
                    generated_files=generated_files,
                )
                warnings.extend(quality_warnings)

        producer_metrics: Mapping[str, object] = {}
        if request.emit_files:
            with _record_language_materialization_subphase(
                request,
                "produce_plugin_declared_outputs",
            ):
                with _record_step(steps, "produce_plugin_declared_outputs"):
                    produced_files, producer_warnings, producer_metrics, _ = (
                        _produce_plugin_declared_outputs(
                            request=request,
                            runtime_graph=runtime_result.runtime_graph,
                            language_graph=language_graph,
                            generated_ocg_node_manifest=generated_manifest,
                            language_external_graphs=language_external_graphs,
                            generated_files=generated_files,
                        )
                    )
                    generated_files = _sort_generated_files(
                        generated_files + produced_files
                    )
                    if (
                        produced_files
                        and post_step_candidate_paths is not None
                        and request.output_root is not None
                    ):
                        post_step_candidate_paths.update(
                            _absolute_generated_file_path(
                                output_root=request.output_root,
                                generated_file=generated_file,
                            ).resolve()
                            for generated_file in produced_files
                        )
                    warnings.extend(producer_warnings)

        if (
            request.emit_files
            and generated_files
            and request.output_root is not None
            and _should_prune_unpacked_language_files(request=request)
        ):
            with _record_language_materialization_subphase(
                request,
                "stale_prune",
            ):
                with _record_step(steps, "stale_prune"):
                    deleted_unpacked_file_refs = _prune_stale_unpacked_language_files(
                        request=request,
                        generated_files=generated_files,
                    )

        post_step_receipts: tuple[Mapping[str, object], ...] = ()
        post_step_metrics: Mapping[str, object] = {}
        post_step_generated_files = _post_step_generated_files(
            request=request,
            generated_files=generated_files,
            candidate_paths=post_step_candidate_paths,
        )
        if (
            request.emit_files
            and post_step_generated_files
            and request.output_root is not None
        ):
            with _record_language_materialization_subphase(request, "post_steps"):
                with _record_step(steps, "post_steps"):
                    post_step_execution = execute_language_materialization_post_steps(
                        LanguageMaterializationPostStepExecutionRequest(
                            target_language_plugin_id=(
                                request.target_language_plugin_id
                            ),
                            output_root=request.output_root,
                            generated_file_paths=tuple(
                                _absolute_generated_file_path(
                                    output_root=request.output_root,
                                    generated_file=generated_file,
                                )
                                for generated_file in post_step_generated_files
                            ),
                            package_name=request.package_name or request.import_root,
                            materialization_source=request.materialization_source,
                            renderer_profile=request.renderer_profile,
                            renderer_kind=request.renderer_kind,
                            tool_env_by_tool_id=(request.post_step_tool_env_by_tool_id),
                            executable_overrides_by_tool_id=(
                                request.post_step_executable_overrides_by_tool_id
                            ),
                        )
                    )
                    generated_files = _refresh_generated_files_after_post_steps(
                        request=request,
                        generated_files=generated_files,
                        execution_results=post_step_execution.execution_results,
                    )
                    post_step_receipts = post_step_execution.receipts
                    post_step_metrics = {
                        **dict(post_step_execution.metrics),
                        **_post_step_candidate_metrics(
                            generated_files=generated_files,
                            candidate_paths=post_step_candidate_paths,
                            selected_files=post_step_generated_files,
                        ),
                    }
                    warnings.extend(post_step_execution.warnings)
        elif (
            request.emit_files
            and generated_files
            and request.output_root is not None
            and post_step_candidate_paths is not None
        ):
            post_step_metrics = _post_step_candidate_metrics(
                generated_files=generated_files,
                candidate_paths=post_step_candidate_paths,
                selected_files=(),
            )

        with _record_language_materialization_subphase(request, "receipt_assembly"):
            package_outputs = _build_package_outputs(
                request=request,
                generated_files=generated_files,
                deleted_file_refs=(
                    *deleted_package_file_refs,
                    *deleted_unpacked_file_refs,
                ),
            )
            artifact_outputs = _build_declared_artifact_outputs(
                generated_files=generated_files,
                package_outputs=package_outputs,
            )
            plugin_declared_outputs = _build_plugin_declared_outputs(
                request=request,
                generated_files=generated_files,
            )
            ownership_receipts = _build_ownership_receipts(
                request=request,
                generated_files=generated_files,
                package_outputs=package_outputs,
                artifact_outputs=artifact_outputs,
                plugin_declared_outputs=plugin_declared_outputs,
                source_graph_hash=runtime_result.source_graph_hash,
                runtime_graph_hash=runtime_result.runtime_graph_hash,
                language_graph_hash=language_graph.hash,
            )
            status = (
                "failed"
                if any(step.status != "succeeded" for step in quality_gate_steps)
                else "succeeded"
            )
            dependency_signature = _dependency_signature(
                runtime_result.runtime_external_graphs,
                request.package_dependency_graphs,
            )
            manifest_snapshots = _build_manifest_snapshots(
                request=request,
                runtime_graph=runtime_result.runtime_graph,
                language_graph=language_graph,
                runtime_external_graphs=runtime_result.runtime_external_graphs,
                language_external_graphs=language_external_graphs,
                source_graph_hash=runtime_result.source_graph_hash,
                runtime_graph_hash=runtime_result.runtime_graph_hash,
                language_graph_hash=language_graph.hash,
                dependency_signature=dependency_signature,
                generated_files=generated_files,
                package_outputs=package_outputs,
                artifact_outputs=artifact_outputs,
                plugin_declared_outputs=plugin_declared_outputs,
                ownership_receipts=ownership_receipts,
                status=status,
            )

        all_steps = (
            tuple(
                LanguageMaterializationStep(
                    name=f"runtime_derivation:{step.name}",
                    duration_s=step.duration_s,
                )
                for step in runtime_result.timings
            )
            + tuple(steps)
            + quality_gate_steps
        )
        metrics: dict[str, object] = {
            **runtime_result.metrics,
            **{
                f"package_build_{key}": value
                for key, value in package_build_metrics.items()
            },
            "target_language_plugin_id": request.target_language_plugin_id.value,
            "emit_files": request.emit_files,
            "generated_file_count": len(generated_files),
            "stale_prune_deleted_file_count": len(deleted_unpacked_file_refs),
            "package_output_count": len(package_outputs),
            "artifact_output_count": len(artifact_outputs),
            "plugin_declared_output_count": len(plugin_declared_outputs),
            "ownership_receipt_count": len(ownership_receipts),
            "plugin_declared_output_produced_file_count": len(
                [
                    item
                    for item in generated_files
                    if item.producer_step == "plugin_declared_output_producer"
                ]
            ),
            "plugin_declared_output_producer_metrics": dict(producer_metrics),
            "manifest_snapshot_count": len(manifest_snapshots),
            "quality_gate_count": len(quality_gate_steps),
            "post_step_metrics": dict(post_step_metrics),
            "post_step_receipt_count": len(post_step_receipts),
            "runtime_to_language_cache": runtime_to_language_cache.stats_payload(),
            **dict(closure_lowering_metrics),
        }
        if request.runtime_derivation_cache is not None:
            metrics["runtime_derivation_cache"] = (
                request.runtime_derivation_cache.stats_payload()
            )

        return LanguagePluginMaterializationResult(
            target_language_plugin_id=request.target_language_plugin_id,
            source_graph=request.source_graph,
            runtime_graph=runtime_result.runtime_graph,
            language_graph=language_graph,
            language_external_graphs=language_external_graphs,
            generated_ocg_node_manifest=generated_manifest,
            object_config_graph_package_id=request.object_config_graph_package_id,
            object_config_graph_id=language_graph.id,
            object_config_graph_commit_id=request.object_config_graph_commit_id,
            source_code_package_id=request.source_code_package_id,
            package_name=request.package_name,
            renderer_profile=request.renderer_profile,
            renderer_kind=request.renderer_kind,
            materialization_source=request.materialization_source,
            import_root=request.import_root,
            output_root=(
                request.output_root.resolve()
                if request.output_root is not None
                else None
            ),
            source_graph_hash=runtime_result.source_graph_hash,
            runtime_graph_hash=runtime_result.runtime_graph_hash,
            language_graph_hash=language_graph.hash,
            dependency_signature=dependency_signature,
            generated_files=generated_files,
            package_outputs=package_outputs,
            artifact_outputs=artifact_outputs,
            plugin_declared_outputs=plugin_declared_outputs,
            ownership_receipts=ownership_receipts,
            manifest_snapshots=manifest_snapshots,
            post_step_receipts=post_step_receipts,
            tool_steps=all_steps,
            warnings=tuple(warnings),
            status=status,
            metrics=metrics,
        )


def materialize_object_config_graph_via_language_plugin(
    request: LanguagePluginMaterializationRequest,
) -> LanguagePluginMaterializationResult:
    return LanguagePluginMaterializationService().materialize(request)


def _derive_runtime_graph_for_language_materialization(
    *,
    request: LanguagePluginMaterializationRequest,
    steps: list[LanguageMaterializationStep],
) -> RuntimeObjectConfigGraphDerivationResult:
    derivation_progress_callback = _runtime_derivation_subphase_progress_callback(
        request
    )
    derivation_request = RuntimeObjectConfigGraphDerivationRequest(
        source_graph=request.source_graph,
        external_runtime_graphs=request.external_runtime_graphs,
        include_projection_graphs=request.include_projection_graphs,
        derive_external_projection_graphs=request.derive_external_projection_graphs,
        source_is_runtime=request.source_is_runtime,
        reuse_external_runtime_graphs=request.reuse_external_runtime_graphs,
        progress_callback=derivation_progress_callback,
    )
    cache = request.runtime_derivation_cache
    if cache is None:
        with _record_language_materialization_subphase(
            request,
            "derive_runtime_graph.service",
        ):
            return RuntimeObjectConfigGraphDerivationService().derive(
                derivation_request
            )

    with _record_language_materialization_subphase(
        request,
        "derive_runtime_graph.cache_key",
    ):
        cache_key = _runtime_derivation_cache_key(derivation_request)
    with _record_language_materialization_subphase(
        request,
        "derive_runtime_graph.cache_lookup",
        detail_payload={
            "cache_key": cache_key.digest,
            "cache_entry_count": cache.entry_count,
        },
    ):
        lookup_started_at = perf_counter()
        cached_result = cache.get(cache_key, source_graph=request.source_graph)
    cache_status = "hit" if cached_result is not None else "miss"
    _record_substep_duration(
        steps,
        f"derive_runtime_graph.cache_{cache_status}",
        duration_s=round(perf_counter() - lookup_started_at, 6),
        parent_step="derive_runtime_graph",
        graph_role="all",
        details={
            "cache_key": cache_key.digest,
            "cache_entry_count": cache.entry_count,
        },
    )
    if cached_result is not None:
        return cached_result

    with _record_language_materialization_subphase(
        request,
        "derive_runtime_graph.service",
        detail_payload={
            "cache_key": cache_key.digest,
            "cache_entry_count": cache.entry_count,
        },
    ):
        result = RuntimeObjectConfigGraphDerivationService().derive(derivation_request)
    with _record_language_materialization_subphase(
        request,
        "derive_runtime_graph.cache_store",
        detail_payload={
            "cache_key": cache_key.digest,
            "cache_entry_count": cache.entry_count,
        },
    ):
        store_started_at = perf_counter()
        cache.store(cache_key, result=result)
    _record_substep_duration(
        steps,
        "derive_runtime_graph.cache_store",
        duration_s=round(perf_counter() - store_started_at, 6),
        parent_step="derive_runtime_graph",
        graph_role="all",
        details={
            "cache_key": cache_key.digest,
            "cache_entry_count": cache.entry_count,
        },
    )
    return result


def _runtime_derivation_subphase_progress_callback(
    request: LanguagePluginMaterializationRequest,
) -> Callable[[Mapping[str, object]], None] | None:
    if request.progress_callback is None:
        return None

    def callback(payload: Mapping[str, object]) -> None:
        subphase_name = payload.get("subphase_name")
        status = payload.get("status")
        if not isinstance(subphase_name, str) or not isinstance(status, str):
            return
        raw_detail = payload.get("detail_payload")
        detail_payload = (
            cast(Mapping[str, object], raw_detail)
            if isinstance(raw_detail, Mapping)
            else None
        )
        duration_s = payload.get("duration_s")
        error = payload.get("error")
        _emit_language_materialization_subphase_progress(
            request=request,
            subphase_name=subphase_name,
            status=status,
            duration_s=(
                float(duration_s)
                if isinstance(duration_s, (float, int))
                and not isinstance(duration_s, bool)
                else None
            ),
            error=str(error) if error else None,
            detail_payload=detail_payload,
        )

    return callback


def _runtime_derivation_cache_key(
    request: RuntimeObjectConfigGraphDerivationRequest,
) -> _RuntimeDerivationCacheKey:
    return _RuntimeDerivationCacheKey(
        target_language=request.target_language,
        source_graph_id=str(request.source_graph.id),
        source_graph_ref=_graph_ref(request.source_graph),
        source_graph_fqn_prefix=request.source_graph.fqn_prefix,
        external_graph_refs=tuple(
            (
                str(graph.id),
                _graph_ref(graph),
                graph.fqn_prefix,
            )
            for graph in request.external_runtime_graphs
        ),
        include_projection_graphs=request.include_projection_graphs,
        derive_external_projection_graphs=request.derive_external_projection_graphs,
        source_is_runtime=request.source_is_runtime,
        reuse_external_runtime_graphs=(
            request.source_is_runtime and request.reuse_external_runtime_graphs
        ),
    )


def render_language_materialization(
    request: LanguageMaterializationRenderRequest,
) -> LanguageMaterializationRenderResult:
    """Run prepared language renderers through Meta's plugin registry."""

    return _render_prepared_language_graph(request)


def plan_language_plugin_declared_outputs(
    request: LanguagePluginDeclaredOutputProductionRequest,
) -> LanguagePluginDeclaredOutputProductionResult:
    _ensure_target_language_plugin(request.target_language_plugin_id)
    plugin = MetaLanguagePluginRegistry.get(request.target_language_plugin_id)
    producer = plugin.declared_output_producer
    if producer is None:
        return LanguagePluginDeclaredOutputProductionResult()
    descriptors = tuple(
        getattr(plugin.code_plugin, "materialization_artifact_outputs", ())
    )
    if not descriptors:
        return LanguagePluginDeclaredOutputProductionResult()

    result = producer(
        _declared_output_producer_request_from_production_request(request)
    )
    ownership_receipts = _build_produced_file_ownership_receipts(
        request=request,
        produced_files=tuple(result.produced_files),
    )
    return LanguagePluginDeclaredOutputProductionResult(
        produced_files=tuple(result.produced_files),
        ownership_receipts=ownership_receipts,
        warnings=result.warnings,
        metrics=result.metrics,
    )


def produce_language_plugin_declared_outputs(
    request: LanguagePluginDeclaredOutputProductionRequest,
) -> LanguagePluginDeclaredOutputProductionResult:
    planned = plan_language_plugin_declared_outputs(request)
    if not planned.produced_files:
        return planned

    output_root = request.output_root.resolve()
    files = tuple(
        _generated_file_for_produced_declared_output(
            produced_file=produced_file,
            output_root=output_root,
            source_graph_ref=request.language_graph.hash
            or str(request.language_graph.id),
        )
        for produced_file in planned.produced_files
    )
    return LanguagePluginDeclaredOutputProductionResult(
        generated_files=files,
        produced_files=planned.produced_files,
        ownership_receipts=_build_produced_file_ownership_receipts(
            request=request,
            produced_files=planned.produced_files,
            generated_files=files,
        ),
        warnings=planned.warnings,
        metrics=planned.metrics,
    )


def _declared_output_producer_request_from_production_request(
    request: LanguagePluginDeclaredOutputProductionRequest,
) -> MetaLanguageDeclaredOutputProducerRequest:
    plugin = MetaLanguagePluginRegistry.get(request.target_language_plugin_id)
    descriptors = tuple(
        getattr(plugin.code_plugin, "materialization_artifact_outputs", ())
    )
    return MetaLanguageDeclaredOutputProducerRequest(
        output_root=request.output_root.resolve(),
        source_graph=request.source_graph,
        runtime_graph=request.runtime_graph,
        language_graph=request.language_graph,
        generated_ocg_node_manifest=request.generated_ocg_node_manifest,
        destinations=request.destinations,
        language_external_graphs=request.language_external_graphs,
        descriptors=descriptors,
        generated_file_paths=request.generated_file_paths,
        package_name=request.package_name,
        import_root=request.import_root,
        package_dependency_import_roots=request.package_dependency_import_roots,
        renderer_profile=request.renderer_profile,
        renderer_kind=request.renderer_kind,
        materialization_source=request.materialization_source,
        entity_file_paths=request.entity_file_paths,
        profile_inputs=request.profile_inputs,
        import_overrides=request.import_overrides,
    )


def _ensure_target_language_plugin(target_language_plugin_id: CodeLanguage) -> None:
    if MetaLanguagePluginRegistry.has_language(target_language_plugin_id):
        return
    for plugin in AwareModulePluginRegistry.get_builtin_meta_language_plugins():
        MetaLanguagePluginRegistry.register(cast(MetaLanguagePlugin, plugin))
    if not MetaLanguagePluginRegistry.has_language(target_language_plugin_id):
        raise ValueError(
            "No Meta language plugin registered for "
            f"{target_language_plugin_id.value!r}."
        )


def _ensure_code_language_plugin(target_language_plugin_id: CodeLanguage) -> None:
    if CodeLanguagePluginRegistry.has_language(target_language_plugin_id):
        return
    for plugin in AwareModulePluginRegistry.get_builtin_code_language_plugins():
        CodeLanguagePluginRegistry.register(plugin)
    if not CodeLanguagePluginRegistry.has_language(target_language_plugin_id):
        raise ValueError(
            "No Code language plugin registered for "
            f"{target_language_plugin_id.value!r}."
        )


def _prepare_runtime_to_language_closure_context(
    *,
    request: RuntimeToLanguageClosureLoweringRequest,
) -> ObjectProjectionGraphPortalClosureContext | None:
    if request.target_language_plugin_id != CodeLanguage.python:
        return None
    if not (
        request.runtime_graph.object_projection_graphs
        or any(
            graph.object_projection_graphs for graph in request.runtime_external_graphs
        )
    ):
        return None

    closure_context: ObjectProjectionGraphPortalClosureContext | None = None
    with _record_substep(
        request.steps,
        f"{request.step_prefix}.closure_context_prepare",
        parent_step=request.step_prefix,
        graph_role="all",
        details={
            "target_language_plugin_id": request.target_language_plugin_id.value,
            "runtime_external_graph_count": len(request.runtime_external_graphs),
        },
    ):
        closure_context = build_portal_closure_context(
            request.runtime_graph,
            external_graphs=list(request.runtime_external_graphs),
        )
    return closure_context


def _runtime_to_language_portal_closure_context_cache_key(
    *,
    request: RuntimeToLanguageClosureLoweringRequest,
) -> _RuntimeToLanguagePortalClosureContextCacheKey | None:
    if request.target_language_plugin_id != CodeLanguage.python:
        return None
    if not (
        request.runtime_graph.object_projection_graphs
        or any(
            graph.object_projection_graphs for graph in request.runtime_external_graphs
        )
    ):
        return None
    return _RuntimeToLanguagePortalClosureContextCacheKey(
        runtime_graph_id=str(request.runtime_graph.id),
        runtime_graph_ref=_graph_ref(request.runtime_graph),
        runtime_graph_fqn_prefix=request.runtime_graph.fqn_prefix,
        external_graph_refs=tuple(
            (
                str(graph.id),
                _graph_ref(graph),
                graph.fqn_prefix,
            )
            for graph in request.runtime_external_graphs
        ),
    )


def _lower_runtime_graph_to_language(
    runtime_graph: ObjectConfigGraph,
    target_language_plugin_id: CodeLanguage,
    *,
    renderer_profile: str | None = None,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...],
    runtime_to_language_cache: RuntimeToLanguageLoweringCache | None = None,
    portal_closure_context: ObjectProjectionGraphPortalClosureContext | None = None,
    portal_closure_context_factory: _PortalClosureContextFactory | None = None,
    steps: list[LanguageMaterializationStep] | None = None,
    step_prefix: str = "runtime_to_language",
    graph_role: str = "primary",
) -> tuple[ObjectConfigGraph, GeneratedObjectConfigGraphNodeManifest | None]:
    if target_language_plugin_id == CodeLanguage.aware:
        return runtime_graph, None

    cache_key: _RuntimeToLanguageLoweringCacheKey | None = None
    if runtime_to_language_cache is not None:
        cache_key = _runtime_to_language_cache_key(
            runtime_graph=runtime_graph,
            target_language_plugin_id=target_language_plugin_id,
            renderer_profile=renderer_profile,
            external_runtime_graphs=external_runtime_graphs,
        )
        lookup_started_at = perf_counter()
        cached_result = runtime_to_language_cache.get(cache_key)
        cache_status = "hit" if cached_result is not None else "miss"
        _record_substep_duration(
            steps,
            f"{step_prefix}.{graph_role}.cache_{cache_status}",
            duration_s=round(perf_counter() - lookup_started_at, 6),
            parent_step=step_prefix,
            graph_role=graph_role,
            details={
                "cache_key": cache_key.digest,
                "cache_entry_count": runtime_to_language_cache.entry_count,
            },
        )
        if cached_result is not None:
            return cached_result

    with _record_substep(
        steps,
        f"{step_prefix}.{graph_role}.namespace_index",
        parent_step=step_prefix,
        graph_role=graph_role,
    ):
        namespace_by_code_id = build_namespace_by_code_id_from_graph(runtime_graph)
    if (
        target_language_plugin_id == CodeLanguage.python
        and portal_closure_context is None
        and portal_closure_context_factory is not None
    ):
        portal_closure_context = portal_closure_context_factory()
    with _record_substep(
        steps,
        f"{step_prefix}.{graph_role}.transformer_resolve",
        parent_step=step_prefix,
        graph_role=graph_role,
    ):
        transformer_kwargs: dict[str, object] = {
            "namespace_by_code_id": namespace_by_code_id,
            "external_graphs_by_id": {
                graph.id: graph for graph in external_runtime_graphs
            }
            or None,
        }
        if (
            target_language_plugin_id == CodeLanguage.python
            and portal_closure_context is not None
        ):
            transformer_kwargs["portal_closure_context"] = portal_closure_context
        transformer = cast(
            ObjectConfigGraphTransformer | None,
            MetaLanguagePluginRegistry.get_runtime_to_language_transformer(
                target_language_plugin_id,
                profile=renderer_profile,
                **transformer_kwargs,
            ),
        )
    if transformer is None:
        return runtime_graph, None

    with _record_substep(
        steps,
        f"{step_prefix}.{graph_role}.clone_graph",
        parent_step=step_prefix,
        graph_role=graph_role,
        details={"clone_strategy": "shallow_runtime_language_transformer_handoff"},
    ):
        graph = clone_runtime_graph_for_language_transformer_handoff(runtime_graph)
    with _record_substep(
        steps,
        f"{step_prefix}.{graph_role}.transform",
        parent_step=step_prefix,
        graph_role=graph_role,
    ):
        language_graph = transformer.transform(graph, code_primitive_type=None)
    with _record_substep(
        steps,
        f"{step_prefix}.{graph_role}.copy_runtime_surfaces",
        parent_step=step_prefix,
        graph_role=graph_role,
    ):
        language_graph.object_config_graph_annotations = list(
            runtime_graph.object_config_graph_annotations
        )
        language_graph.object_projection_graphs = [
            opg.model_copy(deep=False) for opg in runtime_graph.object_projection_graphs
        ]
        language_graph.object_config_graph_relationships = list(
            graph.object_config_graph_relationships
        )
    with _record_substep(
        steps,
        f"{step_prefix}.{graph_role}.generated_manifest",
        parent_step=step_prefix,
        graph_role=graph_role,
    ):
        generated_manifest = transformer.get_generated_ocg_node_manifest()
    if runtime_to_language_cache is not None and cache_key is not None:
        store_started_at = perf_counter()
        runtime_to_language_cache.store(
            cache_key,
            language_graph=language_graph,
            generated_manifest=generated_manifest,
        )
        _record_substep_duration(
            steps,
            f"{step_prefix}.{graph_role}.cache_store",
            duration_s=round(perf_counter() - store_started_at, 6),
            parent_step=step_prefix,
            graph_role=graph_role,
            details={
                "cache_key": cache_key.digest,
                "cache_entry_count": runtime_to_language_cache.entry_count,
            },
        )
    return language_graph, generated_manifest


def _runtime_to_language_cache_key(
    *,
    runtime_graph: ObjectConfigGraph,
    target_language_plugin_id: CodeLanguage,
    renderer_profile: str | None,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...],
) -> _RuntimeToLanguageLoweringCacheKey:
    return _RuntimeToLanguageLoweringCacheKey(
        target_language_plugin_id=target_language_plugin_id,
        renderer_profile=(renderer_profile.strip() if renderer_profile else None),
        runtime_graph_id=str(runtime_graph.id),
        runtime_graph_ref=_graph_ref(runtime_graph),
        runtime_graph_fqn_prefix=runtime_graph.fqn_prefix,
        external_graph_refs=tuple(
            sorted(
                (
                    str(graph.id),
                    _graph_ref(graph),
                    graph.fqn_prefix,
                )
                for graph in external_runtime_graphs
            )
        ),
    )


def _request_with_language_external_import_overrides(
    *,
    request: LanguagePluginMaterializationRequest,
    language_external_graphs: tuple[ObjectConfigGraph, ...],
) -> LanguagePluginMaterializationRequest:
    derived_overrides = _language_external_import_overrides(
        target_language_plugin_id=request.target_language_plugin_id,
        materialization_source=request.materialization_source,
        language_external_graphs=language_external_graphs,
    )
    if not derived_overrides:
        return request
    explicit_overrides = dict(request.import_overrides)
    merged_overrides = {**derived_overrides, **explicit_overrides}
    if merged_overrides == explicit_overrides:
        return request
    return replace(request, import_overrides=merged_overrides)


def _request_with_runtime_handler_local_import_overrides(
    *,
    request: LanguagePluginMaterializationRequest,
    language_graph: ObjectConfigGraph,
) -> LanguagePluginMaterializationRequest:
    source = (request.materialization_source or "").strip().lower()
    if source != "runtime_handlers":
        return request
    if request.target_language_plugin_id not in {
        CodeLanguage.python,
        CodeLanguage.dart,
    }:
        return request

    ontology_import_root = (request.stable_ids_import_root or "").strip()
    if not ontology_import_root:
        return request

    layout_strategy = MetaLanguagePluginRegistry.create_layout_strategy(
        request.target_language_plugin_id,
        Path("."),
        import_root=ontology_import_root,
    )
    layout_strategy.bind_graph(language_graph)

    local_overrides: dict[str, str] = {}
    for node in language_graph.object_config_graph_nodes:
        if node.class_config is not None:
            path = layout_strategy.get_class_file_path(node.class_config)
            local_overrides[str(node.class_config.id)] = (
                layout_strategy.get_module_import_path(path)
            )
        if node.enum_config is not None:
            path = layout_strategy.get_enum_file_path(node.enum_config)
            local_overrides[str(node.enum_config.id)] = (
                layout_strategy.get_module_import_path(path)
            )
    if not local_overrides:
        return request

    explicit_overrides = dict(request.import_overrides)
    merged_overrides = {**local_overrides, **explicit_overrides}
    if merged_overrides == explicit_overrides:
        return request
    return replace(request, import_overrides=merged_overrides)


def _language_external_import_overrides(
    *,
    target_language_plugin_id: CodeLanguage,
    materialization_source: str | None,
    language_external_graphs: tuple[ObjectConfigGraph, ...],
) -> dict[str, str]:
    if not language_external_graphs:
        return {}

    overrides: dict[str, str] = {}
    for graph in _sort_graphs(language_external_graphs):
        import_root = _external_language_import_root(
            graph=graph,
            target_language_plugin_id=target_language_plugin_id,
            materialization_source=materialization_source,
        )
        if not import_root:
            continue
        layout_strategy = MetaLanguagePluginRegistry.create_layout_strategy(
            target_language_plugin_id,
            Path("."),
            import_root=import_root,
        )
        layout_strategy.bind_graph(graph)
        for node in graph.object_config_graph_nodes:
            if node.class_config is not None:
                path = layout_strategy.get_class_file_path(node.class_config)
                path = _language_external_class_import_override_path(
                    target_language_plugin_id=target_language_plugin_id,
                    materialization_source=materialization_source,
                    path=path,
                )
                overrides[str(node.class_config.id)] = (
                    layout_strategy.get_module_import_path(path)
                )
            if node.enum_config is not None:
                path = layout_strategy.get_enum_file_path(node.enum_config)
                overrides[str(node.enum_config.id)] = (
                    layout_strategy.get_module_import_path(path)
                )
            function_config = get_node_function_config(node)
            if function_config is not None:
                path = layout_strategy.get_function_file_path(function_config)
                overrides[str(function_config.id)] = (
                    layout_strategy.get_module_import_path(path)
                )
    return dict(sorted(overrides.items()))


def _language_external_class_import_override_path(
    *,
    target_language_plugin_id: CodeLanguage,
    materialization_source: str | None,
    path: Path,
) -> Path:
    if (
        target_language_plugin_id == CodeLanguage.dart
        and (materialization_source or "").strip().lower() == "ontology_dto"
        and path.suffix == ".dart"
        and not path.stem.endswith("_model")
    ):
        return path.with_name(f"{path.stem}_model{path.suffix}")
    return path


def _external_language_import_root(
    *,
    graph: ObjectConfigGraph,
    target_language_plugin_id: CodeLanguage,
    materialization_source: str | None,
) -> str | None:
    if target_language_plugin_id not in {CodeLanguage.python, CodeLanguage.dart}:
        return None
    root = (graph.fqn_prefix or graph.name or "").strip().replace("-", "_")
    if not root:
        return None
    source = (materialization_source or "").strip().lower()
    if source == "ontology_dto":
        return f"{root}_ontology_dto"
    if source == "ontology_orm_models":
        return f"{root}_ontology_orm_models"
    if source == "ontology":
        return f"{root}_ontology"
    if source == "runtime_handlers":
        return f"{root}_ontology"
    return root


@contextmanager
def _language_render_output_root(
    *,
    request: LanguagePluginMaterializationRequest,
) -> Iterator[Path | None]:
    if not _should_build_language_package(request=request):
        yield request.output_root
        return
    with TemporaryDirectory(prefix="aware-meta-language-render-") as temp_dir:
        yield Path(temp_dir)


def _should_build_language_package(
    *,
    request: LanguagePluginMaterializationRequest,
) -> bool:
    if request.output_root is None or not request.import_root:
        return False
    if request.target_language_plugin_id not in {
        CodeLanguage.python,
        CodeLanguage.dart,
    }:
        return False
    return (request.materialization_source or "").strip().lower() in {
        "api",
        "ontology",
        "ontology_dto",
        "ontology_orm_models",
    }


def _build_packaged_language_files(
    *,
    request: LanguagePluginMaterializationRequest,
    render_output_root: Path | None,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[
    tuple[LanguageMaterializationGeneratedFile, ...],
    tuple[str, ...],
    Mapping[str, object],
    tuple[Path, ...],
    tuple[Path, ...],
]:
    if request.output_root is None or render_output_root is None:
        return generated_files, (), {}, (), ()
    output_root = request.output_root.resolve()
    render_root = render_output_root.resolve()
    import_root = request.import_root or request.package_name or ""
    if not import_root:
        return generated_files, (), {}, (), ()

    package_name = _language_distribution_package_name(request=request)
    package_metadata: dict[str, object] = {
        "aware_package_kind": request.materialization_source or "",
    }
    dependency_import_roots = _language_package_dependency_import_roots(
        request=request,
    )
    if dependency_import_roots:
        package_metadata["dependency_import_roots"] = list(dependency_import_roots)
    package_result = build_language_materialization_packages(
        LanguageMaterializationPackageBuildRequest(
            target_language_plugin_id=request.target_language_plugin_id,
            layout_base_dir=render_root,
            target_output_dir=output_root,
            rendered_files=tuple(render_root / item.path for item in generated_files),
            package_specs=(
                ObjectConfigGraphPackageSpec(
                    name=package_name,
                    package_name=package_name,
                    package_root=output_root,
                    import_root=(
                        None
                        if request.target_language_plugin_id == CodeLanguage.dart
                        else import_root
                    ),
                    metadata=package_metadata,
                ),
            ),
            materialization_source=request.materialization_source,
            renderer_profile=request.renderer_profile,
            renderer_kind=request.renderer_kind,
            package_kind=request.materialization_source,
        )
    )
    changed_package_file_refs = tuple(
        _package_result_file_path(
            output_root=output_root,
            file_path=changed_file,
        )
        for package in package_result.package_results
        for changed_file in package.changed_files
    )
    packaged_files: list[LanguageMaterializationGeneratedFile] = []
    for item in generated_files:
        if item.output_kind != "source_code":
            continue
        packaged_path = _packaged_language_file_path(
            request=request,
            output_root=output_root,
            import_root=import_root,
            relative_path=item.path,
        )
        if not packaged_path.exists():
            continue
        packaged_files.append(
            _generated_file_for_path(
                path=packaged_path,
                output_root=output_root,
                source_graph_ref=item.source_graph_ref,
                renderer_name=item.renderer_name,
                output_kind=item.output_kind,
                producer_step=item.producer_step,
            )
        )
    pruned_stale_files = _prune_stale_packaged_language_files(
        output_root=output_root,
        import_root=import_root,
        current_files=tuple(output_root / item.path for item in packaged_files)
        + tuple(
            package_file
            for package in package_result.package_results
            for package_file in package.files
        ),
    )
    removed_legacy_count = _remove_legacy_unpackaged_render_outputs(
        output_root=output_root,
        import_root=import_root,
        generated_files=generated_files,
    )
    return (
        _sort_generated_files(tuple(packaged_files)),
        package_result.warnings,
        {
            **dict(package_result.metrics),
            "removed_legacy_unpackage_render_output_count": removed_legacy_count,
            "pruned_stale_packaged_language_file_count": len(pruned_stale_files),
            "changed_package_file_count": len(changed_package_file_refs),
        },
        pruned_stale_files,
        changed_package_file_refs,
    )


def _package_result_file_path(*, output_root: Path, file_path: Path) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path.resolve()
    return (output_root / path).resolve()


def _packaged_language_file_path(
    *,
    request: LanguagePluginMaterializationRequest,
    output_root: Path,
    import_root: str,
    relative_path: Path,
) -> Path:
    if request.target_language_plugin_id == CodeLanguage.dart:
        return output_root / "lib" / relative_path
    return (
        output_root
        / import_root
        / _packaged_python_relative_path(
            import_root=import_root,
            relative_path=relative_path,
        )
    )


def _packaged_python_relative_path(
    *,
    import_root: str,
    relative_path: Path,
) -> Path:
    if relative_path.parts and relative_path.parts[0] == import_root:
        stripped = Path(*relative_path.parts[1:])
        return stripped if stripped.parts else Path(relative_path.name)
    return relative_path


def _language_package_dependency_import_roots(
    *,
    request: LanguagePluginMaterializationRequest,
) -> tuple[str, ...]:
    if request.target_language_plugin_id not in {
        CodeLanguage.python,
        CodeLanguage.dart,
    }:
        return ()
    own_import_root = (request.import_root or "").strip().replace("-", "_")
    roots: list[str] = []
    seen: set[str] = set()
    for graph in _sort_graphs(request.package_dependency_graphs):
        root = _external_language_import_root(
            graph=graph,
            target_language_plugin_id=request.target_language_plugin_id,
            materialization_source=request.materialization_source,
        )
        if not root or root == own_import_root or root in seen:
            continue
        roots.append(root)
        seen.add(root)
    if roots:
        return tuple(sorted(roots))
    for module_name in request.import_overrides.values():
        root = str(module_name).strip().split(".", maxsplit=1)[0].replace("-", "_")
        if not root or root == own_import_root or root in seen:
            continue
        roots.append(root)
        seen.add(root)
    return tuple(sorted(roots))


def _remove_legacy_unpackaged_render_outputs(
    *,
    output_root: Path,
    import_root: str,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> int:
    removed = 0
    output_root = output_root.resolve()
    for item in generated_files:
        if item.output_kind != "source_code":
            continue
        first_part = item.path.parts[0] if item.path.parts else ""
        if first_part in {"", ".aware", import_root}:
            continue
        candidate = (output_root / item.path).resolve()
        try:
            candidate.relative_to(output_root)
        except ValueError:
            continue
        if not candidate.is_file():
            continue
        candidate.unlink()
        removed += 1
        _remove_empty_parents(path=candidate.parent, stop=output_root)
    return removed


def _prune_stale_packaged_language_files(
    *,
    output_root: Path,
    import_root: str,
    current_files: tuple[Path, ...],
) -> tuple[Path, ...]:
    output_root = output_root.resolve()
    package_root = (output_root / import_root).resolve()
    if (
        not import_root
        or not package_root.is_dir()
        or not _is_path_within(path=package_root, root=output_root)
    ):
        return ()
    allowed = {
        path.resolve()
        for path in current_files
        if _is_path_within(path=path.resolve(), root=output_root)
    }
    removed: list[Path] = []
    for candidate in sorted(package_root.rglob("*"), key=lambda item: item.as_posix()):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        resolved = candidate.resolve()
        if resolved in allowed:
            continue
        candidate.unlink()
        removed.append(resolved.relative_to(output_root))
        _remove_empty_parents(path=candidate.parent, stop=package_root)
    return tuple(removed)


def _should_prune_unpacked_language_files(
    *,
    request: LanguagePluginMaterializationRequest,
) -> bool:
    return request.target_language_plugin_id == CodeLanguage.sql


def _prune_stale_unpacked_language_files(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[Path, ...]:
    if request.output_root is None:
        return ()
    output_root = request.output_root.resolve()
    if not output_root.is_dir() or not _is_path_within(
        path=output_root,
        root=output_root,
    ):
        return ()
    current_sql_paths = {
        (output_root / item.path).resolve()
        for item in generated_files
        if item.output_kind == "source_code" and item.path.suffix == ".sql"
    }
    if not current_sql_paths:
        return ()
    removed: list[Path] = []
    for candidate in sorted(
        output_root.rglob("*.sql"), key=lambda item: item.as_posix()
    ):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        resolved = candidate.resolve()
        if not _is_path_within(path=resolved, root=output_root):
            continue
        if resolved in current_sql_paths:
            continue
        candidate.unlink()
        removed.append(resolved.relative_to(output_root))
        _remove_empty_parents(path=candidate.parent, stop=output_root)
    return tuple(removed)


def _is_path_within(*, path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _remove_empty_parents(*, path: Path, stop: Path) -> None:
    current = path.resolve()
    stop = stop.resolve()
    while current != stop and stop in current.parents:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def _render_language_graph(
    *,
    request: LanguagePluginMaterializationRequest,
    output_root: Path | None = None,
    runtime_graph: ObjectConfigGraph,
    language_graph: ObjectConfigGraph,
    language_external_graphs: tuple[ObjectConfigGraph, ...],
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None,
) -> tuple[
    tuple[LanguageMaterializationGeneratedFile, ...],
    tuple[str, ...],
    tuple[Path, ...],
    Mapping[str, Mapping[str, float]],
]:
    if output_root is None:
        output_root = request.output_root
    if output_root is None:
        raise ValueError("output_root is required when emit_files=True.")
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    layout_strategy = MetaLanguagePluginRegistry.create_layout_strategy(
        request.target_language_plugin_id,
        output_root,
        generated_ocg_node_manifest=generated_ocg_node_manifest,
        import_root=request.import_root,
    )
    rendered = _render_prepared_language_graph(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=request.target_language_plugin_id,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=layout_strategy,
            renderer_profile=request.renderer_profile,
            renderer_kind=request.renderer_kind,
            source_graph=request.source_graph,
            language_external_graphs=language_external_graphs,
            profile_inputs=request.profile_inputs,
            import_overrides=request.import_overrides,
            renderer_policies=_language_renderer_policies(
                source_graph=request.source_graph,
                runtime_graph=runtime_graph,
                stable_ids_import_root=request.stable_ids_import_root,
                stable_ids_ownership=request.stable_ids_ownership,
                stable_ids_resolution_policy=request.stable_ids_resolution_policy,
                function_impl_ownership=request.function_impl_ownership,
                function_impl_parity_policy=request.function_impl_parity_policy,
            ),
            overwrite=request.overwrite,
        )
    )
    files: list[LanguageMaterializationGeneratedFile] = []
    source_graph_ref = language_graph.hash or str(language_graph.id)
    for renderer_name, paths in _paths_by_renderer(
        renderer_names=rendered.renderer_names,
        written_files=rendered.written_files,
        renderer_file_counts=rendered.renderer_file_counts,
    ).items():
        for path in paths:
            files.append(
                _generated_file_for_path(
                    path=path,
                    output_root=output_root,
                    source_graph_ref=source_graph_ref,
                    renderer_name=renderer_name,
                )
            )
    return (
        _sort_generated_files(tuple(files)),
        rendered.warnings,
        tuple(Path(path).resolve() for path in rendered.changed_files),
        rendered.renderer_phase_timings,
    )


def _language_renderer_policies(
    *,
    source_graph: ObjectConfigGraph | None = None,
    runtime_graph: ObjectConfigGraph,
    stable_ids_import_root: str | None = None,
    stable_ids_ownership: str | None = None,
    stable_ids_resolution_policy: str | None = None,
    function_impl_ownership: str | None = None,
    function_impl_parity_policy: str | None = None,
) -> Mapping[str, Mapping[str, object | None]]:
    stable_ids_policy: dict[str, object | None] = {
        "stable_ids_source_graph": runtime_graph,
    }
    if stable_ids_import_root is not None and stable_ids_import_root.strip():
        stable_ids_policy["stable_ids_import_root"] = stable_ids_import_root.strip()
    if stable_ids_ownership is not None and stable_ids_ownership.strip():
        stable_ids_policy["stable_ids_ownership"] = stable_ids_ownership.strip().lower()
    if (
        stable_ids_resolution_policy is not None
        and stable_ids_resolution_policy.strip()
    ):
        stable_ids_policy["stable_ids_resolution_policy"] = (
            stable_ids_resolution_policy.strip().lower()
        )
    meta_runtime_handlers_policy: dict[str, object | None] = dict(stable_ids_policy)
    if source_graph is not None:
        meta_runtime_handlers_policy["function_impl_source_graph"] = source_graph
    if function_impl_ownership is not None and function_impl_ownership.strip():
        meta_runtime_handlers_policy["function_impl_ownership"] = (
            function_impl_ownership.strip().lower()
        )
    if function_impl_parity_policy is not None and function_impl_parity_policy.strip():
        meta_runtime_handlers_policy["function_impl_parity_policy"] = (
            function_impl_parity_policy.strip().lower()
        )
    runtime_handler_policy = dict(stable_ids_policy)
    return {
        "stable_ids": dict(stable_ids_policy),
        "runtime_handlers": dict(runtime_handler_policy),
        "runtime_handlers_impl": dict(runtime_handler_policy),
        "runtime_handlers_meta": meta_runtime_handlers_policy,
    }


def _render_prepared_language_graph(
    request: LanguageMaterializationRenderRequest,
) -> LanguageMaterializationRenderResult:
    _ensure_target_language_plugin(request.target_language_plugin_id)
    output_root = request.output_root.resolve()
    if request.renderer_kind:
        renderers = {
            request.renderer_kind: MetaLanguagePluginRegistry.get_renderer(
                request.target_language_plugin_id,
                output_root,
                request.layout_strategy,
                overwrite=request.overwrite,
                kind=request.renderer_kind,
                profile=request.renderer_profile,
            )
        }
    else:
        renderers = MetaLanguagePluginRegistry.get_default_renderers(
            request.target_language_plugin_id,
            output_root,
            request.layout_strategy,
            overwrite=request.overwrite,
            profile=request.renderer_profile,
        )

    written_files: list[Path] = []
    changed_files: list[Path] = []
    warnings: list[str] = []
    renderer_file_counts: dict[str, int] = {}
    renderer_warning_counts: dict[str, int] = {}
    renderer_warnings: dict[str, tuple[str, ...]] = {}
    renderer_phase_timings: dict[str, Mapping[str, float]] = {}
    fail_on_warning = set(request.fail_on_renderer_warnings)
    language_overlay = _select_language_overlay(
        target_language=request.target_language_plugin_id,
        language_graph=request.language_graph,
        source_graph=request.source_graph,
    )
    for renderer_name, renderer in renderers.items():
        renderer.set_profile_inputs(dict(request.profile_inputs))
        policy = request.renderer_policies.get(renderer_name)
        if policy is not None:
            renderer.set_policy(cast(ObjectConfigGraphRendererPolicy, dict(policy)))
        renderer.set_external_graphs(list(request.language_external_graphs))
        renderer.set_import_overrides(dict(request.import_overrides))
        if language_overlay is not None:
            renderer.set_language_overlay(language_overlay)

        render_graph_started_at = perf_counter()
        rendered_raw_paths = renderer.render_graph(
            request.language_graph,
            candidate_paths=(
                request.candidate_paths if request.candidate_paths else None
            ),
        )
        render_graph_duration_s = round(
            max(perf_counter() - render_graph_started_at, 0.0),
            6,
        )
        rendered_paths = tuple(Path(path) for path in (rendered_raw_paths or ()))
        renderer_file_counts[renderer_name] = len(rendered_paths)
        written_files.extend(rendered_paths)
        changed_files.extend(
            Path(path).resolve() for path in getattr(renderer, "last_changed_files", ())
        )
        phase_timings = {
            "render_graph": render_graph_duration_s,
            **_renderer_internal_phase_timings(renderer),
        }
        if phase_timings:
            renderer_phase_timings[renderer_name] = phase_timings
        warning_messages = tuple(renderer.get_warnings())
        renderer_warning_counts[renderer_name] = len(warning_messages)
        renderer_warnings[renderer_name] = warning_messages
        warnings.extend(warning_messages)
        if renderer_name in fail_on_warning and warning_messages:
            details = "; ".join(warning_messages[:3])
            if len(warning_messages) > 3:
                details += f"; ... ({len(warning_messages)} total)"
            raise ValueError(f"Renderer warning error for {renderer_name!r}: {details}")

    return LanguageMaterializationRenderResult(
        written_files=tuple(written_files),
        changed_files=tuple(changed_files),
        warnings=tuple(warnings),
        renderer_names=tuple(renderers),
        renderer_file_counts=renderer_file_counts,
        renderer_warning_counts=renderer_warning_counts,
        renderer_warnings=renderer_warnings,
        renderer_phase_timings=renderer_phase_timings,
    )


def _renderer_internal_phase_timings(renderer: object) -> dict[str, float]:
    candidates = (renderer, getattr(renderer, "renderer_language", None))
    for candidate in candidates:
        if candidate is None:
            continue
        getter = getattr(candidate, "get_render_phase_timings", None)
        raw_timings = getter() if callable(getter) else None
        if raw_timings is None:
            raw_timings = getattr(candidate, "last_render_phase_timings", None)
        if not isinstance(raw_timings, Mapping):
            continue
        timings: dict[str, float] = {}
        for raw_name, raw_duration_s in raw_timings.items():
            name = str(raw_name).strip()
            if not name or isinstance(raw_duration_s, bool):
                continue
            try:
                duration_s = round(max(float(raw_duration_s), 0.0), 6)
            except (TypeError, ValueError):
                continue
            timings[name] = duration_s
        if timings:
            return dict(sorted(timings.items()))
    return {}


def _select_language_overlay(
    *,
    target_language: CodeLanguage,
    language_graph: ObjectConfigGraph,
    source_graph: ObjectConfigGraph | None,
) -> ObjectConfigGraphOverlay | None:
    for overlay in language_graph.object_config_graph_overlays:
        if overlay.language == target_language:
            return overlay
    if source_graph is None:
        return None
    return next(
        (
            overlay
            for overlay in source_graph.object_config_graph_overlays
            if overlay.language == target_language
        ),
        None,
    )


def _paths_by_renderer(
    *,
    renderer_names: tuple[str, ...],
    written_files: tuple[Path, ...],
    renderer_file_counts: Mapping[str, int],
) -> dict[str, tuple[Path, ...]]:
    paths_by_renderer: dict[str, tuple[Path, ...]] = {}
    offset = 0
    for renderer_name in renderer_names:
        count = renderer_file_counts.get(renderer_name, 0)
        paths_by_renderer[renderer_name] = written_files[offset : offset + count]
        offset += count
    return paths_by_renderer


def _sort_generated_files(
    files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[LanguageMaterializationGeneratedFile, ...]:
    return tuple(
        sorted(
            files,
            key=lambda item: (
                item.path.as_posix(),
                item.producer_step,
                item.renderer_name or "",
            ),
        )
    )


def _generated_file_for_path(
    *,
    path: Path,
    output_root: Path,
    source_graph_ref: str | None,
    renderer_name: str | None,
    output_kind: str = "source_code",
    producer_step: str = "render",
) -> LanguageMaterializationGeneratedFile:
    resolved = path.resolve()
    data = resolved.read_bytes()
    try:
        rel_path = resolved.relative_to(output_root)
    except ValueError:
        rel_path = resolved
    return LanguageMaterializationGeneratedFile(
        path=rel_path,
        output_kind=output_kind,
        producer_step=producer_step,
        sha256=sha256(data).hexdigest(),
        size_bytes=len(data),
        source_graph_ref=source_graph_ref,
        renderer_name=renderer_name,
    )


def _absolute_generated_file_path(
    *,
    output_root: Path,
    generated_file: LanguageMaterializationGeneratedFile,
) -> Path:
    path = generated_file.path
    return path if path.is_absolute() else output_root / path


def _post_step_generated_files(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    candidate_paths: set[Path] | None,
) -> tuple[LanguageMaterializationGeneratedFile, ...]:
    if candidate_paths is None or request.output_root is None:
        return generated_files
    normalized_candidates = {Path(path).resolve() for path in candidate_paths}
    output_root = request.output_root.resolve()
    selected_files = tuple(
        generated_file
        for generated_file in generated_files
        if _absolute_generated_file_path(
            output_root=output_root,
            generated_file=generated_file,
        ).resolve()
        in normalized_candidates
    )
    formatter_unstable_files = _python_formatter_unstable_generated_files(
        request=request,
        generated_files=generated_files,
        selected_files=selected_files,
    )
    if not formatter_unstable_files:
        return selected_files
    return _sort_generated_files((*selected_files, *formatter_unstable_files))


def _python_formatter_unstable_generated_files(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    selected_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[LanguageMaterializationGeneratedFile, ...]:
    if (
        request.target_language_plugin_id != CodeLanguage.python
        or request.output_root is None
    ):
        return ()
    try:
        import black
    except Exception:
        return ()
    output_root = request.output_root.resolve()
    selected_paths = {
        _absolute_generated_file_path(
            output_root=output_root,
            generated_file=generated_file,
        ).resolve()
        for generated_file in selected_files
    }
    formatter_unstable_files: list[LanguageMaterializationGeneratedFile] = []
    for generated_file in generated_files:
        if generated_file.output_kind != "source_code":
            continue
        if generated_file.path.suffix not in {".py", ".pyi"}:
            continue
        path = _absolute_generated_file_path(
            output_root=output_root,
            generated_file=generated_file,
        ).resolve()
        if path in selected_paths or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
            mode = black.FileMode(line_length=120, is_pyi=(path.suffix == ".pyi"))
            if str(black.format_str(text, mode=mode)) == text:
                continue
        except Exception:
            pass
        formatter_unstable_files.append(generated_file)
    return tuple(formatter_unstable_files)


def _post_step_candidate_metrics(
    *,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    candidate_paths: set[Path] | None,
    selected_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> dict[str, object]:
    if candidate_paths is None:
        return {}
    selected_count = len(selected_files)
    return {
        "post_step_candidate_changed_file_count": len(candidate_paths),
        "post_step_selected_generated_file_count": selected_count,
        "post_step_skipped_unchanged_file_count": max(
            len(generated_files) - selected_count,
            0,
        ),
    }


def _refresh_generated_files_after_post_steps(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    execution_results: tuple[LanguageMaterializationPostStepExecutionResult, ...],
) -> tuple[LanguageMaterializationGeneratedFile, ...]:
    if request.output_root is None or not execution_results:
        return generated_files
    output_root = request.output_root.resolve()
    producer_hints = language_materialization_post_step_execution_path_hints(
        execution_results
    )
    refreshed: list[LanguageMaterializationGeneratedFile] = []
    for generated_file in generated_files:
        path = _absolute_generated_file_path(
            output_root=output_root,
            generated_file=generated_file,
        ).resolve()
        if not path.exists():
            continue
        producer_step = producer_hints.get(path)
        refreshed.append(
            _generated_file_for_path(
                path=path,
                output_root=output_root,
                source_graph_ref=generated_file.source_graph_ref,
                renderer_name=generated_file.renderer_name,
                output_kind=generated_file.output_kind,
                producer_step=(
                    producer_step.value
                    if producer_step is not None
                    else generated_file.producer_step
                ),
            )
        )
    return _sort_generated_files(tuple(refreshed))


def _produce_plugin_declared_outputs(
    *,
    request: LanguagePluginMaterializationRequest,
    runtime_graph: ObjectConfigGraph,
    language_graph: ObjectConfigGraph,
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None,
    language_external_graphs: tuple[ObjectConfigGraph, ...],
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[
    tuple[LanguageMaterializationGeneratedFile, ...],
    tuple[str, ...],
    Mapping[str, object],
    tuple[LanguageMaterializationOwnershipReceipt, ...],
]:
    if request.output_root is None:
        return (), (), {}, ()

    result = produce_language_plugin_declared_outputs(
        LanguagePluginDeclaredOutputProductionRequest(
            target_language_plugin_id=request.target_language_plugin_id,
            output_root=request.output_root.resolve(),
            source_graph=request.source_graph,
            runtime_graph=runtime_graph,
            language_graph=language_graph,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            destinations=request.declared_output_destinations,
            language_external_graphs=language_external_graphs,
            generated_file_paths=tuple(item.path for item in generated_files),
            package_name=request.package_name,
            import_root=request.import_root,
            package_dependency_import_roots=_language_package_dependency_import_roots(
                request=request,
            ),
            renderer_profile=request.renderer_profile,
            renderer_kind=request.renderer_kind,
            materialization_source=request.materialization_source,
            entity_file_paths={},
            profile_inputs=request.profile_inputs,
            import_overrides=request.import_overrides,
            object_config_graph_package_id=request.object_config_graph_package_id,
            object_config_graph_commit_id=request.object_config_graph_commit_id,
            source_code_package_id=request.source_code_package_id,
            source_graph_ref=request.source_graph.hash or str(request.source_graph.id),
            runtime_graph_ref=runtime_graph.hash or str(runtime_graph.id),
            language_graph_ref=language_graph.hash or str(language_graph.id),
        )
    )
    return (
        result.generated_files,
        result.warnings,
        result.metrics,
        result.ownership_receipts,
    )


def _generated_file_for_produced_declared_output(
    *,
    produced_file: MetaLanguageDeclaredOutputProducedFile,
    output_root: Path,
    source_graph_ref: str | None,
) -> LanguageMaterializationGeneratedFile:
    path = produced_file.path
    resolved = path if path.is_absolute() else output_root / path
    resolved.parent.mkdir(parents=True, exist_ok=True)
    if produced_file.content_bytes is not None:
        resolved.write_bytes(produced_file.content_bytes)
    elif produced_file.content_text is not None:
        resolved.write_text(produced_file.content_text, encoding="utf-8")
    elif not resolved.exists():
        raise FileNotFoundError(
            "Declared output producer returned no content for missing file "
            f"{path.as_posix()!r}."
        )
    return _generated_file_for_path(
        path=resolved,
        output_root=output_root,
        source_graph_ref=source_graph_ref,
        renderer_name="declared_output_producer",
        output_kind=produced_file.output_kind or "manifest",
        producer_step=produced_file.producer_step,
    )


def _run_quality_gates(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[tuple[LanguageMaterializationStep, ...], tuple[str, ...]]:
    _ensure_code_language_plugin(request.target_language_plugin_id)
    plugin = CodeLanguagePluginRegistry.get(request.target_language_plugin_id)
    quality_gate_by_id = {gate.gate_id: gate for gate in plugin.quality_gates}
    gate_ids = tuple(gate_id for gate_id in request.quality_gate_ids if gate_id.strip())
    missing_gate_ids = tuple(
        gate_id for gate_id in gate_ids if gate_id not in quality_gate_by_id
    )
    if missing_gate_ids:
        raise ValueError(
            "Unknown language quality gate(s) for "
            f"{request.target_language_plugin_id.value!r}: "
            + ", ".join(sorted(missing_gate_ids))
        )

    targets = _quality_gate_targets(
        output_root=request.output_root,
        generated_files=generated_files,
    )
    steps: list[LanguageMaterializationStep] = []
    warnings: list[str] = []
    for gate_id in gate_ids:
        gate = quality_gate_by_id[gate_id]
        result = run_code_language_quality_gate(
            CodeLanguageQualityGateRunRequest(
                gate=gate,
                targets=targets,
                cwd=request.output_root,
                timeout_s=request.quality_gate_timeout_s,
            )
        )
        steps.append(_quality_gate_step_from_result(result))
        if result.status != "succeeded":
            warnings.append(_quality_gate_warning(result))
    return tuple(steps), tuple(warnings)


def _build_package_outputs(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    deleted_file_refs: tuple[Path, ...] = (),
) -> tuple[LanguageMaterializationPackageOutput, ...]:
    generated_ref_paths = {item.path.as_posix() for item in generated_files}
    deleted_refs = _dedupe_paths(
        (
            *deleted_file_refs,
            *_legacy_packaged_language_deleted_file_refs(
                request=request,
                generated_files=generated_files,
            ),
        )
    )
    deleted_refs = tuple(
        path for path in deleted_refs if path.as_posix() not in generated_ref_paths
    )
    if (not generated_files and not deleted_refs) or request.output_root is None:
        return ()
    package_name = _language_distribution_package_name(request=request)
    return (
        LanguageMaterializationPackageOutput(
            package_name=package_name,
            output_root=request.output_root.resolve(),
            import_root=request.import_root,
            generated_file_refs=tuple(item.path for item in generated_files),
            deleted_file_refs=deleted_refs,
        ),
    )


def _legacy_packaged_language_deleted_file_refs(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[Path, ...]:
    import_root = (request.import_root or "").strip()
    if (
        request.target_language_plugin_id != CodeLanguage.python
        or not import_root
        or (request.materialization_source or "").strip().lower()
        not in {"api", "ontology", "ontology_dto", "ontology_orm_models"}
    ):
        return ()
    refs: set[Path] = set()
    for item in generated_files:
        parts = item.path.parts
        if not parts or parts[0] != import_root:
            continue
        if item.output_kind == "source_code" and len(parts) > 1:
            refs.add(Path(import_root) / import_root / Path(*parts[1:]))
        if item.path.as_posix() == f"{import_root}/_aware/orm.graph.binding.msgpack":
            refs.add(Path(import_root) / "_aware" / "ocg.binding.snapshot.msgpack")
    return tuple(sorted(refs, key=lambda path: path.as_posix()))


def _dedupe_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(
        Path(path_text) for path_text in sorted({path.as_posix() for path in paths})
    )


def _language_distribution_package_name(
    *,
    request: LanguagePluginMaterializationRequest,
) -> str:
    import_root = (request.import_root or "").strip()
    if (
        request.target_language_plugin_id == CodeLanguage.python
        and import_root
        and (request.materialization_source or "").strip().lower()
        in {"api", "ontology", "ontology_dto", "ontology_orm_models"}
    ):
        return import_root.replace("_", "-")
    if (
        request.target_language_plugin_id == CodeLanguage.dart
        and import_root
        and (request.materialization_source or "").strip().lower()
        in {"api", "ontology", "ontology_dto", "ontology_orm_models"}
    ):
        return import_root
    return (
        request.package_name
        or request.import_root
        or request.source_graph.fqn_prefix
        or request.source_graph.name
    )


def _build_declared_artifact_outputs(
    *,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    package_outputs: tuple[LanguageMaterializationPackageOutput, ...],
) -> tuple[LanguageMaterializationArtifactOutput, ...]:
    descriptors = AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
        provider_key=_META_PROVIDER_KEY,
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
    )
    artifact_outputs: list[LanguageMaterializationArtifactOutput] = []
    for descriptor in descriptors:
        generated_file_refs: tuple[Path, ...] = ()
        package_output_refs: tuple[str, ...] = ()
        if (
            descriptor.output_key
            == META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY
        ):
            generated_file_refs = tuple(
                item.path
                for item in generated_files
                if item.output_kind == "source_code"
            )
            if not generated_file_refs:
                continue
        elif descriptor.output_key == META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY:
            package_output_refs = tuple(item.package_name for item in package_outputs)
            if not package_output_refs:
                continue
        else:
            continue
        artifact_outputs.append(
            LanguageMaterializationArtifactOutput(
                provider_key=_META_PROVIDER_KEY,
                semantic_owner=descriptor.semantic_owner,
                producer_key=descriptor.producer_key,
                output_key=descriptor.output_key,
                artifact_family=descriptor.artifact_family,
                artifact_role=descriptor.artifact_role,
                output_kind=descriptor.output_kind,
                package_output_key=descriptor.package_output_key,
                generated_file_refs=generated_file_refs,
                package_output_refs=package_output_refs,
                required_for=descriptor.required_for,
                provider_payload=dict(descriptor.provider_payload or {}),
            )
        )
    return tuple(
        sorted(
            artifact_outputs,
            key=lambda item: (
                item.semantic_owner,
                item.producer_key,
                item.output_key,
            ),
        )
    )


def _build_plugin_declared_outputs(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[LanguageMaterializationPluginDeclaredOutput, ...]:
    if not request.emit_files:
        return ()
    code_plugin = MetaLanguagePluginRegistry.get(
        request.target_language_plugin_id
    ).code_plugin
    descriptors = getattr(code_plugin, "materialization_artifact_outputs", ())
    if not descriptors:
        return ()

    generated_path_by_posix = {
        generated_file.path.as_posix(): generated_file.path
        for generated_file in generated_files
    }
    outputs: list[LanguageMaterializationPluginDeclaredOutput] = []
    for descriptor in descriptors:
        if not _plugin_declared_output_applies_to_request(
            descriptor=descriptor,
            request=request,
        ):
            continue
        resolved_paths = tuple(
            _resolve_plugin_declared_path_template(
                template=template,
                request=request,
            )
            for template in descriptor.path_templates
        )
        resolved_path_set = {path.as_posix() for path in resolved_paths}
        generated_file_refs = tuple(
            generated_path_by_posix[path]
            for path in sorted(resolved_path_set)
            if path in generated_path_by_posix
        )
        outputs.append(
            LanguageMaterializationPluginDeclaredOutput(
                language=request.target_language_plugin_id,
                output_key=descriptor.output_key,
                output_kind=descriptor.output_kind,
                artifact_role=descriptor.artifact_role,
                producer_step=descriptor.producer_step,
                path_templates=descriptor.path_templates,
                resolved_paths=resolved_paths,
                generated_file_refs=generated_file_refs,
                required_for=descriptor.required_for,
                renderer_profiles=descriptor.renderer_profiles,
                renderer_kinds=descriptor.renderer_kinds,
                materialization_sources=descriptor.materialization_sources,
                required=descriptor.required,
                status="materialized" if generated_file_refs else "declared",
                provider_payload=dict(descriptor.provider_payload or {}),
            )
        )
    return tuple(sorted(outputs, key=lambda item: item.output_key))


def _plugin_declared_output_applies_to_request(
    *,
    descriptor: object,
    request: LanguagePluginMaterializationRequest,
) -> bool:
    renderer_profiles = tuple(getattr(descriptor, "renderer_profiles", ()) or ())
    if renderer_profiles and request.renderer_profile not in renderer_profiles:
        return False
    renderer_kinds = tuple(getattr(descriptor, "renderer_kinds", ()) or ())
    if renderer_kinds and request.renderer_kind not in renderer_kinds:
        return False
    materialization_sources = tuple(
        getattr(descriptor, "materialization_sources", ()) or ()
    )
    if (
        materialization_sources
        and request.materialization_source not in materialization_sources
    ):
        return False
    return True


def _build_ownership_receipts(
    *,
    request: LanguagePluginMaterializationRequest,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    package_outputs: tuple[LanguageMaterializationPackageOutput, ...],
    artifact_outputs: tuple[LanguageMaterializationArtifactOutput, ...],
    plugin_declared_outputs: tuple[LanguageMaterializationPluginDeclaredOutput, ...],
    source_graph_hash: str | None,
    runtime_graph_hash: str | None,
    language_graph_hash: str | None,
) -> tuple[LanguageMaterializationOwnershipReceipt, ...]:
    generated_by_path = {item.path.as_posix(): item for item in generated_files}
    receipts: list[LanguageMaterializationOwnershipReceipt] = []
    for artifact_output in artifact_outputs:
        for path in artifact_output.generated_file_refs:
            generated_file = generated_by_path.get(path.as_posix())
            receipts.append(
                _ownership_receipt(
                    request=request,
                    output_key=artifact_output.output_key,
                    artifact_role=artifact_output.artifact_role,
                    output_kind=artifact_output.output_kind,
                    required_for=artifact_output.required_for,
                    path=path,
                    generated_file=generated_file,
                    package_output_key=artifact_output.package_output_key,
                    provider_payload=artifact_output.provider_payload,
                    source_graph_hash=source_graph_hash,
                    runtime_graph_hash=runtime_graph_hash,
                    language_graph_hash=language_graph_hash,
                )
            )
        for package_name in artifact_output.package_output_refs:
            receipts.append(
                _ownership_receipt(
                    request=request,
                    output_key=artifact_output.output_key,
                    artifact_role=artifact_output.artifact_role,
                    output_kind=artifact_output.output_kind,
                    required_for=artifact_output.required_for,
                    package_name=package_name,
                    package_output_key=artifact_output.package_output_key,
                    provider_payload=artifact_output.provider_payload,
                    source_graph_hash=source_graph_hash,
                    runtime_graph_hash=runtime_graph_hash,
                    language_graph_hash=language_graph_hash,
                )
            )
    for declared_output in plugin_declared_outputs:
        status = _declared_output_receipt_status(declared_output)
        provider_payload = {
            **dict(declared_output.provider_payload or {}),
            "path_templates": tuple(path for path in declared_output.path_templates),
            "renderer_profiles": tuple(declared_output.renderer_profiles),
            "renderer_kinds": tuple(declared_output.renderer_kinds),
            "materialization_sources": tuple(declared_output.materialization_sources),
            "required": declared_output.required,
        }
        if declared_output.generated_file_refs:
            for path in declared_output.generated_file_refs:
                generated_file = generated_by_path.get(path.as_posix())
                receipts.append(
                    _ownership_receipt(
                        request=request,
                        output_key=declared_output.output_key,
                        artifact_role=declared_output.artifact_role,
                        output_kind=declared_output.output_kind,
                        required_for=declared_output.required_for,
                        producer_step=declared_output.producer_step,
                        path=path,
                        generated_file=generated_file,
                        status=status,
                        provider_payload=provider_payload,
                        source_graph_hash=source_graph_hash,
                        runtime_graph_hash=runtime_graph_hash,
                        language_graph_hash=language_graph_hash,
                    )
                )
        else:
            receipts.append(
                _ownership_receipt(
                    request=request,
                    output_key=declared_output.output_key,
                    artifact_role=declared_output.artifact_role,
                    output_kind=declared_output.output_kind,
                    required_for=declared_output.required_for,
                    producer_step=declared_output.producer_step,
                    status=status,
                    provider_payload=provider_payload,
                    source_graph_hash=source_graph_hash,
                    runtime_graph_hash=runtime_graph_hash,
                    language_graph_hash=language_graph_hash,
                )
            )
    return _sort_ownership_receipts(receipts)


def _build_produced_file_ownership_receipts(
    *,
    request: LanguagePluginDeclaredOutputProductionRequest,
    produced_files: tuple[MetaLanguageDeclaredOutputProducedFile, ...],
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...] = (),
) -> tuple[LanguageMaterializationOwnershipReceipt, ...]:
    if not produced_files:
        return ()
    descriptors = _language_materialization_output_descriptors(
        request.target_language_plugin_id
    )
    descriptor_by_output_key = {item.output_key: item for item in descriptors}
    generated_by_path = {item.path.as_posix(): item for item in generated_files}
    receipts: list[LanguageMaterializationOwnershipReceipt] = []
    for produced_file in produced_files:
        descriptor = descriptor_by_output_key.get(produced_file.output_key)
        if descriptor is None:
            continue
        path = _produced_file_receipt_path(
            output_root=request.output_root,
            produced_file=produced_file,
        )
        generated_file = generated_by_path.get(path.as_posix())
        payload_bytes = _produced_file_payload_bytes(produced_file)
        digest = generated_file.sha256 if generated_file is not None else None
        size_bytes = generated_file.size_bytes if generated_file is not None else None
        if digest is None and payload_bytes is not None:
            digest = sha256(payload_bytes).hexdigest()
            size_bytes = len(payload_bytes)
        receipts.append(
            LanguageMaterializationOwnershipReceipt(
                producer_provider_key=_META_PROVIDER_KEY,
                semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
                producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
                output_key=descriptor.output_key,
                artifact_key=_receipt_artifact_key(
                    language=request.target_language_plugin_id,
                    output_key=descriptor.output_key,
                    path=path,
                    package_name=_package_name_for_receipt_path(
                        path=path,
                        destinations=request.destinations,
                        fallback=request.package_name,
                    ),
                ),
                artifact_family=META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
                artifact_role=produced_file.artifact_role or descriptor.artifact_role,
                output_kind=produced_file.output_kind or descriptor.output_kind,
                target_language_plugin_id=request.target_language_plugin_id,
                status="available",
                producer_step=produced_file.producer_step or descriptor.producer_step,
                package_name=_package_name_for_receipt_path(
                    path=path,
                    destinations=request.destinations,
                    fallback=request.package_name,
                ),
                required_for=descriptor.required_for,
                path=path,
                digest=digest,
                size_bytes=size_bytes,
                source_code_package_id=request.source_code_package_id,
                object_config_graph_package_id=request.object_config_graph_package_id,
                object_config_graph_commit_id=request.object_config_graph_commit_id,
                source_object_instance_graph_commit_id=(
                    request.source_object_instance_graph_commit_id
                ),
                input_object_instance_graph_commit_id=(
                    request.input_object_instance_graph_commit_id
                ),
                source_graph_ref=request.source_graph_ref
                or request.source_graph.hash
                or str(request.source_graph.id),
                runtime_graph_ref=request.runtime_graph_ref
                or request.runtime_graph.hash
                or str(request.runtime_graph.id),
                language_graph_ref=request.language_graph_ref
                or request.language_graph.hash
                or str(request.language_graph.id),
                provider_payload={
                    **dict(descriptor.provider_payload or {}),
                    **dict(produced_file.provider_payload or {}),
                    "path_templates": tuple(descriptor.path_templates),
                },
            )
        )
    return _sort_ownership_receipts(receipts)


def _language_materialization_output_descriptors(
    target_language_plugin_id: CodeLanguage,
) -> tuple[CodeLanguageMaterializationOutputDescriptor, ...]:
    _ensure_target_language_plugin(target_language_plugin_id)
    plugin = MetaLanguagePluginRegistry.get(target_language_plugin_id).code_plugin
    return tuple(getattr(plugin, "materialization_artifact_outputs", ()) or ())


def _ownership_receipt(
    *,
    request: LanguagePluginMaterializationRequest,
    output_key: str,
    artifact_role: str,
    output_kind: str,
    required_for: tuple[str, ...],
    source_graph_hash: str | None,
    runtime_graph_hash: str | None,
    language_graph_hash: str | None,
    path: Path | None = None,
    generated_file: LanguageMaterializationGeneratedFile | None = None,
    package_name: str | None = None,
    package_output_key: str | None = None,
    producer_step: str | None = None,
    status: str = "available",
    provider_payload: Mapping[str, object] | None = None,
) -> LanguageMaterializationOwnershipReceipt:
    receipt_path = _ownership_receipt_path(request=request, path=path)
    return LanguageMaterializationOwnershipReceipt(
        producer_provider_key=_META_PROVIDER_KEY,
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        output_key=output_key,
        artifact_key=_receipt_artifact_key(
            language=request.target_language_plugin_id,
            output_key=output_key,
            path=receipt_path,
            package_name=package_name or request.package_name,
        ),
        artifact_family=META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        artifact_role=artifact_role,
        output_kind=output_kind,
        target_language_plugin_id=request.target_language_plugin_id,
        status=status,
        producer_step=producer_step
        or (generated_file.producer_step if generated_file is not None else None),
        package_name=package_name or request.package_name,
        package_output_key=package_output_key,
        required_for=required_for,
        path=receipt_path,
        digest=generated_file.sha256 if generated_file is not None else None,
        size_bytes=generated_file.size_bytes if generated_file is not None else None,
        source_code_package_id=request.source_code_package_id,
        object_config_graph_package_id=request.object_config_graph_package_id,
        object_config_graph_commit_id=request.object_config_graph_commit_id,
        source_graph_ref=source_graph_hash,
        runtime_graph_ref=runtime_graph_hash,
        language_graph_ref=language_graph_hash,
        provider_payload=dict(provider_payload or {}),
    )


def _ownership_receipt_path(
    *,
    request: LanguagePluginMaterializationRequest,
    path: Path | None,
) -> Path | None:
    if path is None or path.is_absolute() or request.output_root is None:
        return path
    return request.output_root.resolve() / path


def _declared_output_receipt_status(
    output: LanguageMaterializationPluginDeclaredOutput,
) -> str:
    if output.generated_file_refs:
        return "available"
    return "missing" if output.required else "optional"


def _receipt_artifact_key(
    *,
    language: CodeLanguage,
    output_key: str,
    path: Path | None = None,
    package_name: str | None = None,
) -> str:
    parts = [language.value, output_key]
    if package_name:
        parts.append(package_name)
    if path is not None:
        parts.append(path.as_posix())
    return ":".join(parts)


def _produced_file_receipt_path(
    *,
    output_root: Path,
    produced_file: MetaLanguageDeclaredOutputProducedFile,
) -> Path:
    path = produced_file.path
    return path if path.is_absolute() else output_root.resolve() / path


def _produced_file_payload_bytes(
    produced_file: MetaLanguageDeclaredOutputProducedFile,
) -> bytes | None:
    if produced_file.content_bytes is not None:
        return produced_file.content_bytes
    if produced_file.content_text is not None:
        return produced_file.content_text.encode("utf-8")
    path = produced_file.path
    if path.exists() and path.is_file():
        return path.read_bytes()
    return None


def _package_name_for_receipt_path(
    *,
    path: Path,
    destinations: tuple[MetaLanguageMaterializationDestination, ...],
    fallback: str | None,
) -> str | None:
    resolved = path.resolve()
    matches: list[MetaLanguageMaterializationDestination] = []
    for destination in destinations:
        try:
            _ = resolved.relative_to(destination.root.resolve())
        except ValueError:
            continue
        matches.append(destination)
    if not matches:
        return fallback
    destination = max(matches, key=lambda item: len(item.root.resolve().parts))
    return destination.package_name or fallback


def _sort_ownership_receipts(
    receipts: list[LanguageMaterializationOwnershipReceipt],
) -> tuple[LanguageMaterializationOwnershipReceipt, ...]:
    return tuple(
        sorted(
            receipts,
            key=lambda item: (
                item.output_key,
                item.artifact_key,
                item.path.as_posix() if item.path is not None else "",
            ),
        )
    )


def _resolve_plugin_declared_path_template(
    *,
    template: str,
    request: LanguagePluginMaterializationRequest,
) -> Path:
    import_root = request.import_root or request.package_name or ""
    value = template.format(
        import_root=import_root,
        package_name=request.package_name or "",
        language=request.target_language_plugin_id.value,
    )
    return Path(value)


def _build_manifest_snapshots(
    *,
    request: LanguagePluginMaterializationRequest,
    runtime_graph: ObjectConfigGraph,
    language_graph: ObjectConfigGraph,
    runtime_external_graphs: tuple[ObjectConfigGraph, ...],
    language_external_graphs: tuple[ObjectConfigGraph, ...],
    source_graph_hash: str | None,
    runtime_graph_hash: str | None,
    language_graph_hash: str | None,
    dependency_signature: str | None,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
    package_outputs: tuple[LanguageMaterializationPackageOutput, ...],
    artifact_outputs: tuple[LanguageMaterializationArtifactOutput, ...],
    plugin_declared_outputs: tuple[LanguageMaterializationPluginDeclaredOutput, ...],
    ownership_receipts: tuple[LanguageMaterializationOwnershipReceipt, ...],
    status: str,
) -> tuple[LanguageMaterializationManifestSnapshot, ...]:
    if (
        not generated_files
        and not package_outputs
        and not artifact_outputs
        and not plugin_declared_outputs
    ):
        return ()

    payload: dict[str, object] = {
        "schema": _META_LANGUAGE_MATERIALIZATION_MANIFEST_SNAPSHOT_SCHEMA,
        "provider_key": _META_PROVIDER_KEY,
        "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
        "producer_key": META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        "snapshot_key": _META_LANGUAGE_MATERIALIZATION_MANIFEST_SNAPSHOT_KEY,
        "status": status,
        "target_language_plugin_id": request.target_language_plugin_id.value,
        "renderer": {
            "profile": request.renderer_profile,
            "kind": request.renderer_kind,
        },
        "package_inputs": {
            "object_config_graph_package_id": _uuid_value(
                request.object_config_graph_package_id
            ),
            "object_config_graph_commit_id": _uuid_value(
                request.object_config_graph_commit_id
            ),
            "source_code_package_id": _uuid_value(request.source_code_package_id),
            "package_name": request.package_name,
            "import_root": request.import_root,
        },
        "profile_inputs": _canonical_value(request.profile_inputs),
        "import_root": request.import_root,
        "import_overrides": _sorted_mapping_pairs(request.import_overrides),
        "source_graph": _graph_ref_payload(
            request.source_graph,
            graph_hash=source_graph_hash,
        ),
        "runtime_graph": _graph_ref_payload(
            runtime_graph,
            graph_hash=runtime_graph_hash,
        ),
        "language_graph": _graph_ref_payload(
            language_graph,
            graph_hash=language_graph_hash,
        ),
        "external_runtime_graphs": [
            _graph_ref_payload(graph) for graph in _sort_graphs(runtime_external_graphs)
        ],
        "package_dependency_graphs": [
            _graph_ref_payload(graph)
            for graph in _sort_graphs(request.package_dependency_graphs)
        ],
        "language_external_graphs": [
            _graph_ref_payload(graph)
            for graph in _sort_graphs(language_external_graphs)
        ],
        "dependency_signature": dependency_signature,
        "generated_files": [
            _generated_file_payload(item)
            for item in sorted(
                generated_files,
                key=lambda item: (item.path.as_posix(), item.renderer_name or ""),
            )
        ],
        "package_outputs": [
            _package_output_payload(item)
            for item in sorted(package_outputs, key=lambda item: item.package_name)
        ],
        "artifact_outputs": [
            _artifact_output_payload(item)
            for item in sorted(
                artifact_outputs,
                key=lambda item: (
                    item.semantic_owner,
                    item.producer_key,
                    item.output_key,
                ),
            )
        ],
        "plugin_declared_outputs": [
            _plugin_declared_output_payload(item)
            for item in sorted(
                plugin_declared_outputs, key=lambda item: item.output_key
            )
        ],
        "ownership_receipts": [
            _ownership_receipt_payload(item)
            for item in sorted(
                ownership_receipts,
                key=lambda item: (item.output_key, item.artifact_key),
            )
        ],
    }
    digest = _stable_json_hash(payload)
    return (
        LanguageMaterializationManifestSnapshot(
            snapshot_key=_META_LANGUAGE_MATERIALIZATION_MANIFEST_SNAPSHOT_KEY,
            producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
            sha256=digest,
            payload=payload,
            source_graph_ref=source_graph_hash,
            runtime_graph_ref=runtime_graph_hash,
            language_graph_ref=language_graph_hash,
            dependency_signature=dependency_signature,
            required_for=_META_LANGUAGE_MATERIALIZATION_MANIFEST_REQUIRED_FOR,
            status="materialized" if status == "succeeded" else status,
        ),
    )


def _graph_ref_payload(
    graph: ObjectConfigGraph,
    *,
    graph_hash: str | None = None,
) -> dict[str, object]:
    return {
        "id": str(graph.id),
        "name": graph.name,
        "hash": graph_hash if graph_hash is not None else graph.hash,
        "fqn_prefix": graph.fqn_prefix,
        "language": graph.language.value,
    }


def _generated_file_payload(
    item: LanguageMaterializationGeneratedFile,
) -> dict[str, object]:
    return {
        "path": item.path.as_posix(),
        "output_kind": item.output_kind,
        "producer_step": item.producer_step,
        "sha256": item.sha256,
        "size_bytes": item.size_bytes,
        "source_graph_ref": item.source_graph_ref,
        "renderer_name": item.renderer_name,
    }


def _package_output_payload(
    item: LanguageMaterializationPackageOutput,
) -> dict[str, object]:
    return {
        "package_name": item.package_name,
        "import_root": item.import_root,
        "output_root": ".",
        "output_root_mode": "package_root",
        "generated_file_refs": sorted(
            path.as_posix() for path in item.generated_file_refs
        ),
        "deleted_file_refs": sorted(path.as_posix() for path in item.deleted_file_refs),
    }


def _artifact_output_payload(
    item: LanguageMaterializationArtifactOutput,
) -> dict[str, object]:
    return {
        "provider_key": item.provider_key,
        "semantic_owner": item.semantic_owner,
        "producer_key": item.producer_key,
        "output_key": item.output_key,
        "artifact_family": item.artifact_family,
        "artifact_role": item.artifact_role,
        "output_kind": item.output_kind,
        "package_output_key": item.package_output_key,
        "generated_file_refs": sorted(
            path.as_posix() for path in item.generated_file_refs
        ),
        "package_output_refs": sorted(item.package_output_refs),
        "required_for": sorted(item.required_for),
        "status": item.status,
        "provider_payload": _canonical_value(item.provider_payload),
    }


def _plugin_declared_output_payload(
    item: LanguageMaterializationPluginDeclaredOutput,
) -> dict[str, object]:
    return {
        "language": item.language.value,
        "output_key": item.output_key,
        "output_kind": item.output_kind,
        "artifact_role": item.artifact_role,
        "producer_step": item.producer_step,
        "path_templates": list(item.path_templates),
        "resolved_paths": sorted(path.as_posix() for path in item.resolved_paths),
        "generated_file_refs": sorted(
            path.as_posix() for path in item.generated_file_refs
        ),
        "required_for": sorted(item.required_for),
        "renderer_profiles": sorted(item.renderer_profiles),
        "renderer_kinds": sorted(item.renderer_kinds),
        "materialization_sources": sorted(item.materialization_sources),
        "required": item.required,
        "status": item.status,
        "provider_payload": _canonical_value(item.provider_payload),
    }


def _ownership_receipt_payload(
    item: LanguageMaterializationOwnershipReceipt,
) -> dict[str, object]:
    return item.as_payload()


def _sort_graphs(
    graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    return tuple(sorted(graphs, key=lambda graph: str(graph.id)))


def _sorted_mapping_pairs(mapping: Mapping[str, str]) -> list[dict[str, str]]:
    return [
        {"source": key, "target": value}
        for key, value in sorted(mapping.items(), key=lambda item: item[0])
    ]


def _uuid_value(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _canonical_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, CodeLanguage):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item_value)
            for key, item_value in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple | list):
        return [_canonical_value(item) for item in value]
    if isinstance(value, set | frozenset):
        return [_canonical_value(item) for item in sorted(value, key=str)]
    return str(value)


def _stable_json_hash(payload: Mapping[str, object]) -> str:
    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical_json.encode("utf-8")).hexdigest()


def _quality_gate_targets(
    *,
    output_root: Path | None,
    generated_files: tuple[LanguageMaterializationGeneratedFile, ...],
) -> tuple[Path, ...]:
    if output_root is None:
        raise ValueError("output_root is required when quality gates are requested.")
    root = output_root.resolve()
    paths: list[Path] = []
    for generated_file in generated_files:
        path = generated_file.path
        paths.append(path if path.is_absolute() else root / path)
    return tuple(paths)


def _quality_gate_step_from_result(
    result: CodeLanguageQualityGateRunResult,
) -> LanguageMaterializationStep:
    return LanguageMaterializationStep(
        name=f"quality_gate:{result.gate_id}",
        duration_s=result.duration_s,
        status=result.status,
        details={
            "command": result.command,
            "target_mode": result.target_mode,
            "target_count": result.target_count,
            "cwd": str(result.cwd) if result.cwd is not None else None,
            "returncode": result.returncode,
            "timed_out": result.timed_out,
            "stdout": _trim_tool_output(result.stdout),
            "stderr": _trim_tool_output(result.stderr),
        },
    )


def _quality_gate_warning(result: CodeLanguageQualityGateRunResult) -> str:
    message = _trim_tool_output(result.stderr or result.stdout).strip()
    suffix = f": {message}" if message else ""
    return f"quality gate {result.gate_id!r} {result.status}{suffix}"


def _trim_tool_output(value: str, *, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _dependency_signature(
    external_runtime_graphs: tuple[ObjectConfigGraph, ...],
    package_dependency_graphs: tuple[ObjectConfigGraph, ...],
) -> str | None:
    if not external_runtime_graphs and not package_dependency_graphs:
        return None
    parts = [
        f"runtime:{graph.id}:{graph.hash or ''}"
        for graph in sorted(external_runtime_graphs, key=lambda graph: str(graph.id))
    ] + [
        f"package:{graph.id}:{graph.hash or ''}"
        for graph in sorted(package_dependency_graphs, key=lambda graph: str(graph.id))
    ]
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


@contextmanager
def _record_language_materialization_subphase(
    request: LanguagePluginMaterializationRequest,
    subphase_name: str,
    *,
    detail_payload: Mapping[str, object] | None = None,
) -> Iterator[None]:
    started_at = perf_counter()
    _emit_language_materialization_subphase_progress(
        request=request,
        subphase_name=subphase_name,
        status="running",
        detail_payload=detail_payload,
    )
    try:
        yield
    except Exception as exc:
        _emit_language_materialization_subphase_progress(
            request=request,
            subphase_name=subphase_name,
            status="failed",
            started_at=started_at,
            error=str(exc),
            detail_payload={
                **dict(detail_payload or {}),
                "error_type": type(exc).__name__,
            },
        )
        raise
    else:
        _emit_language_materialization_subphase_progress(
            request=request,
            subphase_name=subphase_name,
            status="succeeded",
            started_at=started_at,
            detail_payload=detail_payload,
        )


def _emit_language_materialization_subphase_progress(
    *,
    request: LanguagePluginMaterializationRequest,
    subphase_name: str,
    status: str,
    started_at: float | None = None,
    duration_s: float | None = None,
    error: str | None = None,
    detail_payload: Mapping[str, object] | None = None,
) -> None:
    callback = request.progress_callback
    if callback is None:
        return
    detail = {"subphase_name": subphase_name}
    detail.update(dict(detail_payload or {}))
    payload: dict[str, object] = {
        "phase_name": "meta.language_target.subphase",
        "status": status,
        "detail_payload": detail,
    }
    if duration_s is not None:
        payload["duration_s"] = round(max(duration_s, 0.0), 6)
    elif started_at is not None and status != "running":
        payload["duration_s"] = round(max(perf_counter() - started_at, 0.0), 6)
    if error:
        payload["error"] = error
    try:
        callback(payload)
    except Exception:
        return


def _record_language_materialization_render_phase_timings(
    *,
    request: LanguagePluginMaterializationRequest,
    steps: list[LanguageMaterializationStep],
    renderer_phase_timings: Mapping[str, Mapping[str, float]],
) -> None:
    for renderer_name, phase_timings in sorted(renderer_phase_timings.items()):
        for phase_name, duration_s in sorted(phase_timings.items()):
            step_name = f"render.{renderer_name}.{phase_name}"
            details = {
                "renderer_name": renderer_name,
                "renderer_phase_name": phase_name,
            }
            _record_substep_duration(
                steps,
                step_name,
                duration_s=duration_s,
                parent_step="render",
                graph_role="all",
                details=details,
            )
            _emit_language_materialization_subphase_progress(
                request=request,
                subphase_name=step_name,
                status="succeeded",
                duration_s=duration_s,
                detail_payload=details,
            )


@contextmanager
def _record_step(
    steps: list[LanguageMaterializationStep],
    name: str,
) -> Iterator[None]:
    started_at = perf_counter()
    try:
        yield
    finally:
        steps.append(
            LanguageMaterializationStep(
                name=name,
                duration_s=round(perf_counter() - started_at, 6),
            )
        )


@contextmanager
def _record_substep(
    steps: list[LanguageMaterializationStep] | None,
    name: str,
    *,
    parent_step: str,
    graph_role: str,
    details: Mapping[str, object] | None = None,
) -> Iterator[None]:
    if steps is None:
        yield
        return
    started_at = perf_counter()
    try:
        yield
    finally:
        _record_substep_duration(
            steps,
            name,
            duration_s=round(perf_counter() - started_at, 6),
            parent_step=parent_step,
            graph_role=graph_role,
            details=details,
        )


def _record_substep_duration(
    steps: list[LanguageMaterializationStep] | None,
    name: str,
    *,
    duration_s: float,
    parent_step: str,
    graph_role: str,
    details: Mapping[str, object] | None = None,
) -> None:
    if steps is None:
        return
    step_details: dict[str, object] = {
        "timing_scope": "substep",
        "timing_parent_step": parent_step,
        "graph_role": graph_role,
    }
    if details:
        step_details.update(details)
    steps.append(
        LanguageMaterializationStep(
            name=name,
            duration_s=duration_s,
            details=step_details,
        )
    )


__all__ = [
    "GraphMaterializationRuntimeBatchRequest",
    "GraphMaterializationRuntimeBatchResult",
    "GraphMaterializationStage",
    "GraphMaterializationTransformRequest",
    "GraphMaterializationTransformResult",
    "GraphMaterializationTransformService",
    "LanguageMaterializationGeneratedFile",
    "LanguageMaterializationArtifactOutput",
    "LanguageMaterializationManifestSnapshot",
    "LanguageMaterializationOwnershipReceipt",
    "LanguageMaterializationPackageOutput",
    "LanguageMaterializationPluginDeclaredOutput",
    "LanguageMaterializationStep",
    "LanguagePluginMaterializationRequest",
    "LanguagePluginMaterializationResult",
    "LanguagePluginMaterializationService",
    "RuntimeToLanguageClosureLoweringRequest",
    "RuntimeToLanguageClosureLoweringResult",
    "RuntimeToLanguageClosureLoweringService",
    "RuntimeToLanguageLoweringCache",
    "materialize_object_config_graph_via_language_plugin",
]
