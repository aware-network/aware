from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationEmittedPackageOutput,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_api_runtime.compile_materialization import (
    materialize_api_compile_plan_ontology,
)
from aware_service_runtime.semantic_contract import (
    SERVICE_OWNED_OCG_PACKAGE_OUTPUT_KEY,
    SERVICE_OWNED_OCG_PACKAGE_PRODUCER_KEY,
    SERVICE_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION,
    SERVICE_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY,
    SERVICE_PROVIDER_OWNER,
)
from aware_service_runtime.materialization import (
    ServicePackageMaterializationResult,
    materialize_service_package_from_manifest,
    resolve_service_package_dependency_payloads,
)
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.runtime_resolution import (
    load_service_protocol_api_reference_lane_inputs_from_dependencies,
    service_protocol_api_reference_branch_id,
)

_FULL_REBUILD_FALLBACK_REASON = (
    "Service provider has not implemented delta materialization yet; "
    "replayed the full Service package manifest."
)


@dataclass(frozen=True, slots=True)
class _ServiceProtocolApiReferenceLaneMaterialization:
    branch_ids_by_api_name: dict[str, UUID]
    accessible_graphs: tuple[ObjectConfigGraph, ...]
    committed_lanes: tuple["_ServiceProtocolApiReferenceCommittedLane", ...] = ()


@dataclass(frozen=True, slots=True)
class _ServiceProtocolApiReferenceCommittedLane:
    package_name: str
    api_name: str
    branch_id: UUID
    projection_hash: str
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    root_source_object_id: UUID


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    api_reference_branch_ids_by_api_name = _api_reference_branch_ids_for_request(
        request=request,
    )
    service_protocol_api_references = (
        await _materialize_service_protocol_api_reference_lanes(request=request)
    )
    api_reference_branch_ids_by_api_name = _merge_api_reference_branch_ids(
        base=api_reference_branch_ids_by_api_name,
        candidate=service_protocol_api_references.branch_ids_by_api_name,
    )
    result = await materialize_service_package_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        service_toml_path=request.manifest_path,
        api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        api_reference_commit_store_roots_by_api_name=(
            _api_reference_commit_store_roots_for_request(request=request)
        ),
        api_reference_accessible_graphs=(
            service_protocol_api_references.accessible_graphs
        ),
        experience_reference_branch_ids_by_experience_name=_uuid_mapping(
            request.context.get("experience_reference_branch_ids_by_experience_name")
        ),
        price_reference_branch_ids_by_package_name=(
            _economy_price_reference_branch_ids_for_request(request=request)
        ),
    )
    return SemanticPackageMaterializationResult(
        details={
            "service_toml_path": result.service_toml_path.as_posix(),
            "service_name": result.service_config.name,
            "service_config_id": str(result.service_config.id),
            "service_package_name": result.service_package.name,
            "service_package_id": str(result.service_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_code_package_id": (
                str(result.source_code_package_id)
                if result.source_code_package_id is not None
                else None
            ),
            "implementation_code_package_ids": [
                str(item) for item in result.implementation_code_package_ids
            ],
            "implementation_code_packages": [
                {
                    key: str(value) if isinstance(value, UUID) else value
                    for key, value in item.items()
                }
                for item in result.implementation_code_package_refs
            ],
            "object_config_graph_packages": [
                {
                    "manifest_path": package.manifest_path.as_posix(),
                    "manifest_relative_path": package.manifest_relative_path,
                    "role": package.role,
                    "package_name": package.package_name,
                    "package_fqn_prefix": package.package_fqn_prefix,
                    "package_kind": package.package_kind,
                    "code_package_surface": "structure",
                    "object_config_graph_package_id": str(
                        package.object_config_graph_package_id
                    ),
                    "object_config_graph_id": str(package.object_config_graph_id),
                    "package_branch_id": (
                        str(package.package_branch_id)
                        if package.package_branch_id is not None
                        else None
                    ),
                    "source_code_package_id": (
                        str(package.source_code_package_id)
                        if package.source_code_package_id is not None
                        else None
                    ),
                    "object_config_graph_package_head_commit_id": (
                        str(package.object_config_graph_package_head_commit_id)
                        if package.object_config_graph_package_head_commit_id
                        is not None
                        else None
                    ),
                    "object_config_graph_package_object_instance_graph_commit_id": (
                        str(
                            package.object_config_graph_package_object_instance_graph_commit_id
                        )
                        if package.object_config_graph_package_object_instance_graph_commit_id
                        is not None
                        else None
                    ),
                    "object_config_graph_object_instance_graph_commit_id": (
                        str(package.object_config_graph_object_instance_graph_commit_id)
                        if package.object_config_graph_object_instance_graph_commit_id
                        is not None
                        else None
                    ),
                    **_language_materialization_targets_details(package),
                }
                for package in getattr(result, "object_config_graph_packages", ())
            ],
            "emitted_owned_object_config_graph_package_count": len(
                getattr(result, "object_config_graph_packages", ())
            ),
            "api_provider_sets": [
                {
                    key: str(value) if isinstance(value, UUID) else value
                    for key, value in item.items()
                }
                for item in result.api_provider_set_refs
            ],
            "api_provider_set_commit_id": (
                str(result.api_provider_set_commit_id)
                if result.api_provider_set_commit_id is not None
                else None
            ),
            "api_provider_set_head_commit_id": (
                str(result.api_provider_set_head_commit_id)
                if result.api_provider_set_head_commit_id is not None
                else None
            ),
            "service_source_path": result.service_source_path,
            "source_files": list(result.source_files),
            "service_phase_timings_s": dict(result.phase_timings_s),
            "service_commit_id": (
                str(result.definition_commit_id)
                if result.definition_commit_id is not None
                else None
            ),
            "service_config_object_instance_graph_commit_id": (
                str(result.service_config_object_instance_graph_commit_id)
                if result.service_config_object_instance_graph_commit_id is not None
                else None
            ),
            "service_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "service_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
            "service_package_object_instance_graph_commit_id": (
                str(result.package_object_instance_graph_commit_id)
                if result.package_object_instance_graph_commit_id is not None
                else None
            ),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.service_package.name,
                manifest_toml_path=result.service_toml_path,
                semantic_package_id=result.service_package.id,
                semantic_root_id=result.service_config.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    result.package_object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    result.service_config_object_instance_graph_commit_id
                ),
                semantic_root_kind="service_config",
                source_code_package_id=result.source_code_package_id,
                runtime_code_package_refs=_runtime_code_package_refs(
                    result.implementation_code_package_refs
                ),
                implementation_code_packages=result.implementation_code_package_refs,
                api_provider_sets=result.api_provider_set_refs,
            ),
            *_service_protocol_api_reference_bundles(
                service_package_name=result.service_package.name,
                manifest_toml_path=result.service_toml_path,
                source_code_package_id=result.source_code_package_id,
                committed_lanes=service_protocol_api_references.committed_lanes,
            ),
            *_service_activation_lane_bundles(result=result),
        ),
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(
            request,
            fallback_keys=(result.service_package.name,),
        ),
        applied_semantic_keys=_semantic_keys_from_request(
            request,
            fallback_keys=(result.service_package.name,),
        ),
        skipped_semantic_keys=(),
        stale_semantic_keys=(),
        emitted_package_outputs=_owned_object_config_graph_package_outputs(
            result=result
        ),
        fallback_reason=_FULL_REBUILD_FALLBACK_REASON,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
    )


async def materialize_delta(request: object) -> object:
    raise NotImplementedError(
        "Service provider delta materialization is declared for adapter "
        "preflight only; Workspace execution remains unwired."
    )


async def _materialize_service_protocol_api_reference_lanes(
    *,
    request: SemanticPackageMaterializationRequest,
) -> _ServiceProtocolApiReferenceLaneMaterialization:
    manifest_spec = load_aware_service_toml_spec(toml_path=request.manifest_path)
    dependencies = resolve_service_package_dependency_payloads(
        spec=manifest_spec,
        workspace_root=request.workspace_root,
    )
    references = load_service_protocol_api_reference_lane_inputs_from_dependencies(
        dependencies=dependencies,
        repo_root=request.workspace_root,
        require_relational_lock=False,
    )
    if not references:
        return _ServiceProtocolApiReferenceLaneMaterialization(
            branch_ids_by_api_name={},
            accessible_graphs=(),
        )

    api_projection_hash = find_meta_graph_projection_hash_by_name(
        index=request.index,
        projection_name="Api",
    )
    base_lane = MaterializationLaneContext(
        branch_id=request.branch_id,
        projection_hash=api_projection_hash,
    )
    branch_ids_by_api_name: dict[str, UUID] = {}
    committed_lanes: list[_ServiceProtocolApiReferenceCommittedLane] = []
    for reference in references:
        lane = _api_reference_lane_for_branch_key(
            lane=base_lane,
            branch_key=reference.branch_key,
        )
        _remember_service_protocol_api_reference_lane(
            api_branch_ids_by_name=branch_ids_by_api_name,
            api_name=reference.api_name,
            lane=lane,
        )
        target_head = await _materialization_lane_head(lane=lane)
        if target_head is None:
            await materialize_api_compile_plan_ontology(
                runtime=request.runtime,
                index=request.index,
                actor_id=request.actor_id,
                lane=lane,
                compile_plan_payloads=(reference.compile_plan_payload,),
                accessible_graphs=reference.accessible_graphs,
            )
            target_head = await _materialization_lane_head(lane=lane)
        committed_lanes.append(
            await _service_protocol_api_reference_committed_lane(
                package_name=reference.package_name,
                api_name=reference.api_name,
                lane=lane,
                target_head=target_head,
            )
        )
    return _ServiceProtocolApiReferenceLaneMaterialization(
        branch_ids_by_api_name=branch_ids_by_api_name,
        accessible_graphs=_dedupe_service_protocol_accessible_graphs(references),
        committed_lanes=tuple(committed_lanes),
    )


def _api_reference_lane_for_branch_key(
    *,
    lane: MaterializationLaneContext,
    branch_key: str,
) -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=service_protocol_api_reference_branch_id(branch_key),
        projection_hash=lane.projection_hash,
    )


def _remember_service_protocol_api_reference_lane(
    *,
    api_branch_ids_by_name: dict[str, UUID],
    api_name: str,
    lane: MaterializationLaneContext,
) -> None:
    existing = api_branch_ids_by_name.get(api_name)
    if existing is not None and existing != lane.branch_id:
        raise RuntimeError(
            "Service workspace provider found conflicting service-protocol API refs "
            f"for api={api_name!r}."
        )
    api_branch_ids_by_name[api_name] = lane.branch_id
    api_branch_ids_by_name[api_name.casefold()] = lane.branch_id


def _dedupe_service_protocol_accessible_graphs(
    references: tuple[object, ...],
) -> tuple[ObjectConfigGraph, ...]:
    graphs_by_key: dict[object, ObjectConfigGraph] = {}
    for reference in references:
        for graph in getattr(reference, "accessible_graphs", ()) or ():
            graph_id = getattr(graph, "id", None)
            key = (
                str(graph_id)
                if graph_id is not None
                else (
                    getattr(graph, "fqn_prefix", None),
                    getattr(graph, "name", None),
                    id(graph),
                )
            )
            if key not in graphs_by_key:
                graphs_by_key[key] = cast(ObjectConfigGraph, graph)
    return tuple(graphs_by_key.values())


def _merge_api_reference_branch_ids(
    *,
    base: dict[str, UUID],
    candidate: dict[str, UUID],
) -> dict[str, UUID]:
    merged = dict(base)
    for api_name, branch_id in candidate.items():
        # The candidate lane is materialized from the dependency's current,
        # content-addressed protocol inputs in this provider invocation. A
        # preflight mapping can describe an older Workspace receipt and must
        # not shadow that fresh committed replica.
        merged[api_name] = branch_id
    return merged


async def _materialization_lane_head(
    *,
    lane: MaterializationLaneContext,
) -> Mapping[str, object] | None:
    target_head = await FSCommitStore().head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return None
    return target_head


async def _service_protocol_api_reference_committed_lane(
    *,
    package_name: str,
    api_name: str,
    lane: MaterializationLaneContext,
    target_head: Mapping[str, object] | None,
) -> _ServiceProtocolApiReferenceCommittedLane:
    if target_head is None:
        raise RuntimeError(
            "Service workspace provider API reference materialization produced "
            f"no committed HEAD for package={package_name!r} api={api_name!r}."
        )
    head_commit_id = UUID(str(target_head["commit_id"]))
    envelope = await FSCommitStore().get_commit_envelope(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        commit_id=head_commit_id,
    )
    if envelope is None:
        raise RuntimeError(
            "Service workspace provider API reference materialization produced "
            "a HEAD without a committed envelope: "
            f"package={package_name!r} api={api_name!r} "
            f"head_commit_id={head_commit_id}."
        )
    return _ServiceProtocolApiReferenceCommittedLane(
        package_name=package_name,
        api_name=api_name,
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        head_commit_id=head_commit_id,
        object_instance_graph_commit_id=envelope.object_instance_graph_commit_id,
        root_source_object_id=envelope.root_source_object_id,
    )


def _service_protocol_api_reference_bundles(
    *,
    service_package_name: str,
    manifest_toml_path: Path,
    source_code_package_id: UUID | None,
    committed_lanes: tuple[_ServiceProtocolApiReferenceCommittedLane, ...],
) -> tuple[SemanticPackageMaterializationBundle, ...]:
    return tuple(
        SemanticPackageMaterializationBundle(
            package_key=(
                f"{service_package_name}:api-reference:"
                f"{lane.package_name}:{lane.api_name}"
            ),
            manifest_toml_path=manifest_toml_path,
            semantic_package_id=lane.root_source_object_id,
            semantic_root_id=lane.root_source_object_id,
            semantic_branch_id=lane.branch_id,
            semantic_head_commit_id=lane.head_commit_id,
            semantic_object_instance_graph_commit_id=(
                lane.object_instance_graph_commit_id
            ),
            semantic_root_object_instance_graph_commit_id=(
                lane.object_instance_graph_commit_id
            ),
            semantic_root_kind="service_protocol_api_reference",
            semantic_projection_name="Api",
            semantic_projection_hash=lane.projection_hash,
            source_code_package_id=source_code_package_id,
        )
        for lane in committed_lanes
    )


def _service_activation_lane_bundles(
    *,
    result: ServicePackageMaterializationResult,
) -> tuple[SemanticPackageMaterializationBundle, ...]:
    bundles: list[SemanticPackageMaterializationBundle] = []
    for lane in getattr(result, "activation_lanes", ()):
        bundles.extend(
            (
                SemanticPackageMaterializationBundle(
                    package_key=(
                        f"{result.service_package.name}:activation:"
                        f"service-config:{lane.service_name}"
                    ),
                    manifest_toml_path=result.service_toml_path,
                    semantic_package_id=lane.service_config_id,
                    semantic_root_id=lane.service_config_id,
                    semantic_branch_id=lane.service_config_branch_id,
                    semantic_head_commit_id=lane.service_config_head_commit_id,
                    semantic_object_instance_graph_commit_id=(
                        lane.service_config_object_instance_graph_commit_id
                    ),
                    semantic_root_object_instance_graph_commit_id=(
                        lane.service_config_object_instance_graph_commit_id
                    ),
                    semantic_root_kind="service_activation_config",
                    semantic_projection_name="ServiceConfig",
                    semantic_projection_hash=lane.service_config_projection_hash,
                    source_code_package_id=result.source_code_package_id,
                ),
                SemanticPackageMaterializationBundle(
                    package_key=(
                        f"{result.service_package.name}:activation:"
                        f"service:{lane.service_name}"
                    ),
                    manifest_toml_path=result.service_toml_path,
                    semantic_package_id=lane.service_id,
                    semantic_root_id=lane.service_id,
                    semantic_branch_id=lane.service_branch_id,
                    semantic_head_commit_id=lane.service_head_commit_id,
                    semantic_object_instance_graph_commit_id=(
                        lane.service_object_instance_graph_commit_id
                    ),
                    semantic_root_object_instance_graph_commit_id=(
                        lane.service_object_instance_graph_commit_id
                    ),
                    semantic_root_kind="service_activation_instance",
                    semantic_projection_name="Service",
                    semantic_projection_hash=lane.service_projection_hash,
                    source_code_package_id=result.source_code_package_id,
                ),
            )
        )
    return tuple(bundles)


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
    *,
    fallback_keys: object = (),
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    semantic_keys = _normalized_strings(raw_keys)
    if semantic_keys:
        return semantic_keys
    return _normalized_strings(fallback_keys)


def _runtime_code_package_refs(
    implementation_code_package_refs: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    refs: list[dict[str, object]] = []
    for implementation_ref in implementation_code_package_refs:
        source_code_package_id = implementation_ref.get("code_package_id")
        if source_code_package_id is None:
            continue
        refs.append(
            {
                "role": "service_implementation_package",
                "source_code_package_id": source_code_package_id,
                "source_object_instance_graph_commit_id": (
                    implementation_ref.get("object_instance_graph_commit_id")
                ),
                "package_name": implementation_ref.get("package_name"),
                "manifest_relative_path": implementation_ref.get(
                    "manifest_relative_path"
                ),
                "package_root": implementation_ref.get("package_root"),
                "sources_root": implementation_ref.get("sources_root"),
                "language": implementation_ref.get("language"),
            }
        )
    return tuple(refs)


def _owned_object_config_graph_package_outputs(
    *,
    result: ServicePackageMaterializationResult,
) -> tuple[SemanticPackageMaterializationEmittedPackageOutput, ...]:
    source_manifest_path = _relative_or_posix(
        path=result.service_toml_path,
        root=result.workspace_root,
    )
    outputs: list[SemanticPackageMaterializationEmittedPackageOutput] = []
    for package in getattr(result, "object_config_graph_packages", ()):
        package_root = _package_root_from_manifest_relative_path(
            package.manifest_relative_path
        )
        payload: dict[str, object] = {
            "aware_toml_path": package.manifest_path.as_posix(),
            "fqn_prefix": package.package_fqn_prefix,
            "manifest_kind": "aware_toml",
            "manifest_relative_path": package.manifest_relative_path,
            "package_kind": package.package_kind,
            "code_package_surface": "structure",
            "package_name": package.package_name,
            "package_root": package_root,
            "role": package.role,
        }
        language_targets = _language_materialization_targets(package)
        if language_targets:
            payload["language_materialization_targets"] = [
                dict(target) for target in language_targets
            ]
        if (
            package.object_config_graph_package_object_instance_graph_commit_id
            is not None
        ):
            payload["object_instance_graph_commit_id"] = str(
                package.object_config_graph_package_object_instance_graph_commit_id
            )
        outputs.append(
            SemanticPackageMaterializationEmittedPackageOutput(
                producer_provider_key="aware_service",
                producer_semantic_owner=SERVICE_PROVIDER_OWNER,
                producer_key=SERVICE_OWNED_OCG_PACKAGE_PRODUCER_KEY,
                output_key=SERVICE_OWNED_OCG_PACKAGE_OUTPUT_KEY,
                target_provider_key="aware_meta",
                target_semantic_owner="aware_meta.object_config_graph",
                target_input_key=SERVICE_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY,
                target_package_family="meta",
                target_semantic_kind="object_config_graph_package",
                package_key=package.package_name,
                input_artifact_family="aware_toml_manifest",
                input_artifact_path=package.manifest_path,
                input_artifact_payload=payload,
                runtime_contract_version=(
                    SERVICE_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION
                ),
                source_package_key=result.service_package.name,
                source_manifest_path=source_manifest_path,
                provider_payload={
                    "schema_version": 1,
                    "source": "service.object_config_graph_packages",
                    "role": package.role,
                },
            )
        )
    return tuple(outputs)


def _language_materialization_targets(package: object) -> tuple[dict[str, object], ...]:
    raw_targets = getattr(package, "language_materialization_targets", ()) or ()
    return tuple(dict(target) for target in raw_targets)


def _language_materialization_targets_details(package: object) -> dict[str, object]:
    targets = _language_materialization_targets(package)
    if not targets:
        return {}
    return {"language_materialization_targets": [dict(target) for target in targets]}


def _package_root_from_manifest_relative_path(manifest_relative_path: str) -> str:
    package_root = Path(manifest_relative_path).parent.as_posix()
    return "." if package_root == "." else package_root


def _relative_or_posix(*, path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalized_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        normalized = value.strip()
        return (normalized,) if normalized else ()
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(
            sorted(
                {item for item in (str(raw_item).strip() for raw_item in value) if item}
            )
        )
    return ()


def _api_reference_branch_ids_for_request(
    *,
    request: SemanticPackageMaterializationRequest,
) -> dict[str, UUID]:
    execution_context_value = (
        request.execution_context.get(
            "api_reference_branch_ids_by_api_name",
            provider_key="aware_service",
        )
        if request.execution_context is not None
        else None
    )
    api_reference_branch_ids_by_api_name = _uuid_mapping(execution_context_value)
    if api_reference_branch_ids_by_api_name:
        return api_reference_branch_ids_by_api_name
    return _uuid_mapping(request.context.get("api_reference_branch_ids_by_api_name"))


def _api_reference_commit_store_roots_for_request(
    *,
    request: SemanticPackageMaterializationRequest,
) -> dict[str, Path]:
    raw_entries = request.context.get("workspace_dependency_semantic_package_entries")
    if not isinstance(raw_entries, (list, tuple)):
        return {}
    roots_by_package_name: dict[str, Path] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            continue
        package_name = str(raw_entry.get("code_package_name") or "").strip()
        raw_owner_root = raw_entry.get("owner_workspace_root")
        if (
            not package_name
            or not isinstance(raw_owner_root, str)
            or not raw_owner_root.strip()
        ):
            continue
        owner_root = Path(raw_owner_root).expanduser()
        if not owner_root.is_absolute():
            raise RuntimeError(
                "Service dependency API owner workspace root must be absolute: "
                f"package_name={package_name!r}"
            )
        resolved_root = owner_root.resolve()
        existing = roots_by_package_name.get(package_name)
        if existing is not None and existing != resolved_root:
            raise RuntimeError(
                "Service dependency API package has conflicting owner roots: "
                f"package_name={package_name!r}"
            )
        roots_by_package_name[package_name] = resolved_root
    return roots_by_package_name


def _uuid_mapping(value: object) -> dict[str, UUID]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): cast(UUID, item)
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, UUID)
    }


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value.strip())
    return None


def _economy_price_reference_branch_ids_for_request(
    *,
    request: SemanticPackageMaterializationRequest,
) -> dict[str, UUID]:
    manifest = load_aware_service_toml_spec(toml_path=request.manifest_path)
    package_dependency_names = {
        dependency.package_name.strip()
        for dependency in manifest.dependencies
        if dependency.kind.value == "package" and dependency.package_name.strip()
    }
    raw_refs = request.context.get("workspace_materialized_semantic_package_refs")
    if not isinstance(raw_refs, (list, tuple)):
        return {}

    resolved: dict[str, UUID] = {}
    for raw_ref in raw_refs:
        if not isinstance(raw_ref, Mapping):
            continue
        family = str(raw_ref.get("semantic_package_family") or "").strip()
        if family != "economy":
            continue
        package_name = str(
            raw_ref.get("package_key") or raw_ref.get("semantic_package_name") or ""
        ).strip()
        if package_name not in package_dependency_names:
            continue
        head_commit_id = str(raw_ref.get("semantic_head_commit_id") or "").strip()
        branch_id = _uuid_or_none(raw_ref.get("semantic_branch_id"))
        if not head_commit_id or branch_id is None:
            raise RuntimeError(
                "Service Economy price dependency lacks committed semantic bundle authority: "
                f"package_name={package_name!r}"
            )
        existing = resolved.get(package_name)
        if existing is not None and existing != branch_id:
            raise RuntimeError(
                "Service Economy price dependency resolved conflicting semantic branches: "
                f"package_name={package_name!r} branches={[str(existing), str(branch_id)]!r}"
            )
        resolved[package_name] = branch_id
    return resolved


__all__ = ["materialize", "materialize_delta"]
