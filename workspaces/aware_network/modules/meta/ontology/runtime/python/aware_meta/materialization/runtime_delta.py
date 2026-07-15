from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import cast
from uuid import UUID

from aware_code.builder import build_code_from_content
from aware_code_ontology.code.code_section import CodeSection
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta.manifest.spec import AwarePackageKind, AwareTomlNamespaceMappingSpec
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.manifest.namespace_match import namespace_for_source_path
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.runtime_derivation import (
    derive_runtime_object_config_graph,
)
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_instruction import (
    FunctionImplInstruction,
)
from aware_meta_ontology.function.function_impl_instruction_construct_assignment import (
    FunctionImplInstructionConstructAssignment,
)
from aware_meta_ontology.function.function_impl_instruction_require_operand import (
    FunctionImplInstructionRequireOperand,
)
from aware_meta_ontology.function.function_impl_value_source import (
    FunctionImplValueSource,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)


META_OCG_RUNTIME_DELTA_TRANSFORM_CONTRACT_VERSION = (
    "aware.meta.ocg.runtime-delta-transform.v1"
)
_STALE_RUNTIME_DELTA_BASELINE_OBJECT_KINDS = {
    "attribute",
    "class",
    "function_impl",
    "function",
    "relationship",
}


@dataclass(frozen=True, slots=True)
class MetaOcgRuntimeDeltaPathEvidence:
    relative_path: str
    kind: str
    language: str | None
    path_role: str | None
    is_structural: bool | None
    has_content_text: bool
    has_content_plan: bool
    content_text_size_bytes: int | None = None

    def evidence_payload(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "kind": self.kind,
            "language": self.language,
            "path_role": self.path_role,
            "is_structural": self.is_structural,
            "has_content_text": self.has_content_text,
            "has_content_plan": self.has_content_plan,
            "content_text_size_bytes": self.content_text_size_bytes,
        }


@dataclass(frozen=True, slots=True)
class MetaOcgRuntimeDeltaTransformRequest:
    code_package_delta: CodePackageDelta | None
    current_delta_fingerprint: str
    namespace_mappings: Sequence[AwareTomlNamespaceMappingSpec] = ()
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]] = field(
        default_factory=dict
    )
    baseline_branch_id: str | None = None
    baseline_projection_name: str | None = None
    baseline_projection_hash: str | None = None
    baseline_semantic_package_id: str | None = None
    baseline_semantic_object_instance_graph_commit_id: str | None = None
    baseline_semantic_root_object_instance_graph_commit_id: str | None = None
    changed_source_files: Sequence[str] = ()
    analysis_source_files: Sequence[str] = ()
    allow_full_rebuild_oracle: bool = False


@dataclass(frozen=True, slots=True)
class MetaOcgRuntimeDeltaTransformResult:
    status: str
    reason: str
    current_delta_fingerprint: str
    namespace_mapping_count: int = 0
    path_evidence: tuple[MetaOcgRuntimeDeltaPathEvidence, ...] = ()
    blockers: tuple[str, ...] = ()
    baseline_semantic_object_index_count: int = 0
    changed_runtime_source_refs: tuple[str, ...] = ()
    deleted_runtime_source_refs: tuple[str, ...] = ()
    current_runtime_semantic_object_index: Mapping[
        str, Mapping[str, object]
    ] = field(default_factory=dict)
    source_ocg_delta_count: int = 0
    runtime_ocg_delta_count: int = 0
    full_rebuild_oracle_used: bool = False

    @property
    def available(self) -> bool:
        return self.status == "runtime_delta_transform_ready"

    @property
    def blocked(self) -> bool:
        return not self.available

    def evidence_payload(self) -> dict[str, object]:
        current_index = {
            str(key): dict(value)
            for key, value in sorted(
                self.current_runtime_semantic_object_index.items()
            )
        }
        return {
            "transform_kind": "meta_ocg_runtime_delta_transform",
            "contract_version": META_OCG_RUNTIME_DELTA_TRANSFORM_CONTRACT_VERSION,
            "status": self.status,
            "reason": self.reason,
            "current_delta_fingerprint": self.current_delta_fingerprint,
            "namespace_mapping_count": self.namespace_mapping_count,
            "path_count": len(self.path_evidence),
            "path_evidence": tuple(
                path.evidence_payload() for path in self.path_evidence
            ),
            "blocker_count": len(self.blockers),
            "blockers": self.blockers,
            "baseline_semantic_object_index_count": (
                self.baseline_semantic_object_index_count
            ),
            "changed_runtime_source_refs": self.changed_runtime_source_refs,
            "deleted_runtime_source_refs": self.deleted_runtime_source_refs,
            "current_runtime_semantic_object_index_available": bool(current_index),
            "current_runtime_semantic_object_index_count": len(current_index),
            "current_runtime_semantic_object_index_keys": tuple(
                sorted(current_index)
            ),
            "current_runtime_semantic_object_index": current_index,
            "source_ocg_delta_count": self.source_ocg_delta_count,
            "runtime_ocg_delta_count": self.runtime_ocg_delta_count,
            "available": self.available,
            "blocked": self.blocked,
            "full_rebuild_oracle_used": self.full_rebuild_oracle_used,
            "would_execute": False,
            "would_persist": False,
            "did_persist": False,
            "execution_wired": False,
            "production_execution_wired": False,
        }


def build_meta_ocg_runtime_delta_transform(
    *,
    request: MetaOcgRuntimeDeltaTransformRequest,
) -> MetaOcgRuntimeDeltaTransformResult:
    delta = request.code_package_delta
    if delta is None:
        return _blocked_result(
            request=request,
            reason="meta_ocg_runtime_delta_requires_code_package_delta",
            blockers=("code_package_delta_missing",),
        )

    path_evidence = _path_evidence(delta=delta)
    if not path_evidence:
        return _blocked_result(
            request=request,
            reason="meta_ocg_runtime_delta_requires_code_package_delta_paths",
            path_evidence=path_evidence,
            blockers=("code_package_delta_paths_empty",),
        )

    if not request.baseline_semantic_object_index:
        return _blocked_result(
            request=request,
            reason="meta_ocg_runtime_delta_requires_baseline_semantic_object_index",
            path_evidence=path_evidence,
            blockers=("baseline_semantic_object_index_missing",),
        )

    missing_content_paths = tuple(
        path.relative_path
        for path in delta.paths
        if path.kind in (CodePackageDeltaKind.create, CodePackageDeltaKind.update)
        and path.content_text is None
        and path.content_plan is None
    )
    if missing_content_paths:
        return _blocked_result(
            request=request,
            reason="meta_ocg_runtime_delta_requires_content_backed_code_package_delta",
            path_evidence=path_evidence,
            blockers=tuple(
                f"path_content_missing:{path}" for path in missing_content_paths
            ),
        )

    runtime_index = _runtime_semantic_object_index_from_delta(
        request=request,
        delta=delta,
    )
    if runtime_index.blockers:
        return _blocked_result(
            request=request,
            reason=runtime_index.reason,
            path_evidence=path_evidence,
            blockers=runtime_index.blockers,
        )

    return MetaOcgRuntimeDeltaTransformResult(
        status="runtime_delta_transform_ready",
        reason="meta_ocg_runtime_delta_transform_ready",
        current_delta_fingerprint=request.current_delta_fingerprint,
        namespace_mapping_count=len(request.namespace_mappings),
        path_evidence=path_evidence,
        baseline_semantic_object_index_count=len(
            request.baseline_semantic_object_index
        ),
        changed_runtime_source_refs=runtime_index.changed_runtime_source_refs,
        deleted_runtime_source_refs=runtime_index.deleted_runtime_source_refs,
        current_runtime_semantic_object_index=runtime_index.entries,
        source_ocg_delta_count=runtime_index.source_ocg_delta_count,
        runtime_ocg_delta_count=runtime_index.runtime_ocg_delta_count,
    )


def build_meta_ocg_runtime_semantic_object_index(
    *,
    package_name: str | None,
    runtime_graph: ObjectConfigGraph,
    source_paths: Sequence[str] = (),
    source_path_by_code_id: Mapping[UUID, str] | None = None,
) -> Mapping[str, Mapping[str, object]]:
    """Build the canonical semantic-object index used by Meta OCG deltas."""

    return _runtime_semantic_object_index(
        package_name=package_name,
        runtime_graph=runtime_graph,
        source_paths=_clean_source_paths(source_paths),
        source_path_by_code_id=source_path_by_code_id or {},
    )


def build_meta_ocg_runtime_semantic_object_index_from_payload(
    *,
    package_name: str | None,
    object_config_graph_payload: Mapping[str, object],
    source_paths: Sequence[str] = (),
    source_path_by_code_id: Mapping[UUID, str] | None = None,
    derive_runtime_graph_from_payload: bool = False,
    allow_payload_graph_on_derivation_failure: bool = True,
) -> Mapping[str, Mapping[str, object]]:
    runtime_graph = ObjectConfigGraph.model_validate(
        dict(object_config_graph_payload)
    )
    if derive_runtime_graph_from_payload:
        try:
            runtime_graph = derive_runtime_object_config_graph(
                runtime_graph,
                external_runtime_graphs=(),
                include_projection_graphs=True,
            ).runtime_graph
        except Exception:
            if not allow_payload_graph_on_derivation_failure:
                raise
    return build_meta_ocg_runtime_semantic_object_index(
        package_name=package_name,
        runtime_graph=runtime_graph,
        source_paths=source_paths,
        source_path_by_code_id=source_path_by_code_id,
    )


@dataclass(frozen=True, slots=True)
class _RuntimeIndexBuildResult:
    reason: str
    blockers: tuple[str, ...] = ()
    changed_runtime_source_refs: tuple[str, ...] = ()
    deleted_runtime_source_refs: tuple[str, ...] = ()
    entries: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    source_ocg_delta_count: int = 0
    runtime_ocg_delta_count: int = 0


def _runtime_semantic_object_index_from_delta(
    *,
    request: MetaOcgRuntimeDeltaTransformRequest,
    delta: CodePackageDelta,
) -> _RuntimeIndexBuildResult:
    fqn_prefix = _baseline_fqn_prefix(
        baseline_semantic_object_index=request.baseline_semantic_object_index,
    )
    if fqn_prefix is None:
        return _runtime_index_blocked(
            reason="meta_ocg_runtime_delta_requires_baseline_graph_identity",
            blockers=("baseline_graph_semantic_key_missing",),
        )

    changed_runtime_source_refs = _aware_delta_source_refs(delta=delta)
    deleted_runtime_source_refs = _aware_delta_source_refs(
        delta=delta,
        kinds=(CodePackageDeltaKind.delete,),
    )
    if deleted_runtime_source_refs and not _baseline_has_stale_candidate_for_source_refs(
        baseline_semantic_object_index=request.baseline_semantic_object_index,
        source_refs=deleted_runtime_source_refs,
    ):
        return _runtime_index_blocked(
            reason="meta_ocg_runtime_delta_delete_requires_baseline_source_refs",
            blockers=tuple(
                "baseline_source_refs_missing_for_delete_path:"
                f"{source_ref}"
                for source_ref in deleted_runtime_source_refs
            ),
        )
    delta_paths = _content_text_aware_delta_paths(delta=delta)
    if not delta_paths:
        if deleted_runtime_source_refs:
            return _RuntimeIndexBuildResult(
                reason="meta_ocg_runtime_delta_delete_stale_scope_ready",
                changed_runtime_source_refs=changed_runtime_source_refs,
                deleted_runtime_source_refs=deleted_runtime_source_refs,
            )
        return _runtime_index_blocked(
            reason="meta_ocg_runtime_delta_requires_aware_source_delta_paths",
            blockers=("aware_source_delta_paths_missing",),
        )

    try:
        parsed_sources = _parse_delta_sources(delta=delta, delta_paths=delta_paths)
        if not parsed_sources:
            return _runtime_index_blocked(
                reason="meta_ocg_runtime_delta_requires_parseable_aware_sources",
                blockers=("parseable_aware_sources_missing",),
            )
        source_paths = tuple(path for path, _code in parsed_sources)
        namespace_by_code_id = _build_namespace_by_code_id(
            source_paths=source_paths,
            parsed_sources=parsed_sources,
            fqn_prefix=fqn_prefix,
            namespace_mappings=tuple(request.namespace_mappings),
        )
        build_result = build_object_config_graph_from_code(
            name=fqn_prefix,
            description=f"Runtime delta fragment for {delta.package_name or fqn_prefix}",
            fqn_prefix=fqn_prefix,
            file_codes=list(parsed_sources),
            namespace_by_code_id=namespace_by_code_id,
            package_kind=AwarePackageKind.ontology,
            external_graphs=[],
        )
        runtime_derivation = derive_runtime_object_config_graph(
            build_result.graph,
            external_runtime_graphs=(),
            include_projection_graphs=True,
        )
    except Exception as exc:
        return _runtime_index_blocked(
            reason="meta_ocg_runtime_delta_transform_failed",
            blockers=(f"runtime_delta_transform_error:{type(exc).__name__}:{exc}",),
        )

    unsupported_blockers = _unsupported_runtime_graph_blockers(
        runtime_graph=runtime_derivation.runtime_graph,
    )
    if unsupported_blockers:
        return _runtime_index_blocked(
            reason="meta_ocg_runtime_delta_transform_unsupported_semantic_shape",
            blockers=unsupported_blockers,
        )

    source_path_by_code_id = {
        code.id: source_path
        for source_path, code in parsed_sources
        if code.id is not None
    }
    entries = _runtime_semantic_object_index(
        package_name=delta.package_name,
        runtime_graph=runtime_derivation.runtime_graph,
        source_paths=source_paths,
        source_path_by_code_id=source_path_by_code_id,
    )
    return _RuntimeIndexBuildResult(
        reason="meta_ocg_runtime_delta_transform_ready",
        changed_runtime_source_refs=changed_runtime_source_refs,
        deleted_runtime_source_refs=deleted_runtime_source_refs,
        entries=entries,
        source_ocg_delta_count=len(build_result.graph.object_config_graph_nodes),
        runtime_ocg_delta_count=len(entries),
    )


def _runtime_index_blocked(
    *,
    reason: str,
    blockers: tuple[str, ...],
) -> _RuntimeIndexBuildResult:
    return _RuntimeIndexBuildResult(reason=reason, blockers=blockers)


def _build_namespace_by_code_id(
    *,
    source_paths: Sequence[str],
    parsed_sources: Sequence[tuple[str, Code]],
    fqn_prefix: str,
    namespace_mappings: Sequence[AwareTomlNamespaceMappingSpec],
) -> dict[UUID, NamespacePath]:
    namespace_by_source_path = {
        source_path: namespace_for_source_path(
            source_path=source_path,
            namespace_mappings=tuple(namespace_mappings),
        )
        for source_path in source_paths
    }
    namespace_by_code_id: dict[UUID, NamespacePath] = {}
    for source_path, code in parsed_sources:
        namespace = namespace_by_source_path.get(source_path)
        if namespace is None or code.id is None:
            continue
        namespace_by_code_id[code.id] = NamespacePath(
            package=fqn_prefix,
            namespace=namespace,
        )
    return namespace_by_code_id


def _blocked_result(
    *,
    request: MetaOcgRuntimeDeltaTransformRequest,
    reason: str,
    blockers: tuple[str, ...],
    path_evidence: tuple[MetaOcgRuntimeDeltaPathEvidence, ...] = (),
) -> MetaOcgRuntimeDeltaTransformResult:
    return MetaOcgRuntimeDeltaTransformResult(
        status="runtime_delta_transform_blocked",
        reason=reason,
        current_delta_fingerprint=request.current_delta_fingerprint,
        namespace_mapping_count=len(request.namespace_mappings),
        path_evidence=path_evidence,
        blockers=blockers,
        baseline_semantic_object_index_count=len(
            request.baseline_semantic_object_index
        ),
    )


def _path_evidence(
    *,
    delta: CodePackageDelta,
) -> tuple[MetaOcgRuntimeDeltaPathEvidence, ...]:
    return tuple(
        MetaOcgRuntimeDeltaPathEvidence(
            relative_path=path.relative_path,
            kind=path.kind.value,
            language=path.language.value if path.language is not None else None,
            path_role=path.path_role.value if path.path_role is not None else None,
            is_structural=path.is_structural,
            has_content_text=path.content_text is not None,
            has_content_plan=path.content_plan is not None,
            content_text_size_bytes=(
                len(path.content_text.encode("utf-8"))
                if path.content_text is not None
                else None
            ),
        )
        for path in delta.paths
    )


def _baseline_fqn_prefix(
    *,
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]],
) -> str | None:
    for semantic_key in sorted(baseline_semantic_object_index):
        if semantic_key.startswith("ocg:") and "/node:" not in semantic_key:
            return semantic_key.removeprefix("ocg:")
    for entry in baseline_semantic_object_index.values():
        fqn_prefix = _optional_text(entry.get("fqn_prefix"))
        if fqn_prefix is not None:
            return fqn_prefix
        graph_semantic_key = _optional_text(entry.get("graph_semantic_key"))
        if graph_semantic_key is not None and graph_semantic_key.startswith("ocg:"):
            return graph_semantic_key.removeprefix("ocg:")
    return None


def _content_text_aware_delta_paths(
    *,
    delta: CodePackageDelta,
) -> tuple[CodePackageDeltaPath, ...]:
    paths: list[CodePackageDeltaPath] = []
    for path in delta.paths:
        normalized_path = path.relative_path.strip()
        language = path.language
        if language is not None and language is not CodeLanguage.aware:
            continue
        if not normalized_path.endswith(".aware"):
            continue
        if path.content_text is None:
            continue
        paths.append(path)
    return tuple(paths)


def _aware_delta_source_refs(
    *,
    delta: CodePackageDelta,
    kinds: tuple[CodePackageDeltaKind, ...] | None = None,
) -> tuple[str, ...]:
    refs: list[str] = []
    for path in delta.paths:
        if kinds is not None and path.kind not in kinds:
            continue
        normalized_path = path.relative_path.strip()
        language = path.language
        if language is not None and language is not CodeLanguage.aware:
            continue
        if not normalized_path.endswith(".aware"):
            continue
        refs.append(_delta_source_path(delta=delta, delta_path=path))
    return tuple(sorted(dict.fromkeys(refs)))


def _baseline_has_stale_candidate_for_source_refs(
    *,
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]],
    source_refs: tuple[str, ...],
) -> bool:
    source_ref_set = set(source_refs)
    if not source_ref_set:
        return False
    for entry in baseline_semantic_object_index.values():
        object_kind = _optional_text(
            entry.get("object_kind")
            or entry.get("semantic_object_kind")
            or entry.get("ontology_subject_kind")
            or entry.get("kind")
        )
        if object_kind not in _STALE_RUNTIME_DELTA_BASELINE_OBJECT_KINDS:
            continue
        if source_ref_set.intersection(_tuple_text(entry.get("source_refs"))):
            return True
    return False


def _parse_delta_sources(
    *,
    delta: CodePackageDelta,
    delta_paths: tuple[CodePackageDeltaPath, ...],
) -> tuple[tuple[str, Code], ...]:
    setup_code_plugins()
    section_index = CodeSectionBuilderIndex()
    symbol_table = CodeSymbolTable()
    parsed: list[tuple[str, Code]] = []
    seen: set[str] = set()
    for delta_path in delta_paths:
        content = delta_path.content_text
        if content is None:
            continue
        source_path = _delta_source_path(delta=delta, delta_path=delta_path)
        if source_path in seen:
            continue
        seen.add(source_path)
        parsed.append(
            (
                source_path,
                build_code_from_content(
                    sections_index=section_index,
                    content=content,
                    code_key=source_path,
                    language=CodeLanguage.aware,
                    symbol_table=symbol_table,
                ),
            )
        )
    return tuple(sorted(parsed, key=lambda item: item[0]))


def _delta_source_path(
    *,
    delta: CodePackageDelta,
    delta_path: CodePackageDeltaPath,
) -> str:
    relative_path = delta_path.relative_path.strip().strip("/")
    for sources_root in _delta_source_root_prefixes(delta=delta):
        prefix = f"{sources_root}/"
        if relative_path.startswith(prefix):
            return relative_path.removeprefix(prefix)
    return relative_path


def _delta_source_root_prefixes(*, delta: CodePackageDelta) -> tuple[str, ...]:
    sources_root = (delta.sources_root or "aware").strip().strip("/")
    prefixes: list[str] = []
    if sources_root:
        prefixes.append(sources_root)
        parts = sources_root.split("/")
        for marker in ("structure/aware", "aware"):
            if sources_root == marker or sources_root.endswith(f"/{marker}"):
                prefixes.append(marker)
        if parts and parts[-1] != sources_root:
            prefixes.append(parts[-1])
    return tuple(dict.fromkeys(prefix for prefix in prefixes if prefix))


def _clean_source_paths(source_paths: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            text
            for raw_path in source_paths
            for text in (str(raw_path).strip().strip("/"),)
            if text
        )
    )


def _unsupported_runtime_graph_blockers(
    *,
    runtime_graph: ObjectConfigGraph,
) -> tuple[str, ...]:
    blockers: list[str] = []
    for node in sorted(runtime_graph.object_config_graph_nodes, key=_node_sort_key):
        if node.type not in (
            ObjectConfigGraphNodeType.class_,
            ObjectConfigGraphNodeType.relationship,
        ):
            blockers.append(f"unsupported_node_type:{node.type.value}:{node.node_key}")
            continue
        if node.type is ObjectConfigGraphNodeType.relationship:
            if node.class_config_relationship is None:
                blockers.append(f"relationship_node_missing_relationship:{node.node_key}")
            continue
        class_config = node.class_config
        if class_config is None:
            blockers.append(f"class_node_missing_class_config:{node.node_key}")
            continue
        for attribute_edge in class_config.class_config_attribute_configs:
            attribute_config = attribute_edge.attribute_config
            blockers.extend(
                _unsupported_attribute_descriptor_blockers(
                    node_key=node.node_key,
                    attribute_name=attribute_config.name,
                    descriptor=attribute_config.type_descriptor,
                )
            )
    return tuple(dict.fromkeys(blockers))


def _unsupported_attribute_descriptor_blockers(
    *,
    node_key: str,
    attribute_name: str,
    descriptor: AttributeTypeDescriptor,
) -> tuple[str, ...]:
    blockers: list[str] = []
    descriptor_stack = (descriptor,)
    while descriptor_stack:
        current_descriptor = descriptor_stack[0]
        descriptor_stack = descriptor_stack[1:]
        if current_descriptor.kind not in {
            AttributeTypeDescriptorKind.primitive,
            AttributeTypeDescriptorKind.class_,
            AttributeTypeDescriptorKind.collection,
        }:
            blockers.append(
                "unsupported_attribute_type:"
                f"{node_key}/{attribute_name}:{current_descriptor.kind.value}"
            )
            continue
        if (
            current_descriptor.kind is AttributeTypeDescriptorKind.primitive
            and current_descriptor.collection_kind
            not in (None, AttributeCollectionType.single)
        ):
            blockers.append(
                "unsupported_attribute_collection:"
                f"{node_key}/{attribute_name}:"
                f"{current_descriptor.collection_kind.value}"
            )
        descriptor_stack = tuple(
            child_link.child for child_link in current_descriptor.child_links
        ) + descriptor_stack
    return tuple(blockers)


def _runtime_semantic_object_index(
    *,
    package_name: str | None,
    runtime_graph: ObjectConfigGraph,
    source_paths: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    graph_semantic_key = f"ocg:{runtime_graph.fqn_prefix}"
    class_fqn_by_id = _class_fqn_by_id(runtime_graph=runtime_graph)
    if package_name is not None:
        package_key = f"ocg_package:{package_name}"
        entries[package_key] = _entry_with_fingerprint(
            {
                "semantic_key": package_key,
                "object_kind": "object_config_graph_package",
                "ontology_subject_kind": "object_config_graph_package",
                "semantic_subject_type": "aware_meta.ObjectConfigGraphPackage",
                "verb": "upsert",
                "package_name": package_name,
                "fqn_prefix": runtime_graph.fqn_prefix,
                "source_refs": ("aware.toml",),
                "source_delta_key": (
                    "aware_meta.runtime_delta.object_config_graph_package:"
                    f"{package_key}"
                ),
            }
        )
    graph_entry = {
        "semantic_key": graph_semantic_key,
        "object_kind": "object_config_graph",
        "ontology_subject_kind": "object_config_graph",
        "semantic_subject_type": "aware_meta.ObjectConfigGraph",
        "verb": "upsert",
        "name": runtime_graph.name,
        "fqn_prefix": runtime_graph.fqn_prefix,
        "language": runtime_graph.language.value,
        "hash": runtime_graph.hash,
        "node_count": len(runtime_graph.object_config_graph_nodes),
        "source_refs": source_paths,
        "source_delta_key": (
            "aware_meta.runtime_delta.object_config_graph:"
            f"{graph_semantic_key}"
        ),
    }
    entries[graph_semantic_key] = _entry_with_fingerprint(
        graph_entry,
        fingerprint_payload={
            key: value
            for key, value in graph_entry.items()
            if key not in {"hash", "name", "node_count", "source_refs"}
        },
    )
    for node in sorted(runtime_graph.object_config_graph_nodes, key=_node_sort_key):
        if node.type is ObjectConfigGraphNodeType.relationship:
            if node.class_config_relationship is None:
                continue
            relationship_key = _node_semantic_key(
                runtime_graph=runtime_graph,
                node=node,
                class_fqn_by_id=class_fqn_by_id,
            )
            relationship_node_key = relationship_key.removeprefix(
                f"ocg:{runtime_graph.fqn_prefix}/node:"
            )
            relationship_source_refs = _source_refs_for_relationship(
                relationship=node.class_config_relationship,
                fallback_source_refs=source_paths,
                source_path_by_code_id=source_path_by_code_id,
            )
            entries[relationship_key] = _entry_with_fingerprint(
                {
                    "semantic_key": relationship_key,
                    "object_kind": "relationship",
                    "ontology_subject_kind": "relationship",
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "verb": "upsert",
                    "graph_semantic_key": graph_semantic_key,
                    "node_id": str(node.id),
                    "node_key": relationship_node_key,
                    "node_type": node.type.value,
                    "entity_id": str(node.class_config_relationship.id),
                    "entity_name": node.class_config_relationship.relationship_key,
                    "relationship_key": (
                        node.class_config_relationship.relationship_key
                    ),
                    "relationship_type": (
                        node.class_config_relationship.relationship_type.value
                    ),
                    "source_class_config_id": str(
                        node.class_config_relationship.class_config_id
                    ),
                    "target_class_config_id": str(
                        node.class_config_relationship.target_class_config_id
                    ),
                    "relationship_signature": _relationship_signature(
                        relationship=node.class_config_relationship,
                    ),
                    "source_refs": relationship_source_refs,
                    "source_delta_key": (
                        "aware_meta.runtime_delta.class_config_relationship:"
                        f"{relationship_key}"
                    ),
                }
            )
            continue
        if node.type is not ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        node_semantic_key = _node_semantic_key(
            runtime_graph=runtime_graph,
            node=node,
            class_fqn_by_id=class_fqn_by_id,
        )
        node_source_refs = _source_refs_for_node(
            node=node,
            source_paths=source_paths,
            source_path_by_code_id=source_path_by_code_id,
        )
        class_signature = _class_signature(class_config=node.class_config)
        entries[node_semantic_key] = _entry_with_fingerprint(
            {
                "semantic_key": node_semantic_key,
                "object_kind": "class",
                "ontology_subject_kind": "class",
                "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                "verb": "upsert",
                "graph_semantic_key": graph_semantic_key,
                "node_id": str(node.id),
                "node_key": node.node_key,
                "node_type": node.type.value,
                "entity_id": str(node.class_config.id),
                "entity_name": node.class_config.name,
                "class_fqn": node.class_config.class_fqn,
                "name": node.class_config.name,
                "description": node.class_config.description,
                "is_base": node.class_config.is_base,
                "is_edge": node.class_config.is_edge,
                "value_mode": _enum_text(node.class_config.value_mode),
                "identity_mode": _enum_text(node.class_config.identity_mode),
                "class_signature": class_signature,
                "source_refs": node_source_refs,
                "source_delta_key": (
                    "aware_meta.runtime_delta.object_config_graph_node:"
                    f"{node_semantic_key}"
                ),
            }
        )
        for function_edge in sorted(
            node.class_config.class_config_function_configs,
            key=lambda item: (
                item.position,
                item.function_config.name,
            ),
        ):
            function_config = function_edge.function_config
            function_node_key = f"{function_config.owner_key}.{function_config.name}"
            function_key = f"{graph_semantic_key}/node:{function_node_key}"
            function_source_refs = _source_refs_for_function(
                function_config=function_config,
                fallback_source_refs=node_source_refs,
                source_path_by_code_id=source_path_by_code_id,
            )
            entries[function_key] = _entry_with_fingerprint(
                {
                    "semantic_key": function_key,
                    "object_kind": "function",
                    "ontology_subject_kind": "function",
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "verb": "upsert",
                    "graph_semantic_key": graph_semantic_key,
                    "parent_semantic_key": node_semantic_key,
                    "owner_semantic_key": node_semantic_key,
                    "node_type": "function",
                    "node_key": function_node_key,
                    "entity_id": str(function_config.id),
                    "entity_name": function_config.name,
                    "class_config_id": str(function_edge.class_config_id),
                    "class_config_function_config_id": str(function_edge.id),
                    "function_config_id": str(
                        function_edge.function_config_id or function_config.id
                    ),
                    "function_name": function_config.name,
                    "function_kind": function_config.kind.value,
                    "function_owner_key": function_config.owner_key,
                    "function_membership_semantic_key": (
                        f"{function_key}/membership:class_config"
                    ),
                    "function_membership_signature": (
                        _function_membership_signature(
                            function_edge=function_edge,
                        )
                    ),
                    "function_signature": _function_signature(
                        function_config=function_config,
                        function_edge_position=function_edge.position,
                    ),
                    "source_refs": function_source_refs,
                    "source_delta_key": (
                        "aware_meta.runtime_delta.function_config:"
                        f"{function_key}"
                    ),
                }
            )
            function_impl = function_config.function_impl
            if function_impl is not None:
                function_impl_key = _function_impl_semantic_key(
                    function_key=function_key,
                    function_impl=function_impl,
                )
                entries[function_impl_key] = _entry_with_fingerprint(
                    {
                        "semantic_key": function_impl_key,
                        "object_kind": "function_impl",
                        "ontology_subject_kind": "function_impl",
                        "semantic_subject_type": "aware_meta.FunctionImpl",
                        "verb": "upsert",
                        "graph_semantic_key": graph_semantic_key,
                        "parent_semantic_key": function_key,
                        "owner_semantic_key": node_semantic_key,
                        "function_semantic_key": function_key,
                        "function_owner_semantic_key": node_semantic_key,
                        "node_type": "function_impl",
                        "node_key": function_node_key,
                        "entity_id": str(function_impl.id),
                        "entity_name": function_impl.key,
                        "function_name": function_config.name,
                        "function_impl_key": function_impl.key,
                        "function_impl_kind": _enum_text(function_impl.kind),
                        "function_impl_signature": _function_impl_signature(
                            function_impl=function_impl,
                            function_config=function_config,
                        ),
                        "source_refs": function_source_refs,
                        "source_delta_key": (
                            "aware_meta.runtime_delta.function_impl:"
                            f"{function_impl_key}"
                        ),
                    }
                )
            for attribute_edge in sorted(
                function_config.function_config_attribute_configs,
                key=lambda item: (
                    item.type.value,
                    item.position,
                    item.name,
                ),
            ):
                attribute_config = attribute_edge.attribute_config
                attribute_key = (
                    f"{function_key}/attribute:"
                    f"{attribute_edge.type.value}:{attribute_edge.name}"
                )
                attribute_signature = _function_attribute_signature(
                    edge=attribute_edge,
                )
                attribute_membership_signature = (
                    _function_attribute_membership_signature(
                        attribute_edge=attribute_edge,
                    )
                )
                attribute_source_refs = _source_refs_for_attribute(
                    attribute_config=attribute_config,
                    fallback_source_refs=function_source_refs,
                    source_path_by_code_id=source_path_by_code_id,
                )
                entries[attribute_key] = _entry_with_fingerprint(
                    {
                        "semantic_key": attribute_key,
                        "object_kind": "attribute",
                        "ontology_subject_kind": "attribute",
                        "semantic_subject_type": "aware_meta.AttributeConfig",
                        "verb": "upsert",
                        "graph_semantic_key": graph_semantic_key,
                        "parent_semantic_key": function_key,
                        "owner_semantic_key": function_key,
                        "owner_object_id": str(function_config.id),
                        "attribute_name": attribute_edge.name,
                        "attribute_config_id": str(attribute_config.id),
                        "function_config_attribute_config_id": str(
                            attribute_edge.id
                        ),
                        "function_config_id": str(attribute_edge.function_config_id),
                        "function_attribute_type": attribute_edge.type.value,
                        "attribute_membership_semantic_key": (
                            f"{attribute_key}/membership:function_config"
                        ),
                        "attribute_membership_owner_kind": "function",
                        "attribute_membership_signature": (
                            attribute_membership_signature
                        ),
                        "entity_id": str(attribute_config.id),
                        "entity_name": attribute_config.name,
                        "attribute_signature": attribute_signature,
                        "source_refs": attribute_source_refs,
                        "source_delta_key": (
                            "aware_meta.runtime_delta.attribute_config:"
                            f"{attribute_key}"
                        ),
                    }
                )
        for attribute_edge in sorted(
            node.class_config.class_config_attribute_configs,
            key=lambda item: (
                item.position,
                item.attribute_config.name,
            ),
        ):
            attribute_config = attribute_edge.attribute_config
            attribute_key = f"{node_semantic_key}/attribute:{attribute_config.name}"
            attribute_signature = _attribute_signature(
                attribute_edge=attribute_edge,
            )
            attribute_source_refs = _source_refs_for_attribute(
                attribute_config=attribute_config,
                fallback_source_refs=node_source_refs,
                source_path_by_code_id=source_path_by_code_id,
            )
            entries[attribute_key] = _entry_with_fingerprint(
                {
                    "semantic_key": attribute_key,
                    "object_kind": "attribute",
                    "ontology_subject_kind": "attribute",
                    "semantic_subject_type": "aware_meta.AttributeConfig",
                    "verb": "upsert",
                    "graph_semantic_key": graph_semantic_key,
                    "parent_semantic_key": node_semantic_key,
                    "owner_semantic_key": node_semantic_key,
                    "owner_object_id": str(node.class_config.id),
                    "attribute_name": attribute_config.name,
                    "attribute_config_id": str(attribute_config.id),
                    "class_config_attribute_config_id": str(attribute_edge.id),
                    "class_config_id": str(attribute_edge.class_config_id),
                    "attribute_membership_semantic_key": (
                        f"{attribute_key}/membership:class_config"
                    ),
                    "attribute_membership_owner_kind": "class",
                    "attribute_membership_signature": (
                        _class_attribute_membership_signature(
                            attribute_edge=attribute_edge,
                        )
                    ),
                    "entity_id": str(attribute_config.id),
                    "entity_name": attribute_config.name,
                    "attribute_signature": attribute_signature,
                    "source_refs": attribute_source_refs,
                    "source_delta_key": (
                        "aware_meta.runtime_delta.attribute_config:"
                        f"{attribute_key}"
                    ),
                }
            )
    return dict(sorted(entries.items()))


def _node_sort_key(node: ObjectConfigGraphNode) -> tuple[str, str]:
    return node.type.value, node.node_key


def _class_fqn_by_id(
    *,
    runtime_graph: ObjectConfigGraph,
) -> dict[UUID, str]:
    values: dict[UUID, str] = {}
    for node in runtime_graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None:
            continue
        values[class_config.id] = class_config.class_fqn
    return values


def _node_semantic_key(
    *,
    runtime_graph: ObjectConfigGraph,
    node: ObjectConfigGraphNode,
    class_fqn_by_id: Mapping[UUID, str],
) -> str:
    if (
        node.type is ObjectConfigGraphNodeType.relationship
        and node.class_config_relationship is not None
    ):
        relationship = node.class_config_relationship
        source_class_fqn = class_fqn_by_id.get(relationship.class_config_id)
        target_class_fqn = class_fqn_by_id.get(relationship.target_class_config_id)
        if source_class_fqn is not None and target_class_fqn is not None:
            return (
                f"ocg:{runtime_graph.fqn_prefix}/node:"
                f"{source_class_fqn}:{relationship.relationship_key}:"
                f"{relationship.relationship_type.value}:{target_class_fqn}"
            )
    return f"ocg:{runtime_graph.fqn_prefix}/node:{node.node_key}"


def _source_refs_for_node(
    *,
    node: ObjectConfigGraphNode,
    source_paths: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
) -> tuple[str, ...]:
    code_section = None
    if node.class_config is not None:
        code_section_class = node.class_config.code_section_class
        code_section = (
            code_section_class.code_section if code_section_class is not None else None
        )
    return _source_refs_for_code_section(
        code_section=code_section,
        fallback_source_refs=source_paths,
        source_path_by_code_id=source_path_by_code_id,
    )


def _source_refs_for_attribute(
    *,
    attribute_config: AttributeConfig,
    fallback_source_refs: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
) -> tuple[str, ...]:
    code_section_attribute = attribute_config.code_section_attribute
    code_section = (
        code_section_attribute.code_section
        if code_section_attribute is not None
        else None
    )
    return _source_refs_for_code_section(
        code_section=code_section,
        fallback_source_refs=fallback_source_refs,
        source_path_by_code_id=source_path_by_code_id,
    )


def _source_refs_for_function(
    *,
    function_config: FunctionConfig,
    fallback_source_refs: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
) -> tuple[str, ...]:
    code_section_function = function_config.code_section_function
    code_section = (
        code_section_function.code_section
        if code_section_function is not None
        else None
    )
    return _source_refs_for_code_section(
        code_section=code_section,
        fallback_source_refs=fallback_source_refs,
        source_path_by_code_id=source_path_by_code_id,
    )


def _source_refs_for_relationship(
    *,
    relationship: ClassConfigRelationship,
    fallback_source_refs: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
) -> tuple[str, ...]:
    refs: list[str] = []
    for relationship_attribute in sorted(
        relationship.class_config_relationship_attributes,
        key=lambda item: (
            item.direction.value,
            item.role.value,
            str(item.attribute_config_id),
        ),
    ):
        attribute_config = relationship_attribute.attribute_config
        if attribute_config is None:
            continue
        refs.extend(
            _source_refs_for_attribute(
                attribute_config=attribute_config,
                fallback_source_refs=(),
                source_path_by_code_id=source_path_by_code_id,
            )
        )
    if refs:
        return tuple(sorted(dict.fromkeys(refs)))
    return fallback_source_refs


def _source_refs_for_code_section(
    *,
    code_section: CodeSection | None,
    fallback_source_refs: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
) -> tuple[str, ...]:
    source_path = (
        source_path_by_code_id.get(code_section.code_id)
        if code_section is not None
        else None
    )
    if source_path is not None:
        return (source_path,)
    return fallback_source_refs


def _attribute_signature(
    *,
    attribute_edge: ClassConfigAttributeConfig,
) -> dict[str, object]:
    attribute_config = attribute_edge.attribute_config
    descriptor = attribute_config.type_descriptor
    descriptor_signature = _attribute_descriptor_signature(descriptor=descriptor)
    return {
        "name": attribute_config.name,
        "type_descriptor": descriptor_signature,
        **descriptor_signature,
        "description": attribute_config.description,
        "default_value": attribute_config.default_value,
        "is_primary": attribute_config.is_primary,
        "is_public": attribute_config.is_public,
        "is_required": attribute_config.is_required,
        "is_unique": attribute_config.is_unique,
        "is_virtual": attribute_config.is_virtual,
        "exclude_serialization": attribute_config.exclude_serialization,
        "is_identity_key": attribute_edge.is_identity_key,
        "position": attribute_edge.position,
    }


def _class_attribute_membership_signature(
    *,
    attribute_edge: ClassConfigAttributeConfig,
) -> dict[str, object]:
    return {
        "owner_kind": "class",
        "class_config_id": str(attribute_edge.class_config_id),
        "attribute_config_id": str(
            attribute_edge.attribute_config_id or attribute_edge.attribute_config.id
        ),
        "position": attribute_edge.position,
        "is_identity_key": attribute_edge.is_identity_key,
    }


def _class_signature(
    *,
    class_config: ClassConfig,
) -> dict[str, object]:
    return {
        "class_fqn": class_config.class_fqn,
        "name": class_config.name,
        "description": class_config.description,
        "is_base": class_config.is_base,
        "is_edge": class_config.is_edge,
        "value_mode": _enum_text(class_config.value_mode),
        "identity_mode": _enum_text(class_config.identity_mode),
    }


def _function_signature(
    *,
    function_config: FunctionConfig,
    function_edge_position: int,
) -> dict[str, object]:
    return {
        "name": function_config.name,
        "owner_key": function_config.owner_key,
        "description": function_config.description,
        "verb": function_config.verb,
        "kind": function_config.kind.value,
        "is_async": function_config.is_async,
        "position": function_edge_position,
        "inputs": tuple(
            _function_attribute_signature(edge=attribute_edge)
            for attribute_edge in sorted(
                function_config.function_config_attribute_configs,
                key=lambda item: (
                    item.type.value,
                    item.position,
                    item.name,
                ),
            )
            if attribute_edge.type.value == "input"
        ),
        "outputs": tuple(
            _function_attribute_signature(edge=attribute_edge)
            for attribute_edge in sorted(
                function_config.function_config_attribute_configs,
                key=lambda item: (
                    item.type.value,
                    item.position,
                    item.name,
                ),
            )
            if attribute_edge.type.value == "output"
        ),
    }


def _function_membership_signature(
    *,
    function_edge: ClassConfigFunctionConfig,
) -> dict[str, object]:
    return {
        "class_config_id": str(function_edge.class_config_id),
        "function_config_id": str(
            function_edge.function_config_id or function_edge.function_config.id
        ),
        "is_public": function_edge.is_public,
        "is_constructor": function_edge.is_constructor,
        "position": function_edge.position,
    }


def _function_impl_semantic_key(
    *,
    function_key: str,
    function_impl: FunctionImpl,
) -> str:
    impl_key = _optional_text(function_impl.key) or "default"
    return f"{function_key}/function_impl:{impl_key}"


def _function_impl_signature(
    *,
    function_impl: FunctionImpl,
    function_config: FunctionConfig,
) -> dict[str, object]:
    instruction_signatures = tuple(
        _function_impl_instruction_signature(instruction=instruction)
        for instruction in sorted(
            function_impl.instructions,
            key=_function_impl_instruction_sort_key,
        )
    )
    instruction_summaries = tuple(
        _function_impl_instruction_summary(signature=signature)
        for signature in instruction_signatures
    )
    return {
        "key": function_impl.key,
        "kind": _enum_text(function_impl.kind),
        "function_name": function_config.name,
        "function_owner_key": function_config.owner_key,
        "instruction_count": len(instruction_signatures),
        "instruction_summaries": instruction_summaries,
        "instructions": instruction_signatures,
    }


def _function_impl_instruction_sort_key(
    instruction: FunctionImplInstruction,
) -> tuple[int, str]:
    return (instruction.sequence, str(instruction.id))


def _function_impl_instruction_signature(
    *,
    instruction: FunctionImplInstruction,
) -> dict[str, object]:
    signature: dict[str, object] = {
        "type": _enum_text(instruction.type),
        "sequence": instruction.sequence,
        "value_sources": tuple(
            _function_impl_value_source_signature(value_source=value_source)
            for value_source in sorted(
                instruction.value_sources,
                key=_function_impl_value_source_sort_key,
            )
        ),
    }
    instruction_let = instruction.instruction_let
    if instruction_let is not None:
        signature["let"] = {
            "name": instruction_let.name,
            "value_expr": instruction_let.value_expr,
        }
    instruction_invoke = instruction.instruction_invoke
    if instruction_invoke is not None:
        target_function = instruction_invoke.target_function_config
        relationship = instruction_invoke.class_config_relationship
        signature["invoke"] = {
            "kind": _enum_text(instruction_invoke.kind),
            "target_function_owner_key": (
                target_function.owner_key if target_function is not None else None
            ),
            "target_function_name": (
                target_function.name if target_function is not None else None
            ),
            "relationship_key": (
                relationship.relationship_key if relationship is not None else None
            ),
            "attribute_configs": tuple(
                {
                    "position": attribute_config.position,
                    "attribute_config_name": (
                        attribute_config.attribute_config.name
                        if attribute_config.attribute_config is not None
                        else None
                    ),
                    "value_expr": attribute_config.value_expr,
                }
                for attribute_config in sorted(
                    instruction_invoke.attribute_configs,
                    key=lambda item: (item.position or 0, str(item.id)),
                )
            ),
        }
    instruction_construct = instruction.instruction_construct
    if instruction_construct is not None:
        target_class = instruction_construct.target_class_config
        signature["construct"] = {
            "target_class_fqn": (
                target_class.class_fqn if target_class is not None else None
            ),
            "assignments": tuple(
                _function_impl_construct_assignment_signature(
                    assignment=assignment,
                )
                for assignment in sorted(
                    instruction_construct.assignments,
                    key=lambda item: (item.position or 0, str(item.id)),
                )
            ),
        }
    instruction_set = instruction.instruction_set
    if instruction_set is not None:
        target_edge = instruction_set.target_class_config_attribute_config
        target_attribute = target_edge.attribute_config
        signature["set"] = {
            "target_attribute_name": target_attribute.name,
            "target_class_config_attribute_config_id": str(target_edge.id),
            "value_source": _function_impl_value_source_signature(
                value_source=instruction_set.value_source,
            ),
        }
    instruction_require = instruction.instruction_require
    if instruction_require is not None:
        signature["require"] = {
            "kind": _enum_text(instruction_require.kind),
            "compare_operator": _enum_text(instruction_require.compare_operator),
            "expected_count": instruction_require.expected_count,
            "message": instruction_require.message,
            "operands": tuple(
                _function_impl_require_operand_signature(operand=operand)
                for operand in sorted(
                    instruction_require.operands,
                    key=lambda item: (item.position, str(item.id)),
                )
            ),
        }
    return signature


def _function_impl_construct_assignment_signature(
    *,
    assignment: FunctionImplInstructionConstructAssignment,
) -> dict[str, object]:
    target_edge = assignment.target_class_config_attribute_config
    target_attribute = target_edge.attribute_config
    return {
        "position": assignment.position,
        "target_attribute_name": target_attribute.name,
        "target_class_config_attribute_config_id": str(target_edge.id),
        "value_source": _function_impl_value_source_signature(
            value_source=assignment.value_source,
        ),
    }


def _function_impl_require_operand_signature(
    *,
    operand: FunctionImplInstructionRequireOperand,
) -> dict[str, object]:
    return {
        "position": operand.position,
        "value_source": _function_impl_value_source_signature(
            value_source=operand.value_source,
        ),
    }


def _function_impl_value_source_sort_key(
    value_source: FunctionImplValueSource,
) -> tuple[str, str]:
    return (value_source.key, str(value_source.id))


def _function_impl_value_source_signature(
    *,
    value_source: FunctionImplValueSource,
) -> dict[str, object]:
    signature: dict[str, object] = {
        "key": value_source.key,
        "kind": _enum_text(value_source.kind),
    }
    source_input = value_source.source_function_config_attribute_config
    if source_input is not None:
        source_attribute = source_input.attribute_config
        signature.update(
            {
                "source_function_config_attribute_config_id": str(
                    source_input.id
                ),
                "source_function_input_name": source_input.name,
                "source_attribute_config_name": (
                    source_attribute.name if source_attribute is not None else None
                ),
            }
        )
    source_let = value_source.source_instruction_let
    if source_let is not None:
        signature["source_let_name"] = source_let.name
    literal_primitive = value_source.source_literal_primitive
    if literal_primitive is not None:
        primitive_config = literal_primitive.primitive_config
        primitive_type = (
            primitive_config.primitive_type
            if primitive_config is not None
            else None
        )
        signature["source_literal_primitive"] = {
            "primitive_base_type": (
                primitive_type.base_type.value
                if primitive_type is not None
                and primitive_type.base_type is not None
                else None
            ),
            "value": literal_primitive.value,
        }
    return signature


def _function_impl_instruction_summary(
    *,
    signature: Mapping[str, object],
) -> str:
    instruction_type = _optional_text(signature.get("type")) or "instruction"
    if instruction_type == "set":
        set_payload = _mapping_payload(signature.get("set"))
        target = _optional_text(set_payload.get("target_attribute_name")) or "target"
        value_source = _mapping_payload(set_payload.get("value_source"))
        source = (
            _optional_text(value_source.get("source_function_input_name"))
            or _optional_text(value_source.get("source_let_name"))
            or _optional_text(value_source.get("key"))
            or "value"
        )
        return f"set {target} = {source}"
    return instruction_type


def _function_attribute_signature(
    *,
    edge: FunctionConfigAttributeConfig,
) -> dict[str, object]:
    attribute_config = edge.attribute_config
    descriptor = attribute_config.type_descriptor
    descriptor_signature = _attribute_descriptor_signature(descriptor=descriptor)
    return {
        "name": edge.name,
        "type": edge.type.value,
        "position": edge.position,
        "attribute_config_name": attribute_config.name,
        "type_descriptor": descriptor_signature,
        **descriptor_signature,
        "description": attribute_config.description,
        "default_value": attribute_config.default_value,
        "is_identity_key": edge.is_identity_key,
        "identity_key_origin": edge.identity_key_origin.value,
        "is_primary": attribute_config.is_primary,
        "is_public": attribute_config.is_public,
        "is_required": attribute_config.is_required,
        "is_unique": attribute_config.is_unique,
        "is_virtual": attribute_config.is_virtual,
        "exclude_serialization": attribute_config.exclude_serialization,
        "function_attribute_type": edge.type.value,
    }


def _function_attribute_membership_signature(
    *,
    attribute_edge: FunctionConfigAttributeConfig,
) -> dict[str, object]:
    return {
        "owner_kind": "function",
        "function_config_id": str(attribute_edge.function_config_id),
        "attribute_config_id": str(
            attribute_edge.attribute_config_id or attribute_edge.attribute_config.id
        ),
        "name": attribute_edge.name,
        "type": attribute_edge.type.value,
        "position": attribute_edge.position,
        "is_identity_key": attribute_edge.is_identity_key,
        "identity_key_origin": attribute_edge.identity_key_origin.value,
    }


def _attribute_descriptor_signature(
    *,
    descriptor: AttributeTypeDescriptor,
) -> dict[str, object]:
    primitive_config = descriptor.primitive_config
    primitive_type = (
        primitive_config.primitive_type if primitive_config is not None else None
    )
    class_config = descriptor.class_config
    enum_config = descriptor.enum_config
    return {
        "kind": descriptor.kind.value,
        "collection_kind": (
            descriptor.collection_kind.value
            if descriptor.collection_kind is not None
            else None
        ),
        "primitive_signature": (
            primitive_type.signature if primitive_type is not None else None
        ),
        "primitive_base_type": (
            primitive_type.base_type.value if primitive_type is not None else None
        ),
        "class_config_id": (
            str(descriptor.class_config_id)
            if descriptor.class_config_id is not None
            else None
        ),
        "class_fqn": class_config.class_fqn if class_config is not None else None,
        "enum_config_id": (
            str(descriptor.enum_config_id)
            if descriptor.enum_config_id is not None
            else None
        ),
        "enum_fqn": enum_config.enum_fqn if enum_config is not None else None,
        "child_links": tuple(
            {
                "role": child_link.role.value,
                "position": child_link.position,
                "child": _attribute_descriptor_signature(
                    descriptor=child_link.child,
                ),
            }
            for child_link in sorted(
                descriptor.child_links,
                key=lambda item: (
                    item.role.value,
                    item.position,
                    str(item.child_id or item.child.id),
                ),
            )
        ),
    }


def _relationship_signature(
    *,
    relationship: ClassConfigRelationship,
) -> dict[str, object]:
    return {
        "relationship_key": relationship.relationship_key,
        "relationship_type": relationship.relationship_type.value,
        "class_config_id": str(relationship.class_config_id),
        "target_class_config_id": str(relationship.target_class_config_id),
        "identity_rail": (
            relationship.identity_rail.value
            if relationship.identity_rail is not None
            else None
        ),
        "forward_required": relationship.forward_required,
        "forward_loading_strategy": (
            relationship.forward_loading_strategy.value
            if relationship.forward_loading_strategy is not None
            else None
        ),
        "reverse_loading_strategy": (
            relationship.reverse_loading_strategy.value
            if relationship.reverse_loading_strategy is not None
            else None
        ),
    }


def _entry_with_fingerprint(
    payload: Mapping[str, object],
    *,
    fingerprint_payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    entry = dict(payload)
    fingerprint_input = cast(
        Mapping[str, object],
        _semantic_fingerprint_payload(fingerprint_payload or entry),
    )
    entry["semantic_fingerprint"] = _semantic_fingerprint(
        payload=fingerprint_input
    )
    return entry


def _semantic_fingerprint(*, payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_safe(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _semantic_fingerprint_payload(value: object) -> object:
    if isinstance(value, Mapping):
        class_config_id = _optional_text(value.get("class_config_id"))
        normalized: dict[str, object] = {}
        for key, item in sorted(value.items(), key=lambda item: str(item[0])):
            text_key = str(key)
            if text_key == "node_id":
                continue
            if text_key == "class_fqn" and class_config_id is not None:
                continue
            if text_key == "identity_rail" and item is None:
                normalized[text_key] = "reference"
                continue
            normalized[text_key] = _semantic_fingerprint_payload(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_semantic_fingerprint_payload(item) for item in value]
    return value


def _json_safe(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _mapping_payload(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _enum_text(value: object) -> str | None:
    if value is None:
        return None
    raw_value = value.value if isinstance(value, Enum) else value
    return _optional_text(raw_value)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values: list[str] = []
        for item in value:
            text = _optional_text(item)
            if text is not None:
                values.append(text)
        return tuple(values)
    text = _optional_text(value)
    return (text,) if text is not None else ()
