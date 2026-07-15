from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_api_runtime.compile_materialization import (
    materialize_api_compile_plan_ontology,
)
from aware_meta_service.local_sdk import (
    MaterializationExecutionError,
    MaterializationLaneContext,
    MetaSdkLaneStore,
    build_local_meta_sdk_lane_store,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_service_runtime.implementation_package import (
    ServiceActivationRequiresMaterialization,
)
from aware_service_runtime.package_ref_resolution import (
    ResolvedServiceRuntimePackageRef,
)
from aware_service_runtime.runtime_resolution import (
    ServiceProtocolApiReferenceLaneInput,
    load_service_protocol_api_reference_lane_inputs,
    load_service_protocol_api_reference_lane_inputs_from_dependencies,
)
from aware_utils.logging import logger

from aware_service_service.api.reference_lanes import (
    api_reference_lane_for_branch_key,
    api_reference_repair_lane_for_incomplete_state,
    classify_service_protocol_api_reference_lane,
    record_service_protocol_api_reference_lane_head,
    remember_service_protocol_api_reference_lane,
)


def load_service_protocol_api_reference_materialization_inputs(
    *,
    toml_paths: tuple[Path, ...],
    committed_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...],
    kernel_repo_root: Path | None,
    artifact_root: Path | None,
    package_names: frozenset[str] | None = None,
    hydrate_accessible_graphs: bool = True,
) -> tuple[ServiceProtocolApiReferenceLaneInput, ...]:
    references: list[ServiceProtocolApiReferenceLaneInput] = []
    if toml_paths:
        references.extend(
            load_service_protocol_api_reference_lane_inputs(
                toml_paths=toml_paths,
                kernel_repo_root=kernel_repo_root,
                package_names=package_names,
                hydrate_accessible_graphs=hydrate_accessible_graphs,
            )
        )
    if committed_package_refs:
        if artifact_root is None:
            raise RuntimeError(
                "ServiceHostApp requires artifact.root when committed "
                "implementation package refs provide api_service_protocol dependencies."
            )
        references.extend(
            load_service_protocol_api_reference_lane_inputs_from_dependencies(
                dependencies=tuple(
                    dependency.to_payload()
                    for package_ref in committed_package_refs
                    for dependency in package_ref.dependencies
                ),
                repo_root=artifact_root,
                additional_repo_roots=(
                    (kernel_repo_root,) if kernel_repo_root is not None else ()
                ),
                package_names=package_names,
                hydrate_accessible_graphs=hydrate_accessible_graphs,
            )
        )
    return tuple(references)


async def materialize_service_protocol_api_reference_lanes(
    *,
    runtime: Any | None,
    index: Any,
    lane: MaterializationLaneContext,
    toml_paths: tuple[Path, ...],
    committed_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...] = (),
    kernel_repo_root: Path | None,
    artifact_root: Path | None,
    meta_lane_store: MetaSdkLaneStore,
    allow_materialization: bool = True,
) -> Mapping[str, UUID]:
    committed_reference_store = (
        FSCommitStore(root_dir=artifact_root)
        if committed_package_refs
        and not allow_materialization
        and artifact_root is not None
        else None
    )
    reference_lane_store = (
        build_local_meta_sdk_lane_store(commit_store=committed_reference_store)
        if committed_reference_store is not None
        else meta_lane_store
    )
    references = list(
        load_service_protocol_api_reference_materialization_inputs(
            toml_paths=toml_paths,
            committed_package_refs=committed_package_refs,
            kernel_repo_root=kernel_repo_root,
            artifact_root=artifact_root,
            hydrate_accessible_graphs=False,
        )
    )
    if not references:
        return {}

    api_branch_ids_by_name: dict[str, UUID] = {}
    materialization_references_by_branch_key: dict[
        str, ServiceProtocolApiReferenceLaneInput
    ] = {}

    def _reference_with_accessible_graphs(
        reference: ServiceProtocolApiReferenceLaneInput,
    ) -> ServiceProtocolApiReferenceLaneInput:
        if reference.accessible_graphs:
            return reference
        materialization_reference = materialization_references_by_branch_key.get(
            reference.branch_key
        )
        if materialization_reference is None:
            for (
                loaded_reference
            ) in load_service_protocol_api_reference_materialization_inputs(
                toml_paths=toml_paths,
                committed_package_refs=committed_package_refs,
                kernel_repo_root=kernel_repo_root,
                artifact_root=artifact_root,
                package_names=frozenset({reference.package_name}),
            ):
                materialization_references_by_branch_key.setdefault(
                    loaded_reference.branch_key,
                    loaded_reference,
                )
            materialization_reference = materialization_references_by_branch_key.get(
                reference.branch_key
            )
        if materialization_reference is None:
            raise RuntimeError(
                "Service host could not load accessible graphs for "
                "service-protocol API reference materialization: "
                f"api={reference.api_name!r} branch_key={reference.branch_key!r}"
            )
        return materialization_reference

    for reference in references:
        classification_reference = (
            _reference_with_accessible_graphs(reference)
            if reference.projection_refs
            else reference
        )
        api_lane = api_reference_lane_for_branch_key(
            lane=lane,
            branch_key=reference.branch_key,
        )
        lane_state = await classify_service_protocol_api_reference_lane(
            index=index,
            lane=api_lane,
            reference=classification_reference,
            meta_lane_store=reference_lane_store,
            commit_store=committed_reference_store,
        )
        if lane_state.head_commit_id is not None:
            record_service_protocol_api_reference_lane_head(
                lane_state=lane_state,
                reason="reuse_candidate",
            )
        if lane_state.state == "complete":
            logger.info(
                "Service host reused committed service-protocol API reference lane "
                "api=%s branch_id=%s head_commit_id=%s",
                reference.api_name,
                api_lane.branch_id,
                lane_state.head_commit_id,
            )
            remember_service_protocol_api_reference_lane(
                api_branch_ids_by_name=api_branch_ids_by_name,
                reference=reference,
                lane=api_lane,
            )
            continue
        if lane_state.state != "empty":
            logger.warning(
                "Service host found an incomplete service-protocol API reference lane. "
                "Superseding it with a deterministic repair lane instead of rerunning "
                "constructors over a non-empty lane. api=%s branch_id=%s "
                "head_commit_id=%s error=%s",
                reference.api_name,
                api_lane.branch_id,
                lane_state.head_commit_id,
                lane_state.error,
            )
            api_lane = api_reference_repair_lane_for_incomplete_state(
                lane=lane,
                reference=reference,
                lane_state=lane_state,
            )
            lane_state = await classify_service_protocol_api_reference_lane(
                index=index,
                lane=api_lane,
                reference=classification_reference,
                meta_lane_store=reference_lane_store,
                commit_store=committed_reference_store,
            )
            if lane_state.head_commit_id is not None:
                record_service_protocol_api_reference_lane_head(
                    lane_state=lane_state,
                    reason="repair_reuse_candidate",
                )
            if lane_state.state == "complete":
                logger.info(
                    "Service host reused repaired service-protocol API reference lane "
                    "api=%s branch_id=%s head_commit_id=%s",
                    reference.api_name,
                    api_lane.branch_id,
                    lane_state.head_commit_id,
                )
                remember_service_protocol_api_reference_lane(
                    api_branch_ids_by_name=api_branch_ids_by_name,
                    reference=reference,
                    lane=api_lane,
                )
                continue
            if lane_state.state != "empty":
                raise RuntimeError(
                    "Service host found an incomplete service-protocol API reference repair lane. "
                    "Refusing to rerun constructor materialization over a non-empty lane; "
                    "the lane must be recovered from committed state or superseded by a new "
                    "content-addressed compile-plan hash. "
                    f"api={reference.api_name!r} branch_id={api_lane.branch_id} "
                    f"head_commit_id={lane_state.head_commit_id} error={lane_state.error!r}"
                )

        remember_service_protocol_api_reference_lane(
            api_branch_ids_by_name=api_branch_ids_by_name,
            reference=reference,
            lane=api_lane,
        )

        if not allow_materialization:
            raise ServiceActivationRequiresMaterialization(
                "ServiceHost activation requires service-protocol API "
                "reference lane materialization before it can use "
                "read-only committed package-ref activation: "
                f"api={reference.api_name!r} branch_id={api_lane.branch_id} "
                f"projection_hash={api_lane.projection_hash} "
                f"state={lane_state.state!r}."
            )

        try:
            materialization_reference = _reference_with_accessible_graphs(reference)
            logger.info(
                "Service host materializing service-protocol API reference lane "
                "api=%s branch_id=%s accessible_graphs=%s",
                materialization_reference.api_name,
                api_lane.branch_id,
                tuple(
                    graph.name for graph in materialization_reference.accessible_graphs
                ),
            )
            _ = await materialize_api_compile_plan_ontology(
                runtime=runtime,
                index=index,
                actor_id=None,
                lane=api_lane,
                compile_plan_payloads=(materialization_reference.compile_plan_payload,),
                accessible_graphs=materialization_reference.accessible_graphs,
            )
        except MaterializationExecutionError as exc:
            lane_state = await classify_service_protocol_api_reference_lane(
                index=index,
                lane=api_lane,
                reference=classification_reference,
                meta_lane_store=reference_lane_store,
                commit_store=committed_reference_store,
            )
            if lane_state.head_commit_id is not None:
                record_service_protocol_api_reference_lane_head(
                    lane_state=lane_state,
                    reason="post_commit_recovery",
                )
            if lane_state.state == "complete":
                logger.warning(
                    "Service host recovered service-protocol API reference lane after "
                    "materialization raised post-commit. api=%s branch_id=%s "
                    "head_commit_id=%s error=%s",
                    reference.api_name,
                    api_lane.branch_id,
                    lane_state.head_commit_id,
                    exc,
                )
                continue
            raise

        lane_state = await classify_service_protocol_api_reference_lane(
            index=index,
            lane=api_lane,
            reference=classification_reference,
            meta_lane_store=reference_lane_store,
            commit_store=committed_reference_store,
        )
        if lane_state.head_commit_id is not None:
            record_service_protocol_api_reference_lane_head(
                lane_state=lane_state,
                reason="materialized",
            )
        if lane_state.state != "complete":
            raise RuntimeError(
                "Service host could not commit required service-protocol API refs "
                f"on the host boot lane: api={reference.api_name!r} "
                f"branch_id={api_lane.branch_id} "
                f"endpoints={sorted(reference.endpoint_refs)} "
                f"state={lane_state.state!r} error={lane_state.error!r}"
            )

    return api_branch_ids_by_name


__all__ = [
    "load_service_protocol_api_reference_materialization_inputs",
    "materialize_service_protocol_api_reference_lanes",
]
