from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from aware_meta.manifest.loader import load_aware_toml_spec
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.semantic_materialization import (
    SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY,
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_meta.materialization import (
    LanguagePluginMaterializationRequest,
    materialize_object_config_graph_via_language_plugin,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_environment.materialization.projection_catalog import (
    environment_meta_projection_catalog_from_context,
)

if TYPE_CHECKING:
    from aware_environment.materialization.service import (
        EnvironmentSemanticPackageMaterializationRef,
    )

_FULL_REBUILD_FALLBACK_REASON = (
    "Environment provider has not implemented delta materialization yet; "
    "replayed the full Environment package manifest."
)
logger = logging.getLogger(__name__)
_WORKSPACE_MATERIALIZED_SEMANTIC_PACKAGE_REFS_CONTEXT_KEY = (
    "workspace_materialized_semantic_package_refs"
)


@dataclass(frozen=True, slots=True)
class _EnvironmentLanguageMaterializationTarget:
    target_language_plugin_id: CodeLanguage
    output_root: Path
    import_root: str
    package_name: str
    materialization_source: str
    source_is_runtime: bool = False
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    stable_ids_import_root: str | None = None


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    from aware_environment.materialization.service import (
        materialize_environment_package_from_manifest,
    )

    progress_callback = cast(
        Any | None,
        request.context.get("semantic_package_progress_callback"),
    )
    result = await materialize_environment_package_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        environment_toml_path=request.manifest_path,
        semantic_package_progress_callback=progress_callback,
        collect_leaf_telemetry=_context_bool(
            request.context.get("environment_semantic_package_collect_telemetry"),
            default=True,
        ),
        selected_semantic_package_names=_context_strings(
            request.context.get("environment_semantic_package_names")
        ),
        dependency_object_config_graphs_by_package_name=(
            _source_object_config_graphs_by_package_name_from_context(request.context)
        ),
        completed_semantic_packages_by_package_name=(
            _completed_semantic_packages_by_package_name_from_context(
                context=request.context,
                workspace_root=request.workspace_root,
            )
        ),
        meta_projection_catalog=environment_meta_projection_catalog_from_context(
            request.context
        ),
        semantic_ontology_package_catalog=(
            _semantic_ontology_package_catalog_from_context(request.context)
        ),
    )
    environment_handle = result.environment_spec.environment.handle
    semantic_package_artifact_ownership_receipts = (
        _semantic_package_artifact_ownership_receipts(result.semantic_packages)
    )
    semantic_package_language_materialization_receipts = (
        _environment_semantic_package_language_materialization_receipts(
            result=result,
            workspace_root=request.workspace_root,
            context=request.context,
        )
    )
    environment_runtime_artifact_ownership_receipts = (
        _environment_runtime_artifact_ownership_receipts(
            result=result,
            workspace_root=request.workspace_root,
            index=request.index,
            branch_id=request.branch_id,
            context=request.context,
        )
    )
    artifact_ownership_receipts = (
        *semantic_package_artifact_ownership_receipts,
        *semantic_package_language_materialization_receipts,
        *environment_runtime_artifact_ownership_receipts,
    )
    return SemanticPackageMaterializationResult(
        details={
            "environment_handle": environment_handle,
            "environment_toml_path": result.environment_toml_path.as_posix(),
            "environment_config_id": str(result.environment_config.id),
            "environment_package_id": str(result.environment_package.id),
            "environment_config_object_instance_graph_commit_id": (
                str(result.environment_config_object_instance_graph_commit_id)
                if result.environment_config_object_instance_graph_commit_id is not None
                else None
            ),
            "semantic_package_selector_count": len(_environment_module_names(result)),
            "completed_semantic_package_reuse_count": int(
                result.phase_timings_s.get(
                    "reuse_completed_semantic_package_count",
                    0.0,
                )
            ),
            "code_module_count": len(
                _context_strings(getattr(result, "code_module_names", None))
            ),
            "environment_phase_timings_s": dict(sorted(result.phase_timings_s.items())),
            "environment_environment_commit_id": (
                str(result.environment_commit_id)
                if result.environment_commit_id is not None
                else None
            ),
            "environment_environment_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "environment_environment_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
            "environment_environment_package_object_instance_graph_commit_id": (
                str(result.package_object_instance_graph_commit_id)
                if result.package_object_instance_graph_commit_id is not None
                else None
            ),
            "artifact_ownership_receipts": artifact_ownership_receipts,
            "semantic_package_artifact_ownership_receipt_count": len(
                semantic_package_artifact_ownership_receipts
            ),
            "semantic_package_language_materialization_receipt_count": len(
                semantic_package_language_materialization_receipts
            ),
            "environment_runtime_artifact_ownership_receipt_count": len(
                environment_runtime_artifact_ownership_receipts
            ),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=environment_handle,
                manifest_toml_path=result.environment_toml_path,
                semantic_package_id=result.environment_package.id,
                semantic_root_id=result.environment_config.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    result.package_object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    result.environment_config_object_instance_graph_commit_id
                ),
                environment_config_package_dependencies=tuple(
                    {
                        "dependency_role": dependency.dependency_role,
                        "dependency_index": dependency.dependency_index,
                        "target_handle": dependency.target_handle,
                        "target_environment_config_package_id": str(
                            dependency.target_environment_config_package_id
                        ),
                        "target_environment_config_package_object_instance_graph_commit_id": str(
                            dependency.target_environment_config_package_object_instance_graph_commit_id
                        ),
                        "manifest_path": dependency.manifest_path.as_posix(),
                        "manifest_toml_path": dependency.manifest_toml_path.as_posix(),
                    }
                    for dependency in result.environment_package_dependencies
                ),
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(
            request,
            fallback_keys=_semantic_package_names_from_result(
                result.semantic_packages,
                context=request.context,
                environment_handle=environment_handle,
            ),
        ),
        applied_semantic_keys=_semantic_keys_from_request(
            request,
            fallback_keys=_semantic_package_names_from_result(
                result.semantic_packages,
                context=request.context,
                environment_handle=environment_handle,
            ),
        ),
        skipped_semantic_keys=(),
        stale_semantic_keys=(),
        fallback_reason=_FULL_REBUILD_FALLBACK_REASON,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
        semantic_packages=tuple(result.semantic_packages),
        semantic_object_config_graphs=tuple(result.semantic_object_config_graphs),
    )


def _semantic_package_artifact_ownership_receipts(
    semantic_packages: object,
) -> tuple[dict[str, object], ...]:
    if not isinstance(semantic_packages, (list, tuple)):
        return ()
    return tuple(
        dict(receipt)
        for semantic_package in semantic_packages
        for receipt in getattr(
            semantic_package,
            "artifact_ownership_receipts",
            (),
        )
        if isinstance(receipt, Mapping)
    )


def _environment_semantic_package_language_materialization_receipts(
    *,
    result: object,
    workspace_root: Path,
    context: Mapping[str, object] | None = None,
) -> tuple[dict[str, object], ...]:
    targets = _environment_language_materialization_targets_from_context(
        context=context,
        workspace_root=workspace_root,
    )
    if not targets:
        return ()
    semantic_packages = tuple(getattr(result, "semantic_packages", ()) or ())
    semantic_graphs = _semantic_object_config_graphs(result)
    if not semantic_packages or not semantic_graphs:
        return ()

    source_graphs_by_fqn_prefix = _source_object_config_graphs_by_fqn_prefix(
        _source_object_config_graphs_from_context(context)
    )
    source_graphs_by_package_name = (
        _source_object_config_graphs_by_package_name_from_context(context)
    )
    runtime_projection_graphs_by_ocg_id = (
        _runtime_projection_graphs_by_ocg_id_from_context(
            context=context,
        )
    )
    runtime_graphs = _runtime_object_config_graphs_with_projection_graphs(
        _runtime_object_config_graphs_from_context(context),
        runtime_projection_graphs_by_ocg_id=runtime_projection_graphs_by_ocg_id,
    )
    runtime_graphs_by_fqn_prefix = _runtime_object_config_graphs_by_fqn_prefix(
        runtime_graphs
    )
    runtime_graphs_by_package_name = (
        _object_config_graphs_by_package_name_with_projection_graphs(
            _runtime_object_config_graphs_by_package_name_from_context(context),
            runtime_projection_graphs_by_ocg_id=runtime_projection_graphs_by_ocg_id,
        )
    )

    receipts: list[dict[str, object]] = []
    for package_ref, package_graph in _semantic_package_graph_pairs(
        semantic_packages=semantic_packages,
        semantic_graphs=semantic_graphs,
    ):
        package_name = _semantic_package_name(package_ref)
        package_targets = tuple(
            target
            for target in targets
            if _environment_language_target_matches_package(
                target=target,
                package_ref=package_ref,
            )
        )
        if not package_targets:
            continue
        package_root = _semantic_package_root(
            package_ref=package_ref,
            workspace_root=workspace_root,
        )
        aware_toml_path = _semantic_package_aware_toml_path(
            package_ref=package_ref,
            package_root=package_root,
        )
        package_spec = load_aware_toml_spec(toml_path=aware_toml_path)
        if _semantic_package_kind_value(package_spec) != "ontology":
            continue
        source_graph = (
            source_graphs_by_package_name.get(package_name)
            or source_graphs_by_fqn_prefix.get(package_graph.fqn_prefix)
            or package_graph
        )
        graph = _semantic_package_runtime_manifest_graph(
            source_graph=source_graph,
            runtime_graphs_by_fqn_prefix=runtime_graphs_by_fqn_prefix,
            package_runtime_graph=runtime_graphs_by_package_name.get(package_name),
            runtime_projection_graphs_by_ocg_id=runtime_projection_graphs_by_ocg_id,
            package_name=package_name,
        )
        for target in package_targets:
            materialized = materialize_object_config_graph_via_language_plugin(
                LanguagePluginMaterializationRequest(
                    source_graph=graph,
                    target_language_plugin_id=target.target_language_plugin_id,
                    external_runtime_graphs=_external_runtime_graphs_for_package(
                        runtime_graphs=runtime_graphs,
                        package_graph=graph,
                    ),
                    output_root=target.output_root,
                    import_root=target.import_root,
                    package_name=target.package_name,
                    renderer_profile=target.renderer_profile,
                    renderer_kind=target.renderer_kind,
                    materialization_source=target.materialization_source,
                    source_is_runtime=target.source_is_runtime,
                    stable_ids_import_root=target.stable_ids_import_root,
                    source_code_package_id=_uuid_or_none(
                        getattr(package_ref, "code_package_id", None)
                    ),
                    object_config_graph_package_id=_uuid_or_none(
                        getattr(package_ref, "object_config_graph_package_id", None)
                    ),
                    object_config_graph_commit_id=_uuid_or_none(
                        getattr(
                            package_ref,
                            "object_config_graph_object_instance_graph_commit_id",
                            None,
                        )
                    ),
                    emit_files=True,
                )
            )
            receipts.extend(
                dict(receipt.as_payload())
                for receipt in materialized.ownership_receipts
            )
    return tuple(receipts)


def _environment_language_materialization_targets_from_context(
    *,
    context: Mapping[str, object] | None,
    workspace_root: Path,
) -> tuple[_EnvironmentLanguageMaterializationTarget, ...]:
    if not isinstance(context, Mapping):
        return ()
    raw_targets = context.get(SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY)
    if not isinstance(raw_targets, (list, tuple)):
        return ()
    targets: list[_EnvironmentLanguageMaterializationTarget] = []
    for raw_target in raw_targets:
        if not isinstance(raw_target, Mapping):
            continue
        target = _environment_language_materialization_target_from_payload(
            payload=raw_target,
            workspace_root=workspace_root,
        )
        if target is not None:
            targets.append(target)
    return tuple(targets)


def _environment_language_materialization_target_from_payload(
    *,
    payload: Mapping[str, object],
    workspace_root: Path,
) -> _EnvironmentLanguageMaterializationTarget | None:
    target_language = _code_language_or_none(
        payload.get("target_language_plugin_id")
        or payload.get("target_language")
        or payload.get("language")
    )
    output_root = _target_output_root_from_payload(
        payload=payload,
        workspace_root=workspace_root,
    )
    import_root = _string_or_none(payload.get("import_root"))
    package_name = _string_or_none(payload.get("package_name"))
    materialization_source = _string_or_none(payload.get("materialization_source"))
    if (
        target_language is None
        or output_root is None
        or import_root is None
        or materialization_source is None
    ):
        return None
    return _EnvironmentLanguageMaterializationTarget(
        target_language_plugin_id=target_language,
        output_root=output_root,
        import_root=import_root,
        package_name=package_name or import_root,
        materialization_source=materialization_source,
        source_is_runtime=bool(payload.get("source_is_runtime")),
        renderer_profile=_string_or_none(payload.get("renderer_profile")),
        renderer_kind=_string_or_none(payload.get("renderer_kind")),
        stable_ids_import_root=_string_or_none(payload.get("stable_ids_import_root")),
    )


def _environment_language_target_matches_package(
    *,
    target: _EnvironmentLanguageMaterializationTarget,
    package_ref: object,
) -> bool:
    if target.materialization_source != "runtime_handlers":
        return False
    fqn_prefix = str(getattr(package_ref, "fqn_prefix", "") or "").strip()
    if not fqn_prefix:
        return False
    ontology_import_root = f"{fqn_prefix}_ontology"
    return (
        target.import_root == fqn_prefix
        or target.package_name == fqn_prefix
        or target.stable_ids_import_root == ontology_import_root
    )


def _code_language_or_none(value: object) -> CodeLanguage | None:
    raw_value = _string_or_none(value)
    if raw_value is None:
        return None
    try:
        return CodeLanguage(raw_value)
    except ValueError:
        return None


def _target_output_root_from_payload(
    *,
    payload: Mapping[str, object],
    workspace_root: Path,
) -> Path | None:
    raw_output_root = _string_or_none(payload.get("output_root"))
    if raw_output_root is None:
        return None
    output_root = Path(raw_output_root)
    return output_root if output_root.is_absolute() else workspace_root / output_root


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    text = _string_or_none(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _environment_runtime_artifact_ownership_receipts(
    *,
    result: object,
    workspace_root: Path,
    index: object,
    branch_id: object,
    context: Mapping[str, object] | None = None,
) -> tuple[dict[str, object], ...]:
    _ = (result, workspace_root, index, branch_id, context)
    return ()


def _runtime_projection_graphs_by_ocg_id_from_context(
    *,
    context: Mapping[str, object] | None,
) -> dict[str, tuple[ObjectProjectionGraph, ...]]:
    grouped: dict[str, list[ObjectProjectionGraph]] = {}
    for graph in _runtime_object_config_graphs_from_context(context):
        for projection_graph in tuple(graph.object_projection_graphs or ()):
            if not isinstance(projection_graph, ObjectProjectionGraph):
                continue
            ocg_id = str(
                getattr(projection_graph, "object_config_graph_id", "") or ""
            ).strip()
            if not ocg_id:
                continue
            grouped.setdefault(ocg_id, []).append(projection_graph)
    return {key: tuple(value) for key, value in grouped.items()}


def _runtime_object_config_graphs_with_projection_graphs(
    graphs: tuple[ObjectConfigGraph, ...],
    *,
    runtime_projection_graphs_by_ocg_id: Mapping[
        str,
        tuple[ObjectProjectionGraph, ...],
    ],
) -> tuple[ObjectConfigGraph, ...]:
    if not graphs or not runtime_projection_graphs_by_ocg_id:
        return graphs
    return tuple(
        _object_config_graph_with_projection_graphs(
            graph,
            runtime_projection_graphs_by_ocg_id=(runtime_projection_graphs_by_ocg_id),
        )
        for graph in graphs
    )


def _object_config_graphs_by_package_name_with_projection_graphs(
    graphs_by_package_name: Mapping[str, ObjectConfigGraph],
    *,
    runtime_projection_graphs_by_ocg_id: Mapping[
        str,
        tuple[ObjectProjectionGraph, ...],
    ],
) -> dict[str, ObjectConfigGraph]:
    if not graphs_by_package_name:
        return {}
    return {
        package_name: _object_config_graph_with_projection_graphs(
            graph,
            runtime_projection_graphs_by_ocg_id=(runtime_projection_graphs_by_ocg_id),
        )
        for package_name, graph in graphs_by_package_name.items()
    }


def _object_config_graph_with_projection_graphs(
    graph: ObjectConfigGraph,
    *,
    runtime_projection_graphs_by_ocg_id: Mapping[
        str,
        tuple[ObjectProjectionGraph, ...],
    ],
) -> ObjectConfigGraph:
    if graph.object_projection_graphs:
        return graph
    projection_graphs = runtime_projection_graphs_by_ocg_id.get(str(graph.id), ())
    if not projection_graphs:
        return graph
    graph_with_projection_graphs = graph.model_copy(deep=True)
    graph_with_projection_graphs.object_projection_graphs = list(projection_graphs)
    return graph_with_projection_graphs


def _semantic_package_runtime_manifest_graph(
    *,
    source_graph: ObjectConfigGraph,
    runtime_graphs_by_fqn_prefix: Mapping[str, ObjectConfigGraph],
    package_runtime_graph: ObjectConfigGraph | None = None,
    runtime_projection_graphs_by_ocg_id: Mapping[
        str,
        tuple[ObjectProjectionGraph, ...],
    ],
    package_name: str,
) -> ObjectConfigGraph:
    runtime_graph = package_runtime_graph or runtime_graphs_by_fqn_prefix.get(
        source_graph.fqn_prefix
    )
    projection_graphs = runtime_projection_graphs_by_ocg_id.get(
        str(source_graph.id), ()
    )
    if runtime_graph is not None:
        if (
            source_graph.object_projection_graph_declarations
            and not runtime_graph.object_projection_graphs
            and not projection_graphs
        ):
            raise RuntimeError(
                "Environment semantic runtime manifest refresh requires Meta runtime "
                "context OPGs for package " + package_name
            )
        graph = runtime_graph.model_copy(deep=True)
        if projection_graphs and not graph.object_projection_graphs:
            graph.object_projection_graphs = list(projection_graphs)
        return graph

    if source_graph.object_projection_graph_declarations and not projection_graphs:
        raise RuntimeError(
            "Environment semantic runtime manifest refresh requires Meta runtime "
            "context OPGs for package " + package_name
        )
    if not projection_graphs:
        return source_graph

    graph = source_graph.model_copy(deep=True)
    graph.object_projection_graphs = list(projection_graphs)
    return graph


def _external_runtime_graphs_for_package(
    *,
    runtime_graphs: tuple[ObjectConfigGraph, ...],
    package_graph: ObjectConfigGraph,
) -> tuple[ObjectConfigGraph, ...]:
    package_graph_id = getattr(package_graph, "id", None)
    if package_graph_id is None:
        return runtime_graphs
    return tuple(
        graph
        for graph in runtime_graphs
        if getattr(graph, "id", None) != package_graph_id
    )


def _runtime_object_config_graphs_from_context(
    context: Mapping[str, object] | None,
) -> tuple[ObjectConfigGraph, ...]:
    if not isinstance(context, Mapping):
        return ()
    direct_graphs = _object_config_graphs_from_context_value(
        context.get("runtime_object_config_graphs")
    )
    if direct_graphs:
        return direct_graphs
    return _object_config_graphs_from_meta_context_candidates(
        context=context,
        attribute_names=("runtime_object_config_graphs", "runtime_graphs"),
    )


def _source_object_config_graphs_from_context(
    context: Mapping[str, object] | None,
) -> tuple[ObjectConfigGraph, ...]:
    if not isinstance(context, Mapping):
        return ()
    direct_graphs = _object_config_graphs_from_context_value(
        context.get("semantic_object_config_graphs")
    )
    if direct_graphs:
        return direct_graphs
    return _object_config_graphs_from_meta_context_candidates(
        context=context,
        attribute_names=("semantic_object_config_graphs", "source_graphs"),
    )


def _runtime_object_config_graphs_by_fqn_prefix(
    graphs: tuple[ObjectConfigGraph, ...],
) -> dict[str, ObjectConfigGraph]:
    return {
        graph.fqn_prefix: graph
        for graph in graphs
        if isinstance(graph.fqn_prefix, str) and graph.fqn_prefix.strip()
    }


def _source_object_config_graphs_by_fqn_prefix(
    graphs: tuple[ObjectConfigGraph, ...],
) -> dict[str, ObjectConfigGraph]:
    return _runtime_object_config_graphs_by_fqn_prefix(graphs)


def _runtime_object_config_graphs_by_package_name_from_context(
    context: Mapping[str, object] | None,
) -> dict[str, ObjectConfigGraph]:
    if not isinstance(context, Mapping):
        return {}
    direct_graphs = _object_config_graphs_by_package_name_from_context_value(
        context.get("runtime_object_config_graphs_by_package_name")
    )
    if direct_graphs:
        return direct_graphs
    return _object_config_graphs_by_package_name_from_meta_context_candidates(
        context=context,
        attribute_names=(
            "runtime_object_config_graphs_by_package_name",
            "runtime_graph_by_package_name",
        ),
    )


def _source_object_config_graphs_by_package_name_from_context(
    context: Mapping[str, object] | None,
) -> dict[str, ObjectConfigGraph]:
    if not isinstance(context, Mapping):
        return {}
    graphs = _object_config_graphs_by_package_name_from_meta_context_candidates(
        context=context,
        attribute_names=(
            "semantic_object_config_graphs_by_package_name",
            "source_graph_by_package_name",
        ),
    )
    graphs.update(
        _object_config_graphs_by_package_name_from_context_value(
            context.get("semantic_object_config_graphs_by_package_name")
        )
    )
    package_name_by_graph_id = _completed_package_name_by_graph_id(context=context)
    for graph in _source_object_config_graphs_from_context(context):
        package_name = package_name_by_graph_id.get(graph.id)
        if package_name is not None:
            graphs[package_name] = graph
    return graphs


def _completed_package_name_by_graph_id(
    *,
    context: Mapping[str, object],
) -> dict[UUID, str]:
    raw_intents = context.get(SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY)
    if not isinstance(raw_intents, (list, tuple)):
        return {}
    package_name_by_graph_id: dict[UUID, str] = {}
    for evidence in raw_intents:
        if (
            not isinstance(evidence, Mapping)
            or _context_text(evidence.get("semantic_root_kind")) != "OntologyPackage"
        ):
            continue
        package_name = _context_text(
            evidence.get("package_key") or evidence.get("package_name")
        )
        if package_name is None:
            continue
        detail = _completed_semantic_package_detail(
            package_name=package_name,
            evidence=evidence,
        )
        graph_id = (
            _context_uuid(detail.get("object_config_graph_id"))
            if detail is not None
            else None
        )
        if graph_id is not None:
            package_name_by_graph_id[graph_id] = package_name
    return package_name_by_graph_id


def _completed_semantic_packages_by_package_name_from_context(
    *,
    context: Mapping[str, object] | None,
    workspace_root: Path,
) -> dict[str, "EnvironmentSemanticPackageMaterializationRef"]:
    from aware_environment.materialization.service import (
        EnvironmentSemanticPackageMaterializationRef,
    )

    if not isinstance(context, Mapping):
        return {}
    graphs_by_id = {
        graph.id: graph for graph in _source_object_config_graphs_from_context(context)
    }
    for graph in _source_object_config_graphs_by_package_name_from_context(
        context
    ).values():
        graphs_by_id[graph.id] = graph
    raw_intents = context.get(SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY)
    if not isinstance(raw_intents, (list, tuple)):
        return {}
    raw_completed_refs = context.get(
        _WORKSPACE_MATERIALIZED_SEMANTIC_PACKAGE_REFS_CONTEXT_KEY
    )
    if not isinstance(raw_completed_refs, (list, tuple)):
        return {}
    completed_authority_keys = frozenset(
        authority_key
        for raw_ref in raw_completed_refs
        if isinstance(raw_ref, Mapping)
        and (authority_key := _completed_semantic_package_authority_key(raw_ref))
        is not None
    )

    evidence_by_package: dict[str, dict[str, Mapping[str, object]]] = {}
    invalid_packages: set[str] = set()
    for raw_intent in raw_intents:
        if not isinstance(raw_intent, Mapping):
            continue
        authority_key = _completed_semantic_package_authority_key(raw_intent)
        if authority_key not in completed_authority_keys:
            continue
        provider_key = _context_text(
            raw_intent.get("semantic_contract_provider_key")
            or raw_intent.get("semantic_owner_module")
        )
        root_kind = _context_text(raw_intent.get("semantic_root_kind"))
        package_name = _context_text(
            raw_intent.get("package_key") or raw_intent.get("package_name")
        )
        if (
            provider_key != "aware_ontology"
            or root_kind not in {"OntologyConfig", "OntologyPackage"}
            or package_name is None
            or _context_uuid(raw_intent.get("semantic_branch_id")) is None
            or _context_uuid(raw_intent.get("semantic_head_commit_id")) is None
            or _context_uuid(raw_intent.get("semantic_object_instance_graph_commit_id"))
            is None
        ):
            continue
        package_evidence = evidence_by_package.setdefault(package_name, {})
        existing = package_evidence.get(root_kind)
        if existing is not None and dict(existing) != dict(raw_intent):
            invalid_packages.add(package_name)
            continue
        package_evidence[root_kind] = raw_intent

    completed: dict[str, "EnvironmentSemanticPackageMaterializationRef"] = {}
    for package_name, package_evidence in evidence_by_package.items():
        if package_name in invalid_packages:
            continue
        config_evidence = package_evidence.get("OntologyConfig")
        package_evidence_row = package_evidence.get("OntologyPackage")
        if config_evidence is None or package_evidence_row is None:
            continue
        detail = _completed_semantic_package_detail(
            package_name=package_name,
            evidence=package_evidence_row,
        )
        if detail is None:
            continue
        graph_id = _context_uuid(detail.get("object_config_graph_id"))
        graph = graphs_by_id.get(graph_id) if graph_id is not None else None
        branch_id = _context_uuid(package_evidence_row.get("semantic_branch_id"))
        if (
            graph is None
            or branch_id is None
            or branch_id != _context_uuid(config_evidence.get("semantic_branch_id"))
            or branch_id != _context_uuid(detail.get("semantic_branch_id"))
        ):
            continue
        try:
            completed[package_name] = EnvironmentSemanticPackageMaterializationRef(
                module_name=_required_context_text(detail, "module_name"),
                aware_toml_path=_context_workspace_path(
                    value=_required_context_text(detail, "aware_toml_path"),
                    workspace_root=workspace_root,
                ),
                ontology_manifest_path=_context_text(
                    detail.get("semantic_contract_manifest_relative_path")
                ),
                source_manifest_path=_required_context_text(
                    detail, "source_manifest_path"
                ),
                manifest_relative_path=_required_context_text(
                    detail, "manifest_relative_path"
                ),
                package_root=_required_context_text(detail, "package_root"),
                workspace_package_root=_required_context_text(
                    detail, "workspace_package_root"
                ),
                sources_root=_context_text(detail.get("sources_root")),
                package_name=package_name,
                fqn_prefix=_required_context_text(detail, "fqn_prefix"),
                semantic_branch_id=branch_id,
                code_package_id=_required_context_uuid(detail, "code_package_id"),
                code_package_object_instance_graph_commit_id=(
                    _required_context_uuid(
                        detail,
                        "code_package_object_instance_graph_commit_id",
                    )
                ),
                object_config_graph_package_id=_required_context_uuid(
                    detail, "object_config_graph_package_id"
                ),
                object_config_graph_id=graph.id,
                object_config_graph_hash=graph.hash,
                object_config_graph_head_commit_id=_required_context_uuid(
                    detail, "object_config_graph_head_commit_id"
                ),
                object_config_graph_package_object_instance_graph_commit_id=(
                    _required_context_uuid(
                        detail,
                        "object_config_graph_package_object_instance_graph_commit_id",
                    )
                ),
                object_config_graph_package_head_commit_id=_required_context_uuid(
                    detail, "object_config_graph_package_head_commit_id"
                ),
                object_config_graph_object_instance_graph_commit_id=(
                    _required_context_uuid(
                        detail,
                        "object_config_graph_object_instance_graph_commit_id",
                    )
                ),
                phase_timings_s={"completed_semantic_package_reuse": 0.0},
                code_package_build_runtime_telemetry={},
                code_package_build_invoke_perf_ms={},
                code_package_upsert_runtime_telemetry={},
                code_package_upsert_invoke_perf_ms={},
                semantic_commit_strategy="completed_semantic_package_reuse",
                semantic_commit_fallback_reset=False,
                semantic_commit_phase_timings_s={},
                code_package_head_commit_id=_required_context_uuid(
                    detail, "code_package_head_commit_id"
                ),
                ontology_config_id=_required_context_uuid(
                    config_evidence, "semantic_root_id"
                ),
                ontology_config_commit_id=_required_context_uuid(
                    detail, "ontology_config_commit_id"
                ),
                ontology_config_head_commit_id=_required_context_uuid(
                    config_evidence, "semantic_head_commit_id"
                ),
                ontology_config_object_instance_graph_commit_id=(
                    _required_context_uuid(
                        config_evidence,
                        "semantic_object_instance_graph_commit_id",
                    )
                ),
                ontology_package_id=_required_context_uuid(
                    package_evidence_row, "semantic_root_id"
                ),
                ontology_package_commit_id=_required_context_uuid(
                    detail, "ontology_package_commit_id"
                ),
                ontology_package_head_commit_id=_required_context_uuid(
                    package_evidence_row, "semantic_head_commit_id"
                ),
                ontology_package_object_instance_graph_commit_id=(
                    _required_context_uuid(
                        package_evidence_row,
                        "semantic_object_instance_graph_commit_id",
                    )
                ),
            )
        except (TypeError, ValueError):
            continue
    logger.info(
        "Environment completed semantic package context decoded: "
        "completed_ref_count=%s completed_authority_count=%s intent_count=%s "
        "decoded_package_count=%s",
        len(raw_completed_refs),
        len(completed_authority_keys),
        len(raw_intents),
        len(completed),
    )
    return completed


def _completed_semantic_package_authority_key(
    evidence: Mapping[str, object],
) -> tuple[str, ...] | None:
    provider_key = _context_text(
        evidence.get("semantic_contract_provider_key")
        or evidence.get("semantic_owner_module")
    )
    package_name = _context_text(
        evidence.get("package_key")
        or evidence.get("semantic_package_name")
        or evidence.get("package_name")
    )
    root_kind = _context_text(evidence.get("semantic_root_kind"))
    root_id = _context_uuid(evidence.get("semantic_root_id"))
    branch_id = _context_uuid(evidence.get("semantic_branch_id"))
    head_commit_id = _context_uuid(evidence.get("semantic_head_commit_id"))
    object_instance_graph_commit_id = _context_uuid(
        evidence.get("semantic_object_instance_graph_commit_id")
    )
    if (
        provider_key != "aware_ontology"
        or package_name is None
        or root_kind not in {"OntologyConfig", "OntologyPackage"}
        or root_id is None
        or branch_id is None
        or head_commit_id is None
        or object_instance_graph_commit_id is None
    ):
        return None
    return (
        provider_key,
        package_name,
        root_kind,
        str(root_id),
        str(branch_id),
        str(head_commit_id),
        str(object_instance_graph_commit_id),
    )


def _completed_semantic_package_detail(
    *,
    package_name: str,
    evidence: Mapping[str, object],
) -> Mapping[str, object] | None:
    raw_details = evidence.get("semantic_packages")
    if not isinstance(raw_details, (list, tuple)):
        return None
    matches = tuple(
        detail
        for detail in raw_details
        if isinstance(detail, Mapping)
        and _context_text(detail.get("package_name")) == package_name
    )
    return matches[0] if len(matches) == 1 else None


def _context_workspace_path(*, value: str, workspace_root: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (workspace_root / path).resolve()


def _context_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _required_context_text(payload: Mapping[str, object], key: str) -> str:
    value = _context_text(payload.get(key))
    if value is None:
        raise ValueError(f"Completed semantic package evidence is missing {key!r}.")
    return value


def _context_uuid(value: object) -> UUID | None:
    try:
        return UUID(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _required_context_uuid(payload: Mapping[str, object], key: str) -> UUID:
    value = _context_uuid(payload.get(key))
    if value is None:
        raise ValueError(f"Completed semantic package evidence is missing {key!r}.")
    return value


def _semantic_ontology_package_catalog_from_context(
    context: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    if not isinstance(context, Mapping):
        return None
    value = context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    return value if isinstance(value, Mapping) else None


def _object_config_graphs_from_meta_context_candidates(
    *,
    context: Mapping[str, object] | None,
    attribute_names: tuple[str, ...],
) -> tuple[ObjectConfigGraph, ...]:
    for candidate in _meta_runtime_context_candidates(context=context):
        for attribute_name in attribute_names:
            graphs = _object_config_graphs_from_context_value(
                getattr(candidate, attribute_name, None)
            )
            if graphs:
                return graphs
    return ()


def _object_config_graphs_by_package_name_from_meta_context_candidates(
    *,
    context: Mapping[str, object] | None,
    attribute_names: tuple[str, ...],
) -> dict[str, ObjectConfigGraph]:
    for candidate in _meta_runtime_context_candidates(context=context):
        for attribute_name in attribute_names:
            graphs = _object_config_graphs_by_package_name_from_context_value(
                getattr(candidate, attribute_name, None)
            )
            if graphs:
                return graphs
    return {}


def _object_config_graphs_by_package_name_from_context_value(
    value: object,
) -> dict[str, ObjectConfigGraph]:
    if not isinstance(value, Mapping):
        return {}
    return {
        key: graph
        for raw_key, graph in value.items()
        for key in (str(raw_key).strip(),)
        if key and isinstance(graph, ObjectConfigGraph)
    }


def _object_config_graphs_from_context_value(
    value: object,
) -> tuple[ObjectConfigGraph, ...]:
    if isinstance(value, ObjectConfigGraph):
        return (value,)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, ObjectConfigGraph))


def _semantic_object_config_graphs(result: object) -> tuple[ObjectConfigGraph, ...]:
    graphs = getattr(result, "semantic_object_config_graphs", None)
    if not isinstance(graphs, (list, tuple)):
        return ()
    return tuple(graph for graph in graphs if isinstance(graph, ObjectConfigGraph))


def _semantic_package_graph_pairs(
    *,
    semantic_packages: tuple[object, ...],
    semantic_graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[tuple[object, ObjectConfigGraph], ...]:
    if len(semantic_packages) != len(semantic_graphs):
        raise RuntimeError(
            "Environment semantic runtime manifest refresh requires one fresh "
            "ObjectConfigGraph per semantic package: "
            f"packages={len(semantic_packages)} graphs={len(semantic_graphs)}"
        )

    pairs: list[tuple[object, ObjectConfigGraph]] = []
    for package_ref, graph in zip(semantic_packages, semantic_graphs, strict=True):
        expected_graph_id = str(
            getattr(package_ref, "object_config_graph_id", "") or ""
        ).strip()
        actual_graph_id = str(getattr(graph, "id", "") or "").strip()
        if (
            expected_graph_id
            and actual_graph_id
            and expected_graph_id != actual_graph_id
        ):
            raise RuntimeError(
                "Environment semantic runtime manifest refresh graph identity "
                "mismatch for package "
                + _semantic_package_name(package_ref)
                + f": expected={expected_graph_id} actual={actual_graph_id}"
            )
        pairs.append((package_ref, graph))
    return tuple(pairs)


def _semantic_package_root(*, package_ref: object, workspace_root: Path) -> Path:
    workspace_package_root = str(
        getattr(package_ref, "workspace_package_root", "") or ""
    ).strip()
    if workspace_package_root:
        resolved = (workspace_root / workspace_package_root).resolve()
        if workspace_root.resolve() not in resolved.parents:
            raise RuntimeError(
                "Environment semantic runtime manifest refresh package root escapes "
                f"workspace: {resolved}"
            )
        return resolved

    module_name = str(getattr(package_ref, "module_name", "") or "").strip()
    package_root = str(getattr(package_ref, "package_root", "") or "").strip()
    if not module_name or not package_root:
        raise RuntimeError(
            "Environment semantic runtime manifest refresh requires module_name "
            "and package_root for package " + _semantic_package_name(package_ref)
        )
    resolved = (workspace_root / "modules" / module_name / package_root).resolve()
    if workspace_root.resolve() not in resolved.parents:
        raise RuntimeError(
            "Environment semantic runtime manifest refresh package root escapes "
            f"workspace: {resolved}"
        )
    return resolved


def _semantic_package_aware_toml_path(
    *,
    package_ref: object,
    package_root: Path,
) -> Path:
    aware_toml_path = _path_or_none(getattr(package_ref, "aware_toml_path", None))
    if aware_toml_path is None:
        return package_root / "aware.toml"
    if not aware_toml_path.is_absolute():
        return (package_root / aware_toml_path).resolve()
    return aware_toml_path.resolve()


def _semantic_package_kind_value(package_spec: object) -> str:
    package = getattr(package_spec, "package", None)
    kind = getattr(package, "kind", None)
    value = getattr(kind, "value", kind)
    return str(value or "").strip()


def _semantic_package_name(package_ref: object) -> str:
    name = str(getattr(package_ref, "package_name", "") or "").strip()
    return name or "unknown-package"


def _meta_runtime_context_candidates(
    *,
    context: Mapping[str, object] | None,
) -> tuple[object, ...]:
    if not isinstance(context, Mapping):
        return ()
    candidates: list[object] = []
    for key in (
        "provider_runtime_context",
        "aware_meta.graph_runtime_context",
        "meta_context",
    ):
        candidate = context.get(key)
        if candidate is None:
            continue
        candidates.append(candidate)
        nested = getattr(candidate, "meta_context", None)
        if nested is not None:
            candidates.append(nested)
    return tuple(candidates)


def _environment_module_names(result: object) -> tuple[str, ...]:
    names = _context_strings(getattr(result, "semantic_package_names", None))
    if names:
        return names
    names = _context_strings(getattr(result, "code_module_names", None))
    if names:
        return names
    return _context_strings(
        getattr(getattr(result, "environment_spec", None), "modules", None)
    )


def _path_or_none(value: object) -> Path | None:
    if isinstance(value, Path):
        return value
    if isinstance(value, str) and value.strip():
        return Path(value)
    return None


def _context_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
    *,
    fallback_keys: object = (),
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    semantic_keys = _context_strings(raw_keys)
    if semantic_keys:
        return semantic_keys
    return _context_strings(fallback_keys)


def _semantic_package_names_from_result(
    semantic_packages: tuple[object, ...],
    *,
    context: object,
    environment_handle: str,
) -> tuple[str, ...]:
    package_names = _context_strings(
        tuple(getattr(package, "package_name", "") for package in semantic_packages)
    )
    if package_names:
        return package_names
    if isinstance(context, Mapping):
        selected_package_names = _context_strings(
            context.get("environment_semantic_package_names")
        )
        if selected_package_names:
            return selected_package_names
    return _context_strings((environment_handle,))


def _context_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        normalized = value.strip()
        return (normalized,) if normalized else ()
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(
            dict.fromkeys(
                item for item in (str(raw_item).strip() for raw_item in value) if item
            )
        )
    return ()


__all__ = ["materialize"]
