from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_code.builder import build_code_from_content
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.symbol_table import CodeSymbolTable
from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
    SemanticCapabilityChangePreview,
    SemanticCapabilityDependencyRequirement,
    SemanticCapabilityDelta,
    SemanticCapabilityDiagnostic,
    SemanticCapabilityEvent,
)
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.manifest.spec import (
    AwarePackageKind,
    AwareTomlNamespaceMappingSpec,
    AwareTomlSpec,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.runtime_derivation import (
    RuntimeObjectConfigGraphDerivationResult,
    derive_runtime_object_config_graph,
    derive_runtime_object_config_graphs,
)
from aware_meta.semantic_diagnostics import collect_meta_completeness_diagnostics
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta.manifest.namespace_match import namespace_for_source_path
from aware_meta.graph.config.cross_ocg import (
    link_cross_ocg_relationships,
)

from .semantic_contract import META_OBJECT_CONFIG_GRAPH_OWNER

_META_OCG_REQUIRED_MATERIALIZATIONS = (
    "meta_object_config_graph_plan",
    "meta_object_config_graph_package_plan",
)


@dataclass(frozen=True, slots=True)
class MetaOcgSemanticDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class MetaOcgSemanticChangePreview:
    changed_source_files: tuple[str, ...]
    affected_object_config_graph_keys: tuple[str, ...]
    affected_node_keys: tuple[str, ...]
    semantic_deltas: tuple[SemanticCapabilityDelta, ...]
    semantic_events: tuple[SemanticCapabilityEvent, ...]
    graph_count: int
    node_count: int
    class_count: int
    enum_count: int
    function_count: int
    relationship_count: int
    required_materializations: tuple[str, ...]
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class MetaOcgSemanticAnalysisResult:
    schema_version: int
    package_root: str
    manifest_path: str
    source_files: tuple[str, ...]
    namespace_mappings: tuple[AwareTomlNamespaceMappingSpec, ...]
    source_object_config_graph: ObjectConfigGraph | None
    object_config_graph: ObjectConfigGraph | None
    runtime_derivation: RuntimeObjectConfigGraphDerivationResult | None
    diagnostics: tuple[MetaOcgSemanticDiagnostic, ...]
    change_preview: MetaOcgSemanticChangePreview
    code_package_delta: CodePackageDelta | None = None


@dataclass(frozen=True, slots=True)
class _BuiltMetaOcgPackage:
    spec: AwareTomlSpec
    manifest_path: Path
    package_root: Path
    source_files: tuple[str, ...]
    source_object_config_graph: ObjectConfigGraph
    runtime_derivation: RuntimeObjectConfigGraphDerivationResult
    object_config_graph: ObjectConfigGraph
    source_path_by_code_id: Mapping[UUID, str]


def analyze_meta_ocg_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    manifest_path: Path | None = None,
    code_package_delta: CodePackageDelta | None = None,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    external_runtime_graphs: Iterable[ObjectConfigGraph] = (),
    fail_on_error: bool = True,
    completeness_diagnostics: bool = False,
    completeness_diagnostic_severity: str = "warning",
) -> MetaOcgSemanticAnalysisResult:
    resolved_package_root = package_root.expanduser().resolve()
    resolved_manifest_path = _resolve_manifest_path(
        package_root=resolved_package_root,
        manifest_path=manifest_path,
    )
    try:
        built_package = _build_meta_ocg_package(
            package_root=resolved_package_root,
            source_files=source_files,
            manifest_path=resolved_manifest_path,
            external_graphs=tuple(external_graphs),
            external_runtime_graphs=tuple(external_runtime_graphs),
        )
        source_graph = built_package.source_object_config_graph
        runtime_derivation = built_package.runtime_derivation
        graph = built_package.object_config_graph
        source_file_names = built_package.source_files
        namespace_mappings = tuple(built_package.spec.build.namespace.mappings)
        diagnostics = _meta_completeness_diagnostics(
            enabled=completeness_diagnostics,
            severity=completeness_diagnostic_severity,
            source_graph=source_graph,
            runtime_derivation=runtime_derivation,
            source_path_by_code_id=built_package.source_path_by_code_id,
            function_impl_ownership=(
                built_package.spec.package.function_impl_ownership
            ),
            function_impl_parity_policy=(
                built_package.spec.package.function_impl_parity_policy
            ),
        )
        preview = _build_change_preview(
            spec=built_package.spec,
            object_config_graph=graph,
            source_files=source_file_names,
            source_path_by_code_id=built_package.source_path_by_code_id,
            code_package_delta=code_package_delta,
            runtime_derivation=runtime_derivation,
        )
    except Exception as exc:
        if fail_on_error:
            raise
        diagnostics = (
            MetaOcgSemanticDiagnostic(
                severity="error",
                code="aware_meta.semantic_analysis.invalid_ocg_source",
                message=str(exc),
            ),
        )
        source_graph = None
        runtime_derivation = None
        graph = None
        source_file_names = _source_file_names(source_files=source_files)
        namespace_mappings = ()
        required_semantic_dependencies = (
            _required_semantic_dependencies_for_manifest_path(
                manifest_path=resolved_manifest_path,
            )
        )
        preview = MetaOcgSemanticChangePreview(
            changed_source_files=_changed_source_files(
                source_files=source_file_names,
                code_package_delta=code_package_delta,
            ),
            affected_object_config_graph_keys=(),
            affected_node_keys=(),
            semantic_deltas=(),
            semantic_events=(),
            graph_count=0,
            node_count=0,
            class_count=0,
            enum_count=0,
            function_count=0,
            relationship_count=0,
            required_materializations=(),
            required_semantic_dependencies=required_semantic_dependencies,
        )

    return MetaOcgSemanticAnalysisResult(
        schema_version=1,
        package_root=resolved_package_root.as_posix(),
        manifest_path=resolved_manifest_path.as_posix(),
        source_files=source_file_names,
        namespace_mappings=namespace_mappings,
        source_object_config_graph=source_graph,
        object_config_graph=graph,
        runtime_derivation=runtime_derivation,
        diagnostics=diagnostics,
        change_preview=preview,
        code_package_delta=code_package_delta,
    )


def analyze_meta_ocg_code_package_delta(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta,
    manifest_path: Path | None = None,
    fail_on_error: bool = False,
) -> MetaOcgSemanticAnalysisResult:
    return analyze_meta_ocg_sources(
        package_root=package_root,
        source_files=source_files,
        manifest_path=manifest_path,
        code_package_delta=code_package_delta,
        fail_on_error=fail_on_error,
    )


def analyze_meta_ocg_semantic_capability(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    completeness_diagnostics = _metadata_bool(
        request.metadata,
        "meta_completeness_diagnostics",
        "completeness_diagnostics",
    )
    completeness_diagnostic_severity = _metadata_severity(
        request.metadata,
        "meta_completeness_diagnostic_severity",
        "completeness_diagnostic_severity",
        default="warning",
    )
    analysis = analyze_meta_ocg_sources(
        package_root=request.package_root,
        source_files=request.source_files,
        manifest_path=request.manifest_path,
        code_package_delta=request.code_package_delta,
        fail_on_error=False,
        completeness_diagnostics=completeness_diagnostics,
        completeness_diagnostic_severity=completeness_diagnostic_severity,
    )
    preview = analysis.change_preview
    return SemanticAnalysisCapabilityResult(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        package_root=analysis.package_root,
        source_files=analysis.source_files,
        diagnostics=tuple(
            SemanticCapabilityDiagnostic(
                severity=diagnostic.severity,
                code=diagnostic.code,
                message=diagnostic.message,
                source_path=diagnostic.source_path,
            )
            for diagnostic in analysis.diagnostics
        ),
        change_preview=SemanticCapabilityChangePreview(
            changed_source_files=preview.changed_source_files,
            affected_semantic_keys=preview.affected_object_config_graph_keys,
            required_materializations=preview.required_materializations,
            required_semantic_dependencies=preview.required_semantic_dependencies,
            semantic_deltas=preview.semantic_deltas,
            semantic_events=preview.semantic_events,
            metadata={
                "affected_node_keys": preview.affected_node_keys,
                "graph_count": preview.graph_count,
                "node_count": preview.node_count,
                "class_count": preview.class_count,
                "enum_count": preview.enum_count,
                "function_count": preview.function_count,
                "relationship_count": preview.relationship_count,
                "function_call_policy": "pending_runtime_ocg_node_mutation_functions",
                "semantic_truth_graph": "runtime_ocg",
                "source_graph_role": "compiler_ir",
                "runtime_graph_role": "runtime_ocg",
                "source_graph_hash": (
                    analysis.runtime_derivation.source_graph_hash
                    if analysis.runtime_derivation is not None
                    else None
                ),
                "runtime_graph_hash": (
                    analysis.runtime_derivation.runtime_graph_hash
                    if analysis.runtime_derivation is not None
                    else None
                ),
            },
        ),
        payload=analysis,
        code_package_delta=request.code_package_delta,
    )


def _resolve_manifest_path(
    *,
    package_root: Path,
    manifest_path: Path | None,
) -> Path:
    if manifest_path is None:
        return (package_root / "aware.toml").resolve()
    resolved = manifest_path.expanduser().resolve()
    if resolved.is_absolute():
        return resolved
    return (package_root / resolved).resolve()


def _build_meta_ocg_package(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    manifest_path: Path,
    external_graphs: tuple[ObjectConfigGraph, ...] = (),
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
) -> _BuiltMetaOcgPackage:
    setup_code_plugins()
    spec = load_aware_toml_spec(toml_path=manifest_path)
    sources_root = (package_root / spec.build.sources_dir).resolve()
    analysis_source_files = _analysis_source_files(
        package_root=package_root,
        sources_root=sources_root,
        source_files=source_files,
        spec=spec,
    )
    parsed_sources = _parse_source_files(
        package_root=package_root,
        sources_root=sources_root,
        source_files=analysis_source_files,
    )
    if not parsed_sources:
        raise ValueError(
            "Meta OCG semantic analysis requires at least one `.aware` source file."
        )

    source_paths = tuple(source_path for source_path, _code in parsed_sources)
    source_path_by_code_id = {
        code.id: source_path
        for source_path, code in parsed_sources
        if code.id is not None
    }
    namespace_by_code_id = _build_namespace_by_code_id(
        source_paths=source_paths,
        parsed_sources=tuple(parsed_sources),
        fqn_prefix=spec.package.fqn_prefix,
        namespace_mappings=tuple(spec.build.namespace.mappings),
    )
    build_result = build_object_config_graph_from_code(
        name=spec.package.fqn_prefix,
        description=(
            spec.package.description
            or f"ObjectConfigGraph for {spec.package.package_name}"
        ),
        fqn_prefix=spec.package.fqn_prefix,
        file_codes=list(parsed_sources),
        namespace_by_code_id=namespace_by_code_id,
        package_kind=AwarePackageKind(spec.package.kind.value),
        external_graphs=list(external_graphs),
    )
    if external_graphs:
        link_cross_ocg_relationships(
            build_results_by_language={CodeLanguage.aware: build_result},
            external_graphs=list(external_graphs),
        )
    runtime_external_graphs = _runtime_external_graphs_for_analysis(
        external_graphs=external_graphs,
        explicit_external_runtime_graphs=external_runtime_graphs,
    )
    runtime_derivation = derive_runtime_object_config_graph(
        build_result.graph,
        external_runtime_graphs=runtime_external_graphs,
        include_projection_graphs=True,
    )
    return _BuiltMetaOcgPackage(
        spec=spec,
        manifest_path=manifest_path,
        package_root=package_root,
        source_files=source_paths,
        source_object_config_graph=build_result.graph,
        runtime_derivation=runtime_derivation,
        object_config_graph=runtime_derivation.runtime_graph,
        source_path_by_code_id=source_path_by_code_id,
    )


def _runtime_external_graphs_for_analysis(
    *,
    external_graphs: tuple[ObjectConfigGraph, ...],
    explicit_external_runtime_graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    if explicit_external_runtime_graphs:
        return explicit_external_runtime_graphs
    if not external_graphs:
        return ()
    if all(
        _external_graph_has_attached_projection_truth(graph)
        for graph in external_graphs
    ):
        return external_graphs
    return derive_runtime_object_config_graphs(
        external_graphs,
        include_projection_graphs=True,
    )


def _external_graph_has_attached_projection_truth(graph: ObjectConfigGraph) -> bool:
    if not graph.object_projection_graph_declarations:
        return True
    return bool(graph.object_projection_graphs)


def _analysis_source_files(
    *,
    package_root: Path,
    sources_root: Path,
    source_files: tuple[Path, ...],
    spec: AwareTomlSpec,
) -> tuple[Path, ...]:
    selected: list[Path] = []
    seen: set[Path] = set()
    for source_file in source_files:
        resolved = _resolve_source_file(
            package_root=package_root,
            sources_root=sources_root,
            source_file=source_file,
        )
        if resolved.suffix != ".aware" or not resolved.is_file():
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        selected.append(resolved)

    for pattern in spec.build.include_paths:
        for candidate in sorted(sources_root.glob(pattern)):
            if candidate.suffix != ".aware" or not candidate.is_file():
                continue
            if _is_excluded_source(
                source_path=candidate,
                sources_root=sources_root,
                exclude_paths=tuple(spec.build.exclude_paths),
            ):
                continue
            resolved_candidate = candidate.resolve()
            if resolved_candidate in seen:
                continue
            seen.add(resolved_candidate)
            selected.append(resolved_candidate)
    return tuple(selected)


def _is_excluded_source(
    *,
    source_path: Path,
    sources_root: Path,
    exclude_paths: tuple[str, ...],
) -> bool:
    if not exclude_paths:
        return False
    try:
        relative_path = source_path.resolve().relative_to(sources_root).as_posix()
    except ValueError:
        return False
    relative = Path(relative_path)
    return any(relative.match(pattern) for pattern in exclude_paths)


def _parse_source_files(
    *,
    package_root: Path,
    sources_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[tuple[str, Code], ...]:
    section_index = CodeSectionBuilderIndex()
    symbol_table = CodeSymbolTable()
    parsed: list[tuple[str, Code]] = []
    seen: set[str] = set()
    for source_file in source_files:
        source_path = _resolve_source_file(
            package_root=package_root,
            sources_root=sources_root,
            source_file=source_file,
        )
        if source_path.suffix != ".aware":
            continue
        source_relative_path = _relative_to_source_root(
            path=source_path,
            sources_root=sources_root,
            package_root=package_root,
        )
        if source_relative_path in seen:
            continue
        seen.add(source_relative_path)
        code = build_code_from_content(
            sections_index=section_index,
            content=source_path.read_text(encoding="utf-8"),
            code_key=source_relative_path,
            language=CodeLanguage.aware,
            symbol_table=symbol_table,
        )
        parsed.append((source_relative_path, code))
    return tuple(sorted(parsed, key=lambda item: item[0]))


def _resolve_source_file(
    *,
    package_root: Path,
    sources_root: Path,
    source_file: Path,
) -> Path:
    candidate = source_file.expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    package_candidate = (package_root / candidate).resolve()
    if package_candidate.exists():
        return package_candidate
    return (sources_root / candidate).resolve()


def _relative_to_source_root(
    *,
    path: Path,
    sources_root: Path,
    package_root: Path,
) -> str:
    try:
        return path.resolve().relative_to(sources_root).as_posix()
    except ValueError:
        return path.resolve().relative_to(package_root).as_posix()


def _build_namespace_by_code_id(
    *,
    source_paths: tuple[str, ...],
    parsed_sources: tuple[tuple[str, Code], ...],
    fqn_prefix: str,
    namespace_mappings: tuple[AwareTomlNamespaceMappingSpec, ...],
) -> dict[UUID, NamespacePath]:
    namespace_by_source_path = {
        source_path: namespace_for_source_path(
            source_path=source_path,
            namespace_mappings=namespace_mappings,
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


def _build_change_preview(
    *,
    spec: AwareTomlSpec,
    object_config_graph: ObjectConfigGraph,
    source_files: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
    code_package_delta: CodePackageDelta | None,
    runtime_derivation: RuntimeObjectConfigGraphDerivationResult,
) -> MetaOcgSemanticChangePreview:
    changed_source_files = _changed_source_files(
        source_files=source_files,
        code_package_delta=code_package_delta,
    )
    source_path_by_class_config_id = _source_path_by_class_config_id(
        object_config_graph=object_config_graph,
        source_path_by_code_id=source_path_by_code_id,
    )
    affected_nodes = _affected_nodes(
        object_config_graph=object_config_graph,
        changed_source_files=changed_source_files,
        source_path_by_code_id=source_path_by_code_id,
        source_path_by_class_config_id=source_path_by_class_config_id,
    )
    graph_metadata = _runtime_graph_metadata(runtime_derivation=runtime_derivation)
    semantic_deltas = _semantic_deltas_for_graph(
        spec=spec,
        object_config_graph=object_config_graph,
        affected_nodes=affected_nodes,
        source_path_by_code_id=source_path_by_code_id,
        source_path_by_class_config_id=source_path_by_class_config_id,
        graph_metadata=graph_metadata,
    )
    semantic_events = _semantic_events_for_deltas(
        semantic_deltas=semantic_deltas,
        graph_metadata=graph_metadata,
    )
    return MetaOcgSemanticChangePreview(
        changed_source_files=changed_source_files,
        affected_object_config_graph_keys=(
            f"ocg:{spec.package.fqn_prefix}",
            f"ocg_package:{spec.package.package_name}",
        ),
        affected_node_keys=tuple(
            sorted(
                _node_semantic_key(object_config_graph, node) for node in affected_nodes
            )
        ),
        semantic_deltas=semantic_deltas,
        semantic_events=semantic_events,
        graph_count=1,
        node_count=len(object_config_graph.object_config_graph_nodes),
        class_count=_node_count(
            object_config_graph=object_config_graph,
            node_type=ObjectConfigGraphNodeType.class_,
        ),
        enum_count=_node_count(
            object_config_graph=object_config_graph,
            node_type=ObjectConfigGraphNodeType.enum,
        ),
        function_count=_node_count(
            object_config_graph=object_config_graph,
            node_type=ObjectConfigGraphNodeType.function,
        ),
        relationship_count=_node_count(
            object_config_graph=object_config_graph,
            node_type=ObjectConfigGraphNodeType.relationship,
        ),
        required_materializations=_META_OCG_REQUIRED_MATERIALIZATIONS,
        required_semantic_dependencies=(
            _required_semantic_dependencies_for_spec(spec=spec)
        ),
    )


def _required_semantic_dependencies_for_spec(
    *,
    spec: AwareTomlSpec,
) -> tuple[SemanticCapabilityDependencyRequirement, ...]:
    dependencies: list[SemanticCapabilityDependencyRequirement] = []
    source_package_name = spec.package.package_name
    for dependency in spec.dependencies:
        package_name = dependency.package_name.strip()
        if not package_name:
            continue
        dependencies.append(
            SemanticCapabilityDependencyRequirement(
                dependency_key=(
                    "aware_meta.object_config_graph_package.dependency:"
                    f"{source_package_name}:{package_name}"
                ),
                provider_key="aware_meta",
                semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
                package_name=package_name,
                manifest_kind="aware_toml",
                reason="aware_toml_dependency",
                source_refs=(Path("aware.toml").as_posix(),),
                metadata={
                    "source_package_name": source_package_name,
                    "source_fqn_prefix": spec.package.fqn_prefix,
                    "dependency_package_name": package_name,
                },
            )
        )
    return tuple(dependencies)


def _required_semantic_dependencies_for_manifest_path(
    *,
    manifest_path: Path,
) -> tuple[SemanticCapabilityDependencyRequirement, ...]:
    try:
        spec = load_aware_toml_spec(toml_path=manifest_path)
    except Exception:
        return ()
    return _required_semantic_dependencies_for_spec(spec=spec)


def _semantic_deltas_for_graph(
    *,
    spec: AwareTomlSpec,
    object_config_graph: ObjectConfigGraph,
    affected_nodes: tuple[ObjectConfigGraphNode, ...],
    source_path_by_code_id: Mapping[UUID, str],
    source_path_by_class_config_id: Mapping[UUID, str],
    graph_metadata: Mapping[str, object],
) -> tuple[SemanticCapabilityDelta, ...]:
    package_key = f"ocg_package:{spec.package.package_name}"
    graph_key = f"ocg:{spec.package.fqn_prefix}"
    deltas: list[SemanticCapabilityDelta] = [
        SemanticCapabilityDelta(
            delta_key=f"aware_meta.object_config_graph_package.upsert:{package_key}",
            semantic_key=package_key,
            verb="upsert",
            subject_type="aware_meta.ObjectConfigGraphPackage",
            source="aware_meta.semantic_analysis",
            source_refs=(Path("aware.toml").as_posix(),),
            after_payload={
                "package_name": spec.package.package_name,
                "fqn_prefix": spec.package.fqn_prefix,
                "package_kind": spec.package.kind.value,
            },
            metadata=graph_metadata,
        ),
        SemanticCapabilityDelta(
            delta_key=f"aware_meta.object_config_graph.upsert:{graph_key}",
            semantic_key=graph_key,
            verb="upsert",
            subject_type="aware_meta.ObjectConfigGraph",
            source="aware_meta.semantic_analysis",
            source_refs=tuple(sorted(set(source_path_by_code_id.values()))),
            after_payload={
                "name": object_config_graph.name,
                "fqn_prefix": object_config_graph.fqn_prefix,
                "language": object_config_graph.language.value,
                "hash": object_config_graph.hash,
                "node_count": len(object_config_graph.object_config_graph_nodes),
            },
            metadata=graph_metadata,
        ),
    ]
    for node in sorted(
        affected_nodes, key=lambda item: _node_semantic_key(object_config_graph, item)
    ):
        source_paths = _source_paths_for_node(
            node=node,
            source_path_by_code_id=source_path_by_code_id,
            source_path_by_class_config_id=source_path_by_class_config_id,
        )
        source_path = source_paths[0] if source_paths else None
        semantic_key = _node_semantic_key(object_config_graph, node)
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=f"aware_meta.object_config_graph_node.upsert:{semantic_key}",
                semantic_key=semantic_key,
                verb="upsert",
                subject_type="aware_meta.ObjectConfigGraphNode",
                source="aware_meta.semantic_analysis",
                source_refs=source_paths,
                after_payload={
                    "graph_semantic_key": graph_key,
                    "node_id": str(node.id),
                    "node_key": node.node_key,
                    "node_type": node.type.value,
                    "entity_id": str(_node_entity_id(node)),
                    "entity_name": _node_entity_name(node),
                    "source_path": source_path,
                    "source_paths": source_paths,
                },
                metadata={
                    **dict(graph_metadata),
                    "runtime_node_type": node.type.value,
                },
            )
        )
    return tuple(deltas)


def _semantic_events_for_deltas(
    *,
    semantic_deltas: tuple[SemanticCapabilityDelta, ...],
    graph_metadata: Mapping[str, object],
) -> tuple[SemanticCapabilityEvent, ...]:
    return tuple(
        SemanticCapabilityEvent(
            event_key=f"{_event_prefix(delta.subject_type)}.{delta.verb}ed",
            semantic_key=delta.semantic_key,
            verb=delta.verb,
            subject_type=delta.subject_type,
            source=delta.source,
            source_refs=delta.source_refs,
            delta_keys=(delta.delta_key,),
            payload=dict(delta.after_payload or {}),
            metadata={
                **dict(graph_metadata),
                "delta_metadata": dict(delta.metadata),
            },
        )
        for delta in semantic_deltas
    )


def _event_prefix(subject_type: str) -> str:
    return {
        "aware_meta.ObjectConfigGraphPackage": (
            "aware_meta.object_config_graph_package"
        ),
        "aware_meta.ObjectConfigGraph": "aware_meta.object_config_graph",
        "aware_meta.ObjectConfigGraphNode": "aware_meta.object_config_graph_node",
    }.get(subject_type, subject_type)


def _affected_nodes(
    *,
    object_config_graph: ObjectConfigGraph,
    changed_source_files: tuple[str, ...],
    source_path_by_code_id: Mapping[UUID, str],
    source_path_by_class_config_id: Mapping[UUID, str],
) -> tuple[ObjectConfigGraphNode, ...]:
    if not changed_source_files:
        return tuple(object_config_graph.object_config_graph_nodes)
    changed = frozenset(changed_source_files)
    return tuple(
        node
        for node in object_config_graph.object_config_graph_nodes
        if any(
            source_path in changed
            for source_path in _source_paths_for_node(
                node=node,
                source_path_by_code_id=source_path_by_code_id,
                source_path_by_class_config_id=source_path_by_class_config_id,
            )
        )
    )


def _source_paths_for_node(
    *,
    node: ObjectConfigGraphNode,
    source_path_by_code_id: Mapping[UUID, str],
    source_path_by_class_config_id: Mapping[UUID, str],
) -> tuple[str, ...]:
    code_id = _node_source_code_id(node)
    source_paths: set[str] = set()
    if code_id is not None:
        source_path = source_path_by_code_id.get(code_id)
        if source_path is not None:
            source_paths.add(source_path)

    relationship = node.class_config_relationship
    if relationship is not None:
        for class_config_id in _relationship_class_config_ids(relationship):
            source_path = source_path_by_class_config_id.get(class_config_id)
            if source_path is not None:
                source_paths.add(source_path)
    return tuple(sorted(source_paths))


def _source_path_by_class_config_id(
    *,
    object_config_graph: ObjectConfigGraph,
    source_path_by_code_id: Mapping[UUID, str],
) -> dict[UUID, str]:
    source_path_by_class_config_id: dict[UUID, str] = {}
    for node in object_config_graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None:
            continue
        code_section_class = class_config.code_section_class
        code_section = (
            code_section_class.code_section if code_section_class is not None else None
        )
        if code_section is None:
            continue
        source_path = source_path_by_code_id.get(code_section.code_id)
        if source_path is not None:
            source_path_by_class_config_id[class_config.id] = source_path
    return source_path_by_class_config_id


def _relationship_class_config_ids(relationship: Any) -> tuple[UUID, ...]:
    class_config_ids: set[UUID] = set()
    for value in (
        getattr(relationship, "class_config_id", None),
        getattr(relationship, "target_class_config_id", None),
    ):
        if isinstance(value, UUID):
            class_config_ids.add(value)
    target_class_config = getattr(relationship, "target_class_config", None)
    target_class_config_id = getattr(target_class_config, "id", None)
    if isinstance(target_class_config_id, UUID):
        class_config_ids.add(target_class_config_id)
    association_edge = getattr(
        relationship,
        "class_config_relationship_association_edge",
        None,
    )
    association_class_config_id = getattr(association_edge, "class_config_id", None)
    if isinstance(association_class_config_id, UUID):
        class_config_ids.add(association_class_config_id)
    return tuple(sorted(class_config_ids, key=str))


def _runtime_graph_metadata(
    *,
    runtime_derivation: RuntimeObjectConfigGraphDerivationResult,
) -> dict[str, object]:
    return {
        "semantic_truth_graph": "runtime_ocg",
        "source_graph_role": runtime_derivation.source_graph_role,
        "runtime_graph_role": runtime_derivation.runtime_graph_role,
        "source_graph_hash": runtime_derivation.source_graph_hash,
        "runtime_graph_hash": runtime_derivation.runtime_graph_hash,
    }


def _node_source_code_id(node: ObjectConfigGraphNode) -> UUID | None:
    code_section = None
    if node.class_config is not None:
        code_section_class = node.class_config.code_section_class
        code_section = (
            code_section_class.code_section if code_section_class is not None else None
        )
    elif node.enum_config is not None:
        code_section_enum = node.enum_config.code_section_enum
        code_section = (
            code_section_enum.code_section if code_section_enum is not None else None
        )
    elif (function_config := _node_function_config(node)) is not None:
        code_section_function = function_config.code_section_function
        code_section = (
            code_section_function.code_section
            if code_section_function is not None
            else None
        )
    if code_section is None:
        return None
    return code_section.code_id


def _node_semantic_key(
    object_config_graph: ObjectConfigGraph,
    node: ObjectConfigGraphNode,
) -> str:
    return f"ocg:{object_config_graph.fqn_prefix}/node:{node.node_key}"


def _node_entity_id(node: ObjectConfigGraphNode) -> UUID:
    if node.class_config is not None:
        return node.class_config.id
    if node.enum_config is not None:
        return node.enum_config.id
    if (function_config := _node_function_config(node)) is not None:
        return function_config.id
    if node.class_config_relationship is not None:
        return node.class_config_relationship.id
    return node.id


def _node_entity_name(node: ObjectConfigGraphNode) -> str | None:
    if node.class_config is not None:
        return node.class_config.name
    if node.enum_config is not None:
        return node.enum_config.name
    if (function_config := _node_function_config(node)) is not None:
        return function_config.name
    relationship = node.class_config_relationship
    if relationship is not None:
        return relationship.relationship_key
    return None


def _node_function_config(node: ObjectConfigGraphNode) -> Any | None:
    return getattr(node, "function_config", None)


def _node_count(
    *,
    object_config_graph: ObjectConfigGraph,
    node_type: ObjectConfigGraphNodeType,
) -> int:
    return sum(
        1
        for node in object_config_graph.object_config_graph_nodes
        if node.type == node_type
    )


def _changed_source_files(
    *,
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
) -> tuple[str, ...]:
    if code_package_delta is None:
        return source_files
    changed_paths = frozenset(
        _normalize_path_text(path.relative_path)
        for path in code_package_delta.paths
        if _normalize_path_text(path.relative_path)
    )
    if not changed_paths:
        return source_files
    matched = tuple(
        source_file
        for source_file in source_files
        if source_file in changed_paths
        or any(
            source_file.endswith(f"/{changed_path}") for changed_path in changed_paths
        )
        or any(
            changed_path.endswith(f"/{source_file}") for changed_path in changed_paths
        )
    )
    return tuple(sorted(matched)) or source_files


def _source_file_names(*, source_files: tuple[Path, ...]) -> tuple[str, ...]:
    return tuple(_normalize_path_text(path.as_posix()) for path in source_files)


def _normalize_path_text(value: str) -> str:
    return Path(value).as_posix().strip().strip("/")


def _meta_completeness_diagnostics(
    *,
    enabled: bool,
    severity: str,
    source_graph: ObjectConfigGraph,
    runtime_derivation: RuntimeObjectConfigGraphDerivationResult,
    source_path_by_code_id: Mapping[UUID, str],
    function_impl_ownership: str = "authored",
    function_impl_parity_policy: str = "off",
) -> tuple[MetaOcgSemanticDiagnostic, ...]:
    if not enabled:
        return ()
    normalized_ownership = str(function_impl_ownership).strip().lower()
    normalized_parity_policy = str(function_impl_parity_policy).strip().lower()
    native_function_impl_required = (
        normalized_ownership == "compiler"
        and normalized_parity_policy in {"warn", "error"}
    )
    native_function_impl_severity = (
        "error" if normalized_parity_policy == "error" else severity
    )
    return tuple(
        MetaOcgSemanticDiagnostic(
            severity=diagnostic.severity,
            code=diagnostic.code,
            message=diagnostic.message,
            source_path=diagnostic.source_path,
        )
        for diagnostic in collect_meta_completeness_diagnostics(
            source_graph=source_graph,
            runtime_derivation=runtime_derivation,
            severity=severity,
            source_path_by_code_id=source_path_by_code_id,
            native_function_impl_required=native_function_impl_required,
            native_function_impl_severity=native_function_impl_severity,
        )
    )


def _metadata_bool(
    metadata: Mapping[str, object],
    *keys: str,
) -> bool:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "enabled"}:
                return True
            if normalized in {"0", "false", "no", "off", "disabled"}:
                return False
    return False


def _metadata_severity(
    metadata: Mapping[str, object],
    *keys: str,
    default: str,
) -> str:
    for key in keys:
        value = metadata.get(key)
        if not isinstance(value, str):
            continue
        normalized = value.strip().lower()
        if normalized in {"error", "warning", "info"}:
            return normalized
    return default


__all__ = [
    "MetaOcgSemanticAnalysisResult",
    "MetaOcgSemanticChangePreview",
    "MetaOcgSemanticDiagnostic",
    "analyze_meta_ocg_code_package_delta",
    "analyze_meta_ocg_semantic_capability",
    "analyze_meta_ocg_sources",
]
