from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID, NAMESPACE_URL, uuid5

from aware_attention_ontology.stable_ids import (
    stable_attention_package_id,
)
from aware_code.stable_ids import (
    code_package_generated_config_key,
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code_ontology.stable_ids import stable_code_package_id
from aware_code.types.json import JsonArray, JsonObject, JsonValue
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.actor.compiler import load_actor_role_ownership_from_sources
from aware_experience.compiler.builder import (
    publish_environment_profile_actor_role_ownership,
)
from aware_experience.compiler.compile import compile_experience_workspace
from aware_experience.compiler.models import (
    ExperienceEnvironmentProfileOwnership,
)
from aware_experience.environment.compiler import (
    load_environment_ownership_from_sources,
)
from aware_experience.environment_profile.compiler import (
    load_environment_profile_ownership_from_sources,
)
from aware_experience.environment_profile.runtime_support import ocg_support
from aware_experience.event.compiler import (
    load_dependency_event_ownership_from_snapshot,
    load_event_ownership_from_sources,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from aware_experience.language_contracts import (
    ExperienceLanguageContractPackage,
)
from aware_experience.manifest.spec import AwareExperienceDependencyKind
from aware_experience.graph.materialization.service import (
    materialize_experience_graph_ontology,
)
from aware_experience.materialization.snapshot_commit import (
    ExperiencePackageLanguagePackageSnapshotRef,
)
from aware_experience.materialization import lane_state as _lane_state
from aware_experience.materialization.lane_state import (
    hydrate_lane_root_from_head as _hydrate_lane_root_from_head,
    hydrate_lane_session as _hydrate_lane_session,
    lane_head_commit_id as _lane_head_commit_id,
)
from aware_experience.materialization import (
    static_projection_targets as _static_projection_targets,
)
from aware_experience.materialization.compile_plan_payloads import (
    _build_source_experience_compile_plan_payload,
    _dependency_projection_experience_prefixes,
    load_api_compile_plan_payloads_for_workspace,
    load_experience_compile_plan_payloads,
)
from aware_experience.materialization.activation_topology_materialization import (
    ActivationTopologyMaterializationDependencies,
    _ActivationInvocationTargetSpec,
    _ActivationTopologyStepContext,
    _EndpointRequestAttributeRef,
    _activation_action_request_bindings as _activation_action_request_bindings_impl,
    _activation_projection_spec_for_profile,
    _endpoint_request_attributes_by_endpoint_ref,
    materialize_experience_activation_topology_ontology as _run_experience_activation_topology_ontology,
)
from aware_experience.materialization.action_materialization import (  # noqa: F401
    ActionMaterializationDependencies,
    ActionMaterializationSpec,
    build_action_materialization_plan,
    materialize_experience_compile_plan_actions as _run_experience_compile_plan_actions,
    resolve_action_materialization_specs,
)
from aware_experience.materialization.actor_materialization import (  # noqa: F401
    ActorMaterializationDependencies,
    ActorMaterializationSpec,
    ProfileActorMaterializationSpec,
    ProfileRoleMaterializationSpec,
    build_actor_materialization_plan,
    decode_actor_materialization_step_payload,
    encode_actor_materialization_step_payload,
    materialize_environment_experience_profile_actor_role_ontology as _run_environment_experience_profile_actor_role_ontology,
    materialize_experience_actor_ontology as _run_experience_actor_ontology,
    materialize_experience_compile_plan_actors as _run_experience_compile_plan_actors,
    resolve_actor_materialization_specs,
    resolve_profile_role_capability_target,
)
from aware_experience.materialization.connector_materialization import (  # noqa: F401
    ActuatorConfigMaterializationSpec,
    ConnectorConfigMaterializationSpec,
    ConnectorInvocationActionConfigMaterializationSpec,
    ConnectorInvocationRequestFieldMaterializationSpec,
    ConnectorMaterializationDependencies,
    ConnectorProviderMaterializationSpec,
    SensorConfigMaterializationSpec,
    _connector_invocation_action_target_ids,
    build_connector_config_materialization_plan,
    decode_connector_config_materialization_step_payload,
    encode_connector_config_materialization_step_payload,
    materialize_experience_compile_plan_connector_configs as _run_experience_compile_plan_connector_configs,
    materialize_experience_connector_config_ontology as _run_experience_connector_config_ontology,
    resolve_activation_target_materialization_specs,
    resolve_connector_config_materialization_specs,
)
from aware_experience.materialization.environment_profile_materialization import (  # noqa: F401
    EnvironmentProfileMaterializationDependencies,
    EnvironmentProfileMaterializationSpec,
    EnvironmentProfileProcessMaterializationSpec,
    EnvironmentProfileThreadLayoutMaterializationSpec,
    EnvironmentProfileThreadLayoutSectionMaterializationSpec,
    EnvironmentProfileThreadMaterializationSpec,
    EnvironmentProfileThreadProjectionMaterializationSpec,
    EnvironmentProfileViewEventTransitionMaterializationSpec,
    _EnvironmentExperienceRootEnsureResult,
    _ThreadConfigRootEnsureResult,
    _environment_profile_projection_catalog_branch_ids,
    _filter_environment_profile_spec_for_projection_catalog,
    _projection_keys_by_experience_name_from_catalog,
    _require_environment_profile_identity,
    _resolve_projection_experience_for_reference,
    _upsert_environment_profile_via_api,
    build_environment_profile_materialization_plan,
    decode_environment_profile_materialization_step_payload,
    encode_environment_profile_materialization_step_payload,
    materialize_experience_environment_profile_ontology as _run_experience_environment_profile_ontology,
    resolve_environment_profile_materialization_specs,
    _ensure_environment_experience_profile_config_branch_root as _run_ensure_environment_experience_profile_config_branch_root,
    _ensure_environment_experience_profile_lane_root as _run_ensure_environment_experience_profile_lane_root,
    _ensure_thread_config_lane_root as _run_ensure_thread_config_lane_root,
)
from aware_experience.materialization.projection_contract_materialization import (  # noqa: F401
    ProjectionExperienceLayoutGraphBindingSpec,
    ProjectionExperienceMaterializationSpec,
    ProjectionExperienceSectionSurfaceBindingSpec,
    ProjectionExperienceSectionSurfaceMaterializationSpec,
    ProjectionExperienceViewMaterializationSpec,
    _ApiViewCapabilityEndpointMaterializationRef,
    _api_view_capability_endpoint_refs_by_view_action,
    _build_observable_id_index,
    _decode_projection_experience_ownership,
    _find_projection_graph_by_opgi_id,
    _has_planned_threads,
    _layout_config_section_config_ids_by_section_surface,
    _layout_graph_binding_specs_by_experience,
    _normalize_symbol,
    _projection_experience_ids_by_name_and_opgi_from_session,
    _projection_experience_view_ids_by_projection_key_from_session,
    _projection_view_invocation_action_snapshot,
    _projection_view_key,
    _record_optional_phase,
    _resolve_observable_id_for_projection_view,
    _resolve_projection_hash_for_class_suffix,
    _resolve_projection_opgi_id_for_projection_key,
    _resolve_projection_view_invocation_actions,
    _sort_section_surface_binding_specs,
    _split_api_view_ref,
    _stable_api_capability_endpoint_id_for_endpoint_ref,
    build_projection_materialization_plan,
    build_section_surface_materialization_plan,
    decode_projection_materialization_step_payload,
    decode_section_surface_materialization_step_payload,
    encode_projection_materialization_step_payload,
    encode_section_surface_materialization_step_payload,
    materialize_experience_compile_plan_graphs,
    materialize_experience_compile_plan_projections,
    materialize_experience_compile_plan_section_surfaces,
    materialize_experience_projection_ontology,
    materialize_experience_section_surface_ontology as _run_experience_section_surface_ontology,
    resolve_projection_materialization_specs,
    resolve_section_surface_materialization_specs,
)
from aware_experience.materialization.projection_resolution import (
    build_projection_runtime_resolver,
)
from aware_experience.materialization.program_materialization import (
    ProgramMaterializationDependencies,
    ProgramMaterializationSpec,
    build_program_materialization_plan,
    decode_program_materialization_step_payload,
    encode_program_materialization_step_payload,
    materialize_experience_compile_plan_programs as _run_experience_compile_plan_programs,
    materialize_experience_program_ontology as _run_experience_program_ontology,
    resolve_program_materialization_specs,
    _program_invoke_port_node_id as _program_invoke_port_node_id,
    _program_projection_catalog_branch_ids,
    _resolve_program_port_node_snapshot as _resolve_program_port_node_snapshot,
)
from aware_experience.materialization.package_orchestrator import (
    ExperiencePackageInstallScope,
    ExperiencePackageMaterializationOrchestratorDependencies,
    ExperiencePackageMaterializationResult,
    ExperiencePackageMaterializationSpec,
    run_experience_package_materialization,
)
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)
from aware_experience_ontology.environment.experience_package import ExperiencePackage
from aware_experience_ontology.actuator.actuator_invocation_action_config import (  # noqa: F401
    ActuatorInvocationActionConfig,
)
from aware_experience_ontology.connector.connector_config import (  # noqa: F401
    ConnectorConfig,
)
from aware_experience_ontology.sensor.sensor_invocation_action_config import (  # noqa: F401
    SensorInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (  # noqa: F401
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_experience.program.registry_index import find_repo_root
from aware_meta.materialization import (
    MaterializationExecutionError,
    MaterializationLaneContext,
    MaterializationRunReceipt,
)
from aware_meta.runtime.graph_lane import (
    bind_meta_graph_runtime_lane as _bind_meta_graph_runtime_lane_impl,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)


class _RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...

    @property
    def invoker(self) -> object: ...


def _bind_meta_graph_runtime_lane(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection: str,
    actor_id: UUID | None,
) -> _EnvironmentExperienceRootEnsureResult:
    _ = index
    runtime_context = getattr(runtime, "context", None)
    if runtime_context is None:
        raise RuntimeError(
            "Experience materialization requires MetaGraphRuntime.context to bind "
            "Meta graph materialization lanes."
        )
    return _bind_meta_graph_runtime_lane_impl(
        runtime=cast(Any, runtime),
        context=runtime_context,
        branch_id=branch_id,
        projection=projection,
        actor_id=actor_id,
    )


_module_id_from_projection_node_name = (
    _static_projection_targets.module_id_from_projection_node_name
)
_projection_oigi_snapshots_for_materialization = (
    _static_projection_targets.projection_oigi_snapshots_for_materialization
)
_stable_source_id_binding_for_node = (
    _static_projection_targets.stable_source_id_binding_for_node
)
_StaticProjectionTargetNotDerivable = (
    _static_projection_targets.StaticProjectionTargetNotDerivable
)


_EXPERIENCE_PROFILE_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/environment-profile/snapshot-commit/v1",
)
_EXPERIENCE_PROFILE_EVENT_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/environment-profile/event-config-snapshot-commit/v1",
)
_EXPERIENCE_ACTIVATION_PROFILE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/activation/profile-config-snapshot/v1",
)
_EXPERIENCE_ACTIVATION_ACTION_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/activation/action-snapshot/v1",
)
_EXPERIENCE_ACTIVATION_INVOCATION_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/activation/invocation-config-snapshot/v1",
)

_ENVIRONMENT_EXPERIENCE_PROJECTION_NAME = "EnvironmentExperience"
_ENVIRONMENT_EXPERIENCE_PROFILE_PROJECTION_NAME = "EnvironmentExperienceProfile"
_ENVIRONMENT_TOPOLOGY_SEED_PROJECTION_NAME = "EnvironmentTopologySeed"


@dataclass(frozen=True, slots=True)
class ExperienceProfilePublicationSummary:
    experience_handle: str
    profiles: tuple[ExperienceEnvironmentProfileOwnership, ...]


def resolve_experience_package_materialization_spec(
    *,
    experience_toml_path: Path,
    workspace_root: Path,
) -> ExperiencePackageMaterializationSpec:
    resolved_experience_toml_path = experience_toml_path.resolve()
    resolved_workspace_root = workspace_root.resolve()
    compile_result = compile_experience_workspace(
        toml_path=resolved_experience_toml_path,
        repo_root=resolved_workspace_root,
    )
    snapshot = compile_result.snapshot
    manifest_spec = snapshot.spec
    package_name = (manifest_spec.experience.package_name or "").strip()
    if not package_name:
        raise RuntimeError(
            "Experience package materialization requires non-empty [experience].package_name in aware.experience.toml: "
            + str(resolved_experience_toml_path)
        )
    package_fqn_prefix = (manifest_spec.experience.fqn_prefix or "").strip()
    if not package_fqn_prefix:
        raise RuntimeError(
            "Experience package materialization requires non-empty [experience].fqn_prefix in aware.experience.toml: "
            + str(resolved_experience_toml_path)
        )

    projection_experiences = load_projection_experience_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    if not projection_experiences:
        discovered_experience_names = sorted(
            item.name for item in projection_experiences
        )
        raise RuntimeError(
            "Experience package materialization requires at least one canonical `experience` declaration per "
            "aware.experience.toml package: "
            + f"experience_toml_path={resolved_experience_toml_path} "
            + f"discovered={discovered_experience_names!r}"
        )
    canonical_projection_experiences = tuple(
        sorted(
            projection_experiences,
            key=lambda experience: (
                experience.name.casefold(),
                experience.source_path,
            ),
        )
    )
    canonical_experience_names = tuple(
        experience.name for experience in canonical_projection_experiences
    )
    canonical_experience = canonical_projection_experiences[0]

    return ExperiencePackageMaterializationSpec(
        experience_toml_path=resolved_experience_toml_path,
        workspace_root=resolved_workspace_root,
        manifest_spec=manifest_spec,
        package_name=package_name,
        package_fqn_prefix=package_fqn_prefix,
        experience_names=canonical_experience_names,
        experience_name=canonical_experience.name,
        experience_source_path=canonical_experience.source_path,
        source_files=tuple(path.as_posix() for path in snapshot.source_files),
    )


def resolve_experience_profile_publication_summary(
    *,
    experience_toml_path: Path,
    workspace_root: Path,
) -> ExperienceProfilePublicationSummary:
    compile_result = compile_experience_workspace(
        toml_path=experience_toml_path.resolve(),
        repo_root=workspace_root.resolve(),
    )
    snapshot = compile_result.snapshot
    experience_handle = (snapshot.spec.experience.fqn_prefix or "").strip()
    if not experience_handle:
        raise RuntimeError(
            "Experience profile publication requires non-empty [experience].fqn_prefix in aware.experience.toml: "
            + str(experience_toml_path.resolve())
        )

    projection_experience_ownership = load_projection_experience_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    environment_profile_ownership = load_environment_profile_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        projection_experience_ownership=projection_experience_ownership,
        event_ownership=load_event_ownership_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
            package_name=(snapshot.spec.experience.package_name or "").strip() or None,
            fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip() or None,
        )
        + load_dependency_event_ownership_from_snapshot(snapshot=snapshot),
        external_projection_experience_prefixes=(
            _dependency_projection_experience_prefixes(snapshot=snapshot)
        ),
    )
    role_ownership, actor_ownership, environment_actor_bindings = (
        load_actor_role_ownership_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
        )
    )
    environment_ownership = load_environment_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    return ExperienceProfilePublicationSummary(
        experience_handle=experience_handle,
        profiles=publish_environment_profile_actor_role_ownership(
            environment_profile_ownership=environment_profile_ownership,
            role_ownership=role_ownership,
            actor_ownership=actor_ownership,
            environment_actor_bindings=environment_actor_bindings,
            environment_ownership=environment_ownership,
        ),
    )


def _supports_source_experience_projection_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    compile_plan_payload: Mapping[str, object],
) -> bool:
    projection_ownership = _decode_projection_experience_ownership(
        compile_plan_payloads=(compile_plan_payload,),
    )
    if not projection_ownership:
        return False

    resolver = build_projection_runtime_resolver(index=index)
    try:
        for ownership in projection_ownership:
            _ = resolver.resolve(
                projection_key=ownership.projection,
                node_refs=(node.node_ref for node in ownership.nodes),
                experience_name=ownership.name,
                context="Projection materialization",
            )
    except RuntimeError:
        return False
    return True


def experience_source_code_package_config_id() -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_experience_toml",
            surface="experience",
        )
    )


def experience_source_code_package_id(*, package_name: str) -> UUID:
    return stable_code_package_id(
        code_package_config_id=experience_source_code_package_config_id(),
        package_name=package_name,
        language=CodeLanguage.aware.value,
    )


_LANGUAGE_CONTRACT_OUTPUT_KEY = "experience.language_contract.generated_code_packages"
_LANGUAGE_CONTRACT_MATERIALIZATION_SOURCE = "experience"
_LANGUAGE_CONTRACT_RENDERER_KIND = "language_contract"
_LANGUAGE_CONTRACT_SURFACE = "runtime"


def _experience_language_contract_code_package_config_id(
    *,
    package: ExperienceLanguageContractPackage,
) -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_generated_config_key(
            materialization_source=_LANGUAGE_CONTRACT_MATERIALIZATION_SOURCE,
            renderer_kind=_LANGUAGE_CONTRACT_RENDERER_KIND,
            language=_experience_language_contract_code_language(
                language=package.language,
            ),
            surface=_LANGUAGE_CONTRACT_SURFACE,
            manifest_kind=_experience_language_contract_manifest_kind(
                language=package.language,
            ),
        )
    )


def _experience_language_contract_code_package_id(
    *,
    package: ExperienceLanguageContractPackage,
) -> UUID:
    return stable_code_package_id(
        code_package_config_id=_experience_language_contract_code_package_config_id(
            package=package,
        ),
        package_name=package.package_name,
        language=package.language,
    )


def _experience_language_contract_package_snapshot_refs(
    *,
    language_contract_packages: tuple[ExperienceLanguageContractPackage, ...],
) -> tuple[ExperiencePackageLanguagePackageSnapshotRef, ...]:
    refs: list[ExperiencePackageLanguagePackageSnapshotRef] = []
    for package in language_contract_packages:
        refs.append(
            ExperiencePackageLanguagePackageSnapshotRef(
                code_package_id=_experience_language_contract_code_package_id(
                    package=package,
                ),
                package_name=package.package_name,
                language=_experience_language_contract_code_language(
                    language=package.language,
                ),
                import_root=package.import_root,
                manifest_relative_path=package.manifest_relative_path,
                package_root=package.relpath,
                sources_root=package.sources_root_relpath,
                role="view_model_package",
                output_key=_LANGUAGE_CONTRACT_OUTPUT_KEY,
                include_paths=JsonArray([]),
                exclude_paths=JsonArray([]),
            )
        )
    return tuple(refs)


def _experience_language_contract_code_language(*, language: str) -> CodeLanguage:
    if language == "python":
        return CodeLanguage.python
    if language == "dart":
        return CodeLanguage.dart
    raise RuntimeError(f"Unsupported Experience language package target: {language!r}")


def _experience_language_contract_manifest_kind(*, language: str) -> str:
    if language == "python":
        return "pyproject_toml"
    if language == "dart":
        return "pubspec_yaml"
    raise RuntimeError(f"Unsupported Experience language package target: {language!r}")


async def materialize_experience_package_from_manifest(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    experience_toml_path: Path,
    allow_unresolved_projection_experiences: bool = False,
    install_scope: ExperiencePackageInstallScope | str = (
        ExperiencePackageInstallScope.activation
    ),
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
    prefer_snapshot_environment_profiles: bool = False,
    environment_api_client: Any | None = None,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    semantic_materialization_context: Mapping[str, object] | None = None,
) -> ExperiencePackageMaterializationResult:
    return await run_experience_package_materialization(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        workspace_root=workspace_root,
        experience_toml_path=experience_toml_path,
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
        install_scope=install_scope,
        projection_reference_branch_ids_by_name=(
            projection_reference_branch_ids_by_name
        ),
        prefer_snapshot_environment_profiles=prefer_snapshot_environment_profiles,
        environment_api_client=environment_api_client,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        semantic_materialization_context=semantic_materialization_context,
        dependencies=ExperiencePackageMaterializationOrchestratorDependencies(
            resolve_experience_package_materialization_spec=(
                resolve_experience_package_materialization_spec
            ),
            compile_experience_workspace=compile_experience_workspace,
            build_source_experience_compile_plan_payload=(
                _build_source_experience_compile_plan_payload
            ),
            load_api_compile_plan_payloads_for_workspace=(
                load_api_compile_plan_payloads_for_workspace
            ),
            source_code_package_config_id=experience_source_code_package_config_id,
            source_code_package_id=experience_source_code_package_id,
            relative_to=_relative_to,
            language_contract_package_snapshot_refs=(
                _experience_language_contract_package_snapshot_refs
            ),
            validate_environment_experience_materialization_result=(
                _validate_environment_experience_materialization_result
            ),
            validate_experience_package_materialization_result=(
                _validate_experience_package_materialization_result
            ),
            supports_source_experience_projection_materialization=(
                _supports_source_experience_projection_materialization
            ),
            materialize_experience_projection_ontology=(
                materialize_experience_projection_ontology
            ),
            materialize_experience_graph_ontology=(
                materialize_experience_graph_ontology
            ),
            materialize_experience_section_surface_ontology=(
                materialize_experience_section_surface_ontology
            ),
            materialize_experience_activation_topology_ontology=(
                materialize_experience_activation_topology_ontology
            ),
            materialize_experience_environment_profile_ontology=(
                materialize_experience_environment_profile_ontology
            ),
            materialize_experience_program_ontology=(
                materialize_experience_program_ontology
            ),
        ),
    )


def _actor_materialization_dependencies() -> ActorMaterializationDependencies:
    return ActorMaterializationDependencies(
        bind_meta_graph_runtime_lane=_bind_meta_graph_runtime_lane,
        resolve_projection_hash_for_class_suffix=(
            _resolve_projection_hash_for_class_suffix
        ),
    )


async def materialize_experience_actor_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_experience_profile_config_id: UUID,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    return await _run_experience_actor_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_experience_profile_config_id=(
            environment_experience_profile_config_id
        ),
        compile_plan_payloads=compile_plan_payloads,
        dependencies=_actor_materialization_dependencies(),
    )


async def materialize_environment_experience_profile_actor_role_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_experience_profile_config_id: UUID,
    role_specs: Sequence[ProfileRoleMaterializationSpec],
    actor_specs: Sequence[ProfileActorMaterializationSpec],
) -> None:
    return await _run_environment_experience_profile_actor_role_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_experience_profile_config_id=(
            environment_experience_profile_config_id
        ),
        role_specs=role_specs,
        actor_specs=actor_specs,
        dependencies=_actor_materialization_dependencies(),
    )


async def materialize_experience_compile_plan_actors(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_experience_profile_config_id: UUID,
    planned_processes: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    return await _run_experience_compile_plan_actors(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_experience_profile_config_id=(
            environment_experience_profile_config_id
        ),
        planned_processes=planned_processes,
        dependencies=_actor_materialization_dependencies(),
    )


def _action_materialization_dependencies() -> ActionMaterializationDependencies:
    return ActionMaterializationDependencies(
        invoke_constructor_environment_function=(
            _invoke_constructor_environment_function
        ),
    )


async def materialize_experience_compile_plan_actions(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    return await _run_experience_compile_plan_actions(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        planned_processes=planned_processes,
        dependencies=_action_materialization_dependencies(),
    )


def _connector_materialization_dependencies() -> ConnectorMaterializationDependencies:
    return ConnectorMaterializationDependencies(
        bind_meta_graph_runtime_lane=_bind_meta_graph_runtime_lane,
        resolve_projection_opgi_id=_resolve_projection_opgi_id_for_projection_key,
        find_projection_graph_by_opgi_id=_find_projection_graph_by_opgi_id,
    )


async def materialize_experience_connector_config_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    return await _run_experience_connector_config_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        dependencies=_connector_materialization_dependencies(),
    )


async def materialize_experience_compile_plan_connector_configs(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    return await _run_experience_compile_plan_connector_configs(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        planned_processes=planned_processes,
        dependencies=_connector_materialization_dependencies(),
    )


async def materialize_experience_section_surface_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> MaterializationRunReceipt | None:
    external_projection_keys_by_experience_name: dict[str, str] = {}
    if projection_reference_branch_ids_by_name:
        reference_catalog = await _load_projection_experience_catalog(
            index=index,
            branch_ids=tuple(
                dict.fromkeys(projection_reference_branch_ids_by_name.values())
            ),
        )
        external_projection_keys_by_experience_name = (
            _projection_keys_by_experience_name_from_catalog(
                index=index,
                catalog=reference_catalog,
            )
        )
    return await _run_experience_section_surface_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        external_projection_keys_by_experience_name=(
            external_projection_keys_by_experience_name
        ),
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
    )


async def materialize_experience_activation_topology_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_compile_plan_payloads: Sequence[Mapping[str, object]] = (),
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
    allow_unresolved_projection_experiences: bool = False,
) -> MaterializationRunReceipt | None:
    _ = runtime
    return await _run_experience_activation_topology_ontology(
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        api_compile_plan_payloads=api_compile_plan_payloads,
        projection_reference_branch_ids_by_name=(
            projection_reference_branch_ids_by_name
        ),
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
        dependencies=_activation_topology_materialization_dependencies(),
    )


def _activation_topology_materialization_dependencies() -> (
    ActivationTopologyMaterializationDependencies
):
    return ActivationTopologyMaterializationDependencies(
        load_projection_experience_catalog=_load_projection_experience_catalog,
        resolve_environment_profile_materialization_specs=(
            resolve_environment_profile_materialization_specs
        ),
        resolve_action_materialization_specs=resolve_action_materialization_specs,
        resolve_connector_config_materialization_specs=(
            resolve_connector_config_materialization_specs
        ),
        resolve_activation_target_materialization_specs=(
            resolve_activation_target_materialization_specs
        ),
        resolve_projection_materialization_specs=resolve_projection_materialization_specs,
        resolve_projection_opgi_id_for_projection_key=(
            _resolve_projection_opgi_id_for_projection_key
        ),
        find_projection_graph_by_opgi_id=_find_projection_graph_by_opgi_id,
        connector_invocation_action_target_ids=(
            _connector_invocation_action_target_ids
        ),
        normalize_symbol=_normalize_symbol,
    )


def _activation_action_request_bindings(
    *,
    action_specs: Sequence[ActionMaterializationSpec],
    targets: Sequence[_ActivationInvocationTargetSpec],
) -> tuple[
    tuple[ActionMaterializationSpec, tuple[_ActivationInvocationTargetSpec, ...]], ...
]:
    return _activation_action_request_bindings_impl(
        action_specs=action_specs,
        targets=targets,
        dependencies=_activation_topology_materialization_dependencies(),
    )


async def materialize_experience_program_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    phase_timings_s: dict[str, float] | None = None,
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
) -> tuple[MaterializationRunReceipt | None, MaterializationRunReceipt | None]:
    _ = runtime
    return await _run_experience_program_ontology(
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        phase_timings_s=phase_timings_s,
        projection_reference_branch_ids_by_name=(
            projection_reference_branch_ids_by_name
        ),
        dependencies=_program_materialization_dependencies(),
    )


async def materialize_experience_compile_plan_programs(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
) -> tuple[MaterializationRunReceipt | None, MaterializationRunReceipt | None]:
    return await _run_experience_compile_plan_programs(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        planned_processes=planned_processes,
        dependencies=_program_materialization_dependencies(),
    )


async def _load_projection_experience_catalog(
    *,
    index: MetaGraphRuntimeIndex,
    branch_ids: Sequence[UUID],
) -> dict[str, object]:
    projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    unique_branch_ids = tuple(dict.fromkeys(branch_ids))
    projections_by_name: dict[str, ProjectionExperience] = {}
    views_by_projection_and_name: dict[tuple[UUID, str], ProjectionExperienceView] = {}
    section_graph_bindings_by_projection_and_key: dict[
        tuple[UUID, str], ProjectionExperienceSectionGraphBinding
    ] = {}
    nodes_by_projection_and_key: dict[tuple[UUID, str], ProjectionExperienceNode] = {}
    identities_by_node_and_key: dict[
        tuple[UUID, str], ProjectionExperienceNodeIdentity
    ] = {}
    store = FSCommitStore()
    for branch_id in unique_branch_ids:
        head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
        if head is None or head.get("commit_id") is None:
            continue
        session = await _hydrate_lane_session(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            error_context="Program materialization ProjectionExperience catalog",
        )
        for obj in session.imap_all_objects():
            if isinstance(obj, ProjectionExperience) and obj.id is not None:
                name = (obj.name or "").strip()
                if name:
                    projections_by_name[name.casefold()] = obj
            elif isinstance(obj, ProjectionExperienceView) and obj.id is not None:
                projection_experience_id = obj.projection_experience_id
                name = (obj.name or "").strip()
                if projection_experience_id is not None and name:
                    views_by_projection_and_name[
                        (projection_experience_id, name.casefold())
                    ] = obj
            elif (
                isinstance(obj, ProjectionExperienceSectionGraphBinding)
                and obj.id is not None
            ):
                projection_experience_id = obj.projection_experience_id
                binding_key = (obj.binding_key or "").strip()
                if projection_experience_id is not None and binding_key:
                    section_graph_bindings_by_projection_and_key[
                        (projection_experience_id, binding_key.casefold())
                    ] = obj
            elif isinstance(obj, ProjectionExperienceNode) and obj.id is not None:
                projection_experience_id = obj.projection_experience_id
                key = (obj.key or "").strip()
                if projection_experience_id is not None and key:
                    nodes_by_projection_and_key[
                        (projection_experience_id, key.casefold())
                    ] = obj
            elif (
                isinstance(obj, ProjectionExperienceNodeIdentity) and obj.id is not None
            ):
                projection_experience_node_id = obj.projection_experience_node_id
                key = (obj.key or "").strip()
                if projection_experience_node_id is not None and key:
                    identities_by_node_and_key[
                        (projection_experience_node_id, key.casefold())
                    ] = obj
    return {
        "projections_by_name": projections_by_name,
        "views_by_projection_and_name": views_by_projection_and_name,
        "section_graph_bindings_by_projection_and_key": (
            section_graph_bindings_by_projection_and_key
        ),
        "nodes_by_projection_and_key": nodes_by_projection_and_key,
        "identities_by_node_and_key": identities_by_node_and_key,
    }


def _program_materialization_dependencies() -> ProgramMaterializationDependencies:
    return ProgramMaterializationDependencies(
        phase_recorder=_record_optional_phase,
        load_projection_experience_catalog=_load_projection_experience_catalog,
    )


def _environment_profile_materialization_dependencies() -> (
    EnvironmentProfileMaterializationDependencies
):
    return EnvironmentProfileMaterializationDependencies(
        commit_store_factory=FSCommitStore,
        load_projection_experience_catalog=_load_projection_experience_catalog,
        invoke_constructor_environment_function=(
            _invoke_constructor_environment_function
        ),
        lane_head_commit_id=_lane_head_commit_id,
        hydrate_lane_root_from_head=_hydrate_lane_root_from_head,
        resolve_specs=resolve_environment_profile_materialization_specs,
    )


async def materialize_experience_environment_profile_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_id: UUID,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
    prefer_snapshot_materialization: bool = False,
    allow_unresolved_projection_experiences: bool = False,
    environment_api_client: Any | None = None,
) -> MaterializationRunReceipt | None:
    return await _run_experience_environment_profile_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        compile_plan_payloads=compile_plan_payloads,
        projection_reference_branch_ids_by_name=(
            projection_reference_branch_ids_by_name
        ),
        prefer_snapshot_materialization=prefer_snapshot_materialization,
        allow_unresolved_projection_experiences=(
            allow_unresolved_projection_experiences
        ),
        environment_api_client=environment_api_client,
        dependencies=_environment_profile_materialization_dependencies(),
    )


async def materialize_experience_compile_plan_environment_profiles(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
) -> MaterializationRunReceipt | None:
    if not _has_planned_threads(planned_processes=planned_processes):
        return None

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_environment_profile_ontology(  # type: ignore[call-arg]
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
    )


async def _ensure_environment_experience_profile_lane_root(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    function_id: UUID,
    spec: EnvironmentProfileMaterializationSpec,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> _EnvironmentExperienceRootEnsureResult:
    return await _run_ensure_environment_experience_profile_lane_root(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        function_id=function_id,
        spec=spec,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        dependencies=_environment_profile_materialization_dependencies(),
    )


async def _ensure_environment_experience_profile_config_branch_root(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    function_id: UUID,
    spec: EnvironmentProfileMaterializationSpec,
    environment_experience_id: UUID,
    environment_profile_config_id: UUID,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> _EnvironmentExperienceRootEnsureResult:
    return await _run_ensure_environment_experience_profile_config_branch_root(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        function_id=function_id,
        spec=spec,
        environment_experience_id=environment_experience_id,
        environment_profile_config_id=environment_profile_config_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        dependencies=_environment_profile_materialization_dependencies(),
    )


async def _ensure_thread_config_lane_root(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    function_id: UUID,
    process_config_id: UUID,
    thread_spec: EnvironmentProfileThreadMaterializationSpec,
) -> object:
    return await _run_ensure_thread_config_lane_root(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        function_id=function_id,
        process_config_id=process_config_id,
        thread_spec=thread_spec,
        dependencies=_environment_profile_materialization_dependencies(),
    )


def _resolve_projection_experience_for_program_port(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
) -> ProjectionExperience:
    return _resolve_projection_experience_for_reference(
        catalog=catalog,
        projection_ref=projection_ref,
        context="Program port materialization",
    )


async def _invoke_constructor_environment_function(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    function_id: UUID,
    args: list[JsonValue],
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> InvokeFunctionResponse:
    opg = index.opg_by_hash.get(lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Constructor invocation could not resolve ObjectProjectionGraph "
            f"for projection_hash={lane.projection_hash!r}"
        )
    request = InvokeFunctionRequest(
        operation="invoke_function",
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        call_target=InvokeFunctionCallTarget.opg_constructor,
        object_id=None,
        object_projection_graph_id=opg.id,
        function_id=function_id,
        args=JsonArray(args),
        kwargs=JsonObject({}),
        expected_graph_hash_pre=None,
        expected_head_commit_id=None,
        commit=True,
        publish=False,
    )
    return await runtime.invoker.invoke_function_with_index(
        index=index, request=request
    )


def _validate_environment_experience_materialization_result(
    *,
    environment_experience: EnvironmentExperience,
    spec: ExperiencePackageMaterializationSpec,
) -> None:
    if environment_experience.fqn_prefix != spec.package_fqn_prefix:
        raise RuntimeError(
            "Experience package materialization resolved EnvironmentExperience with unexpected fqn_prefix: "
            + f"expected={spec.package_fqn_prefix!r} actual={environment_experience.fqn_prefix!r}"
        )
    if environment_experience.title != spec.manifest_spec.experience.title:
        raise RuntimeError(
            "Experience package materialization resolved EnvironmentExperience with unexpected title: "
            + f"expected={spec.manifest_spec.experience.title!r} actual={environment_experience.title!r}"
        )
    if environment_experience.description != spec.manifest_spec.experience.description:
        raise RuntimeError(
            "Experience package materialization resolved EnvironmentExperience with unexpected description: "
            + f"expected={spec.manifest_spec.experience.description!r} actual={environment_experience.description!r}"
        )


def _validate_experience_package_materialization_result(
    *,
    experience_package: ExperiencePackage,
    environment_experience: EnvironmentExperience,
    spec: ExperiencePackageMaterializationSpec,
    language_package_refs: Sequence[ExperiencePackageLanguagePackageSnapshotRef],
) -> None:
    if experience_package.name != spec.package_name:
        raise RuntimeError(
            "Experience package materialization resolved ExperiencePackage with unexpected name: "
            + f"expected={spec.package_name!r} actual={experience_package.name!r}"
        )
    if experience_package.environment_experience_id != environment_experience.id:
        raise RuntimeError(
            "Experience package materialization resolved ExperiencePackage with unexpected "
            + "environment_experience_id: "
            + f"expected={environment_experience.id} actual={experience_package.environment_experience_id}"
        )
    if experience_package.source_code_package_id is not None:
        expected_source_code_package_id = experience_source_code_package_id(
            package_name=spec.package_name,
        )
        if experience_package.source_code_package_id != expected_source_code_package_id:
            raise RuntimeError(
                "Experience package materialization resolved ExperiencePackage with unexpected "
                + "source_code_package_id: "
                + f"expected={expected_source_code_package_id} "
                + f"actual={experience_package.source_code_package_id}"
            )
    else:
        raise RuntimeError(
            "Experience package materialization expected non-null source_code_package_id"
        )

    expected_dependency_ids = {
        experience_stable_ids.stable_experience_package_dependency_id(
            experience_package_id=experience_package.id,
            target_experience_package_id=experience_stable_ids.stable_experience_package_id(
                name=dependency.package_name,
            ),
        )
        for dependency in spec.manifest_spec.dependencies
        if dependency.kind is AwareExperienceDependencyKind.experience_package
    }
    actual_dependency_ids = {
        dependency.id
        for dependency in experience_package.experience_package_dependencies
    }
    if actual_dependency_ids != expected_dependency_ids:
        raise RuntimeError(
            "Experience package materialization resolved ExperiencePackage with unexpected "
            + "experience_package_dependencies: "
            + f"expected={sorted(str(item) for item in expected_dependency_ids)} "
            + f"actual={sorted(str(item) for item in actual_dependency_ids)}"
        )

    expected_attention_package_ids = {
        experience_stable_ids.stable_experience_package_attention_package_id(
            experience_package_id=experience_package.id,
            attention_package_id=stable_attention_package_id(
                name=dependency.package_name,
            ),
        )
        for dependency in spec.manifest_spec.dependencies
        if dependency.kind is AwareExperienceDependencyKind.attention_package
    }
    actual_attention_package_ids = {
        dependency.id for dependency in experience_package.attention_packages
    }
    if actual_attention_package_ids != expected_attention_package_ids:
        raise RuntimeError(
            "Experience package materialization resolved ExperiencePackage with unexpected "
            + "attention_packages: "
            + f"expected={sorted(str(item) for item in expected_attention_package_ids)} "
            + f"actual={sorted(str(item) for item in actual_attention_package_ids)}"
        )

    expected_language_package_ids = {
        experience_stable_ids.stable_experience_package_language_package_id(
            experience_package_id=experience_package.id,
            code_package_id=language_ref.code_package_id,
        )
        for language_ref in language_package_refs
    }
    actual_language_package_ids = {
        language_package.id for language_package in experience_package.language_packages
    }
    if actual_language_package_ids != expected_language_package_ids:
        raise RuntimeError(
            "Experience package materialization resolved ExperiencePackage with unexpected "
            + "language_packages: "
            + f"expected={sorted(str(item) for item in expected_language_package_ids)} "
            + f"actual={sorted(str(item) for item in actual_language_package_ids)}"
        )


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Experience package materialization path resolved outside workspace root: "
            + f"label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    relative_text = relative.as_posix()
    return relative_text or "."


async def _reset_projection_lane_with_duplicate_view_keys_if_needed(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
) -> bool:
    return await _lane_state.reset_projection_lane_with_duplicate_view_keys_if_needed(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        error_context=error_context,
        view_ids_by_projection_key_resolver=(
            _projection_experience_view_ids_by_projection_key_from_session
        ),
    )


__all__ = [
    "ActorMaterializationSpec",
    "ActionMaterializationSpec",
    "ActuatorConfigMaterializationSpec",
    "ConnectorConfigMaterializationSpec",
    "ConnectorInvocationActionConfigMaterializationSpec",
    "ConnectorInvocationRequestFieldMaterializationSpec",
    "ConnectorProviderMaterializationSpec",
    "EnvironmentProfileMaterializationSpec",
    "EnvironmentProfileProcessMaterializationSpec",
    "EnvironmentProfileThreadMaterializationSpec",
    "EnvironmentProfileThreadProjectionMaterializationSpec",
    "ExperiencePackageMaterializationResult",
    "ExperiencePackageMaterializationSpec",
    "ExperienceProfilePublicationSummary",
    "MaterializationExecutionError",
    "ProgramMaterializationSpec",
    "ProjectionExperienceMaterializationSpec",
    "ProjectionExperienceLayoutGraphBindingSpec",
    "ProjectionExperienceSectionSurfaceBindingSpec",
    "ProjectionExperienceSectionSurfaceMaterializationSpec",
    "ProjectionExperienceViewMaterializationSpec",
    "SensorConfigMaterializationSpec",
    "build_actor_materialization_plan",
    "build_action_materialization_plan",
    "build_connector_config_materialization_plan",
    "build_environment_profile_materialization_plan",
    "build_program_materialization_plan",
    "build_projection_materialization_plan",
    "build_section_surface_materialization_plan",
    "decode_actor_materialization_step_payload",
    "decode_connector_config_materialization_step_payload",
    "decode_environment_profile_materialization_step_payload",
    "decode_program_materialization_step_payload",
    "decode_projection_materialization_step_payload",
    "decode_section_surface_materialization_step_payload",
    "encode_actor_materialization_step_payload",
    "encode_connector_config_materialization_step_payload",
    "encode_environment_profile_materialization_step_payload",
    "encode_program_materialization_step_payload",
    "encode_projection_materialization_step_payload",
    "encode_section_surface_materialization_step_payload",
    "experience_source_code_package_config_id",
    "experience_source_code_package_id",
    "load_experience_compile_plan_payloads",
    "materialize_experience_compile_plan_actors",
    "materialize_experience_compile_plan_actions",
    "materialize_experience_compile_plan_connector_configs",
    "materialize_experience_compile_plan_environment_profiles",
    "materialize_experience_compile_plan_projections",
    "materialize_experience_compile_plan_programs",
    "materialize_experience_compile_plan_section_surfaces",
    "materialize_experience_compile_plan_graphs",
    "materialize_experience_actor_ontology",
    "materialize_experience_connector_config_ontology",
    "materialize_experience_environment_profile_ontology",
    "materialize_experience_package_from_manifest",
    "materialize_experience_program_ontology",
    "materialize_experience_projection_ontology",
    "materialize_experience_section_surface_ontology",
    "resolve_actor_materialization_specs",
    "resolve_activation_target_materialization_specs",
    "resolve_environment_profile_materialization_specs",
    "resolve_action_materialization_specs",
    "resolve_connector_config_materialization_specs",
    "resolve_experience_package_materialization_spec",
    "resolve_experience_profile_publication_summary",
    "resolve_program_materialization_specs",
    "resolve_projection_materialization_specs",
    "resolve_section_surface_materialization_specs",
    "_program_invoke_port_node_id",
    "_program_projection_catalog_branch_ids",
    "_resolve_program_port_node_snapshot",
    "_ActivationInvocationTargetSpec",
    "_ActivationTopologyStepContext",
    "_EndpointRequestAttributeRef",
    "_activation_action_request_bindings",
    "_activation_projection_spec_for_profile",
    "_endpoint_request_attributes_by_endpoint_ref",
]
