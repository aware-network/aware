from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, cast
from uuid import UUID

from aware_meta_service.local_sdk import read_local_meta_runtime_read_model
from aware_service_runtime.implementation_package import (
    ProjectionSessionResolver,
    activate_committed_service_package_binding,
    activate_service_package_binding,
)
from aware_service_runtime.package_ref_resolution import (
    ResolvedServiceRuntimePackageRef,
)
from aware_service_runtime.contracts import ServiceGraphGateway
from aware_utils.logging import logger

from aware_service_service.activation.package_refs import (
    implementation_package_toml_paths,
    resolve_committed_implementation_package_refs,
)
from aware_service_service.activation.registry import (
    ActivatedServiceImplementationPackage,
    service_package_id_for_activated_binding,
    service_package_id_for_committed_package_ref,
)
from aware_service_service.activation.runner import (
    activate_implementation_package_bindings,
    duration_since,
)
from aware_service_service.activation.runtime_context import (
    ActivatedImplementationRuntimeContext,
    MetaSdkServiceHostRuntime,
    ReadOnlyCommittedServiceHostRuntime,
    build_implementation_package_lanes,
)
from aware_service_service.config import ServiceHostAppConfig
from aware_service_service.ontology.projections import (
    ensure_service_host_projection_runtime_requirements_available,
    verify_service_host_projection_runtime_from_ontology_artifacts,
)


@dataclass(frozen=True, slots=True)
class ServiceHostActivationResult:
    activated_packages: tuple[ActivatedServiceImplementationPackage, ...]
    service_ids_by_name: dict[str, UUID]
    runtime_context: ActivatedImplementationRuntimeContext | None
    resolved_implementation_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...]
    implementation_package_toml_paths: tuple[Path, ...]
    timings: dict[str, object]


async def activate_service_host_implementation_packages(
    *,
    config: ServiceHostAppConfig,
    resolver: Any,
    graph_gateway: ServiceGraphGateway,
    implementation_package_toml_paths_value: tuple[Path, ...],
    resolved_implementation_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...],
    uses_committed_package_refs: bool,
    service_api_dependency_routes: Mapping[str, object],
    resolve_hosted_runtime_manifest_context: Callable[..., Any],
    install_service_host_ontology_runtime_artifacts: Callable[
        ..., Mapping[str, object]
    ],
    ensure_service_host_db_schema_installed: Callable[..., Any],
    service_host_projection_runtime_requirements: Callable[..., Any],
    service_host_required_projection_names: Callable[..., tuple[str, ...]],
    read_source_activation_meta_runtime_read_model: Callable[..., Any],
    read_source_activation_meta_api_activation_read_model: Callable[..., Any],
    load_verified_revision_semantic_runtime_catalog: Callable[..., Any],
    materialize_service_protocol_api_reference_lanes: Callable[..., Any],
    resolve_experience_reference_branch_resolution: Callable[..., Any],
    service_ontology_orm_package_path_context_for_toml_path: Callable[
        [Path], AbstractContextManager[object]
    ],
    service_activation_projection_session_resolver: Callable[
        [], ProjectionSessionResolver
    ],
    service_host_materialization_runtime_persistence_context: Callable[
        [], AbstractContextManager[object]
    ],
    baseline_required_projection_names: tuple[str, ...],
) -> ServiceHostActivationResult:
    started = perf_counter()
    resolved_refs = tuple(resolved_implementation_package_refs)
    toml_paths = tuple(implementation_package_toml_paths_value)
    has_package_refs = bool(config.implementation_packages.package_refs)
    timings: dict[str, object] = {
        "configured_toml_package_count": len(toml_paths),
        "configured_package_ref_count": len(
            config.implementation_packages.package_refs
        ),
    }
    if not toml_paths and not has_package_refs:
        timings["skipped"] = True
        timings["total_duration_s"] = duration_since(started)
        return _activation_result(
            timings=timings,
            resolved_refs=resolved_refs,
            toml_paths=toml_paths,
        )

    hosted_runtime_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: resolve_hosted_runtime"
    )
    runtime = await resolve_hosted_runtime_manifest_context(resolver)
    timings["get_hosted_runtime_duration_s"] = duration_since(hosted_runtime_started)
    timings["hosted_runtime_resolution_source"] = runtime.source
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "resolve_hosted_runtime duration_s=%.3f source=%s",
        timings["get_hosted_runtime_duration_s"],
        runtime.source,
    )

    ontology_artifact_install_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: "
        "install_ontology_runtime_artifacts"
    )
    ontology_artifact_install_evidence = (
        install_service_host_ontology_runtime_artifacts(
            runtime=runtime,
            config=config,
            implementation_toml_paths=toml_paths,
        )
    )
    timings["install_ontology_runtime_artifacts_duration_s"] = duration_since(
        ontology_artifact_install_started
    )
    timings["ontology_runtime_artifacts"] = ontology_artifact_install_evidence
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "install_ontology_runtime_artifacts duration_s=%.3f status=%s "
        "projection_plan_count=%s",
        timings["install_ontology_runtime_artifacts_duration_s"],
        ontology_artifact_install_evidence.get("status"),
        ontology_artifact_install_evidence.get("projection_plan_count"),
    )

    db_schema_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: "
        "ensure_service_host_db_schema"
    )
    db_schema_evidence = await ensure_service_host_db_schema_installed(
        runtime=runtime,
        config=config,
        implementation_toml_paths=toml_paths,
    )
    timings["ensure_service_host_db_schema_duration_s"] = duration_since(
        db_schema_started
    )
    timings["service_host_db_schema"] = db_schema_evidence
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "ensure_service_host_db_schema duration_s=%.3f status=%s sql_root_count=%s "
        "step_count=%s",
        timings["ensure_service_host_db_schema_duration_s"],
        db_schema_evidence.get("status"),
        db_schema_evidence.get("sql_root_count"),
        db_schema_evidence.get("step_count"),
    )

    projection_runtime_requirements = (
        await service_host_projection_runtime_requirements(
            runtime_manifest_path=runtime.manifest_path,
            config=config,
            implementation_toml_paths=toml_paths,
            service_api_dependency_routes=service_api_dependency_routes,
        )
    )
    required_projection_names = service_host_required_projection_names(
        projection_runtime_requirements=projection_runtime_requirements,
    )
    timings["projection_runtime_requirement_count"] = len(
        projection_runtime_requirements
    )
    timings["required_projection_names"] = list(required_projection_names)
    materialization_allowed = not uses_committed_package_refs
    timings["activation_materialization_allowed"] = materialization_allowed

    if uses_committed_package_refs:
        harness: Any = ReadOnlyCommittedServiceHostRuntime(
            manifest_path=runtime.manifest_path
        )
        catalog_started = perf_counter()
        semantic_runtime_catalog = load_verified_revision_semantic_runtime_catalog(
            config=config,
        )
        timings["semantic_runtime_package_catalog_duration_s"] = duration_since(
            catalog_started
        )
        timings["semantic_runtime_package_catalog"] = {
            "manifest_path": semantic_runtime_catalog.manifest_path.as_posix(),
            "artifact_path": semantic_runtime_catalog.artifact_path.as_posix(),
            "sha256": semantic_runtime_catalog.sha256,
            "byte_length": semantic_runtime_catalog.byte_length,
        }
        read_model_started = perf_counter()
        artifact_root = cast(Path, config.artifact_root).expanduser().resolve()
        read_model = read_local_meta_runtime_read_model(
            repo_root=artifact_root,
            aware_root=artifact_root,
            required_projection_names=required_projection_names,
            required_package_names=_required_meta_runtime_package_names(
                implementation_toml_paths=toml_paths,
            ),
            semantic_ontology_package_catalog=semantic_runtime_catalog.catalog,
            composite_name="ServiceHost WorkspaceRevision Activation Runtime",
        )
        timings["meta_runtime_read_model_duration_s"] = duration_since(
            read_model_started
        )
        timings["meta_runtime_read_model_cache_status"] = read_model.cache_status
        timings["runtime_index_source"] = "workspace_revision_semantic_runtime_catalog"
        index = read_model.index
    else:
        read_model_started = perf_counter()
        logger.info(
            "ServiceHost implementation activation phase started: "
            "meta_api_activation_read_model"
        )
        read_model = read_source_activation_meta_api_activation_read_model(
            config=config,
            runtime=runtime,
            implementation_toml_paths=toml_paths,
            required_projection_names=required_projection_names,
        )
        timings["meta_api_activation_read_model_duration_s"] = duration_since(
            read_model_started
        )
        timings["meta_api_activation_read_model_cache_status"] = read_model.cache_status
        logger.info(
            "ServiceHost implementation activation phase finished: "
            "meta_api_activation_read_model duration_s=%.3f",
            timings["meta_api_activation_read_model_duration_s"],
        )
        timings["runtime_index_source"] = (
            "servicehost_source_meta_api_activation_read_model"
        )
        index = read_model.index
        harness = MetaSdkServiceHostRuntime(
            manifest_path=runtime.manifest_path,
            graph_gateway=graph_gateway,
            index=index,
            environment_id=runtime.environment_config_id,
        )

    projection_runtime_verify_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: "
        "verify_ontology_artifact_projection_runtime"
    )
    projection_runtime_alignment_evidence = (
        verify_service_host_projection_runtime_from_ontology_artifacts(
            read_model=read_model,
            required_projection_names=baseline_required_projection_names,
        )
    )
    timings["verify_ontology_artifact_projection_runtime_duration_s"] = duration_since(
        projection_runtime_verify_started
    )
    timings["ontology_artifact_projection_runtime"] = (
        projection_runtime_alignment_evidence
    )
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "verify_ontology_artifact_projection_runtime duration_s=%.3f status=%s "
        "projection_plan_count=%s",
        timings["verify_ontology_artifact_projection_runtime_duration_s"],
        projection_runtime_alignment_evidence.get("status"),
        projection_runtime_alignment_evidence.get("projection_plan_count"),
    )

    projection_readiness_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: "
        "ensure_projection_runtime_requirements"
    )
    projection_runtime_evidence = (
        ensure_service_host_projection_runtime_requirements_available(
            index=index,
            requirements=projection_runtime_requirements,
        )
    )
    timings["ensure_projection_runtime_requirements_duration_s"] = duration_since(
        projection_readiness_started
    )
    timings["projection_runtime_requirements"] = projection_runtime_evidence
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "ensure_projection_runtime_requirements duration_s=%.3f status=%s "
        "resolved_projection_count=%s",
        timings["ensure_projection_runtime_requirements_duration_s"],
        projection_runtime_evidence.get("status"),
        projection_runtime_evidence.get("resolved_projection_count"),
    )

    refresh_refs_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: "
        "refresh_committed_implementation_refs"
    )
    refreshed_refs = await resolve_committed_implementation_package_refs(
        config=config,
        index=index,
    )
    if refreshed_refs is not None:
        resolved_refs = tuple(refreshed_refs)
        toml_paths = implementation_package_toml_paths(
            config=config,
            resolved_package_refs=resolved_refs,
        )
    timings["refresh_committed_implementation_refs_duration_s"] = duration_since(
        refresh_refs_started
    )
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "refresh_committed_implementation_refs duration_s=%.3f",
        timings["refresh_committed_implementation_refs_duration_s"],
    )

    committed_package_refs = tuple(
        ref for ref in resolved_refs if ref.service_package is not None
    )
    timings["toml_package_count"] = len(toml_paths)
    timings["committed_package_ref_count"] = len(committed_package_refs)
    if not toml_paths and not committed_package_refs:
        timings["skipped"] = True
        timings["total_duration_s"] = duration_since(started)
        return _activation_result(
            timings=timings,
            resolved_refs=resolved_refs,
            toml_paths=toml_paths,
        )

    if not uses_committed_package_refs and materialization_allowed:
        read_model_started = perf_counter()
        logger.info(
            "ServiceHost implementation activation phase started: meta_runtime_read_model"
        )
        read_model = read_source_activation_meta_runtime_read_model(
            config=config,
            runtime=runtime,
            implementation_toml_paths=toml_paths,
            required_projection_names=required_projection_names,
        )
        timings["meta_runtime_read_model_duration_s"] = duration_since(
            read_model_started
        )
        timings["meta_runtime_read_model_cache_status"] = read_model.cache_status
        logger.info(
            "ServiceHost implementation activation phase finished: "
            "meta_runtime_read_model duration_s=%.3f",
            timings["meta_runtime_read_model_duration_s"],
        )
        timings["runtime_index_source"] = "servicehost_source_meta_runtime_read_model"
        index = read_model.index
        harness = MetaSdkServiceHostRuntime(
            manifest_path=runtime.manifest_path,
            graph_gateway=graph_gateway,
            index=index,
            environment_id=runtime.environment_config_id,
            graph_context=read_model.context,
        )

    lanes_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: build_implementation_lanes"
    )
    lanes = build_implementation_package_lanes(
        runtime=None,
        index=index,
        environment_id=runtime.environment_config_id,
    )
    timings["build_implementation_lanes_duration_s"] = duration_since(lanes_started)
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "build_implementation_lanes duration_s=%.3f",
        timings["build_implementation_lanes_duration_s"],
    )
    runtime_context = ActivatedImplementationRuntimeContext(
        runtime=harness,
        environment_config_id=runtime.environment_config_id,
        index=index,
        lanes=lanes,
        runtime_index_source=str(timings["runtime_index_source"]),
    )

    api_reference_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: "
        "materialize_service_protocol_api_reference_lanes"
    )
    api_reference_branch_ids_by_api_name = (
        await materialize_service_protocol_api_reference_lanes(
            runtime=None if not materialization_allowed else harness,
            index=index,
            lane=lanes.api,
            toml_paths=toml_paths,
            committed_package_refs=committed_package_refs,
            allow_materialization=materialization_allowed,
        )
        if toml_paths or committed_package_refs
        else {}
    )
    timings["materialize_service_protocol_api_reference_lanes_duration_s"] = (
        duration_since(api_reference_started)
    )
    timings["api_reference_count"] = len(api_reference_branch_ids_by_api_name)
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "materialize_service_protocol_api_reference_lanes duration_s=%.3f "
        "api_reference_count=%d",
        timings["materialize_service_protocol_api_reference_lanes_duration_s"],
        len(api_reference_branch_ids_by_api_name),
    )

    experience_reference_started = perf_counter()
    logger.info(
        "ServiceHost implementation activation phase started: "
        "resolve_experience_reference_branch_ids"
    )
    experience_reference_resolution = (
        await resolve_experience_reference_branch_resolution(
            index=index,
            runtime=harness,
            environment_id=runtime.environment_config_id,
        )
    )
    experience_reference_branch_ids_by_experience_name = (
        experience_reference_resolution.branch_ids_by_name
    )
    experience_reference_commit_store_root = (
        experience_reference_resolution.commit_store_root
        if experience_reference_resolution.commit_store_root is not None
        else config.artifact_root
    )
    timings["resolve_experience_reference_branch_ids_duration_s"] = duration_since(
        experience_reference_started
    )
    timings["experience_reference_count"] = len(
        experience_reference_branch_ids_by_experience_name
    )
    logger.info(
        "ServiceHost implementation activation phase finished: "
        "resolve_experience_reference_branch_ids duration_s=%.3f "
        "experience_reference_count=%d",
        timings["resolve_experience_reference_branch_ids_duration_s"],
        len(experience_reference_branch_ids_by_experience_name),
    )

    activation_result = await activate_implementation_package_bindings(
        toml_paths=toml_paths,
        committed_package_refs=committed_package_refs,
        runtime=harness,
        index=index,
        lanes=lanes,
        api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        experience_reference_branch_ids_by_experience_name=(
            experience_reference_branch_ids_by_experience_name
        ),
        experience_reference_commit_store_root=experience_reference_commit_store_root,
        allow_materialization=materialization_allowed,
        activation_commit_store_root=(
            cast(Path, config.artifact_root).expanduser().resolve()
            if uses_committed_package_refs
            else None
        ),
        projection_session_resolver_factory=(
            service_activation_projection_session_resolver
        ),
        materialization_runtime_persistence_context=(
            service_host_materialization_runtime_persistence_context
        ),
        toml_path_context=service_ontology_orm_package_path_context_for_toml_path,
        activate_committed_package_binding=activate_committed_service_package_binding,
        activate_toml_package_binding=activate_service_package_binding,
        service_package_id_for_committed_package_ref=(
            service_package_id_for_committed_package_ref
        ),
        service_package_id_for_activated_binding=(
            service_package_id_for_activated_binding
        ),
    )
    timings.update(activation_result.timings)
    timings["activated_package_count"] = len(activation_result.activated_packages)
    timings["activated_service_count"] = len(activation_result.service_ids_by_name)
    timings["total_duration_s"] = duration_since(started)
    return ServiceHostActivationResult(
        activated_packages=activation_result.activated_packages,
        service_ids_by_name=activation_result.service_ids_by_name,
        runtime_context=runtime_context,
        resolved_implementation_package_refs=resolved_refs,
        implementation_package_toml_paths=toml_paths,
        timings=timings,
    )


def _required_meta_runtime_package_names(
    *,
    implementation_toml_paths: tuple[Path, ...],
) -> tuple[str, ...]:
    from aware_service_runtime.manifest.loader import (  # noqa: WPS433
        load_aware_service_toml_spec,
    )

    package_names: list[str] = []
    seen: set[str] = set()
    for toml_path in implementation_toml_paths:
        spec = load_aware_service_toml_spec(toml_path=toml_path.expanduser().resolve())
        for ontology_package in getattr(spec, "ontology_packages", ()) or ():
            package_name = str(
                getattr(ontology_package, "package_name", "") or ""
            ).strip()
            if not package_name or package_name in seen:
                continue
            seen.add(package_name)
            package_names.append(package_name)
    return tuple(package_names)


def _activation_result(
    *,
    timings: dict[str, object],
    resolved_refs: tuple[ResolvedServiceRuntimePackageRef, ...],
    toml_paths: tuple[Path, ...],
) -> ServiceHostActivationResult:
    return ServiceHostActivationResult(
        activated_packages=(),
        service_ids_by_name={},
        runtime_context=None,
        resolved_implementation_package_refs=resolved_refs,
        implementation_package_toml_paths=toml_paths,
        timings=timings,
    )


__all__ = [
    "ServiceHostActivationResult",
    "activate_service_host_implementation_packages",
]
