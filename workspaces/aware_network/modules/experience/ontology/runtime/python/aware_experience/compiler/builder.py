from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from aware_experience.actor.compiler import (
    load_actor_role_ownership_from_sources,
)
from aware_experience.actor.contracts import (
    load_actor_role_contract,
    load_actor_role_contract_from_runtime_manifests,
)
from aware_experience.action.compiler import (
    load_dependency_action_ownership_from_snapshot,
    load_action_ownership_from_sources,
)
from aware_experience.connector.compiler import (
    load_dependency_connector_ownership_from_snapshot,
    load_connector_ownership_from_sources,
)
from aware_experience.compiler.models import (
    ExperienceActionOwnership,
    ExperienceActionProgramBindingOwnership,
    ExperienceActuatorConfigOwnership,
    ExperienceActorOwnership,
    ExperienceActorRoleContract,
    ExperienceCompilePlan,
    ExperienceCompilePlanArtifact,
    ExperienceConnectorConfigOwnership,
    ExperienceConnectorInvocationActionConfigOwnership,
    ExperienceConnectorProviderOwnership,
    ExperienceEnvironmentActorBinding,
    ExperienceEnvironmentEventActionOwnership,
    ExperienceEnvironmentEventOwnership,
    ExperienceEnvironmentProfileActorSpec,
    ExperienceEnvironmentProfileOwnership,
    ExperienceEnvironmentProfileRoleSpec,
    ExperienceViewStateModelContract,
    ExperienceEnvironmentOwnership,
    ExperienceEnvironmentProgramOwnership,
    ExperienceEventBindingOwnership,
    ExperienceEventOwnership,
    ExperienceProgramOwnership,
    ExperienceProjectionBranchOwnership,
    ExperienceProjectionAPIOwnership,
    ExperienceProjectionAPIContractOwnership,
    ExperienceProjectionAPIContractParamOwnership,
    ExperienceProjectionExperienceOwnership,
    ExperienceProjectionObservableOwnership,
    ExperienceProjectionViewOwnership,
    ExperienceRoleOwnership,
    ExperienceSensorConfigOwnership,
    ExperienceViewApiOwnership,
    ExperienceViewApiViewOwnership,
)
from aware_experience.compiler.structure import (
    load_environment_projection_observable_truth,
    load_environment_projection_observable_truth_from_runtime_manifests,
    load_environment_projection_truth,
    load_environment_projection_truth_from_runtime_manifests,
)
from aware_experience.compiler.workspace import ExperienceWorkspaceSnapshot
from aware_experience.manifest.spec import AwareExperienceDependencyKind
from aware_experience.event.compiler import (
    load_dependency_event_ownership_from_snapshot,
    load_event_ownership_from_sources,
)
from aware_experience.environment.compiler import (
    load_environment_ownership_from_sources,
)
from aware_experience.environment_profile.compiler import (
    load_environment_profile_ownership_from_sources,
)
from aware_experience.graph.compiler import (
    load_graph_ownership_from_sources,
)
from aware_experience.graph.ontology import (
    build_graph_ontology_plans,
    encode_graph_ontology_plan_payload,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from aware_experience.program.compiler import (
    load_program_ownership_from_sources,
    select_program_source_files,
)
from aware_experience.view_contracts import (
    load_view_state_model_contracts_from_sources,
)
from aware_experience.view_api import build_experience_view_api_ownership


def build_experience_compile_plan(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
    environment_runtime_manifest_paths: Sequence[Path] = (),
    environment_composition_manifest_path: Path | None = None,
    repo_root: Path | None = None,
) -> ExperienceCompilePlan:
    return build_experience_compile_plan_with_environment_validation(
        snapshot=snapshot,
        environment_runtime_manifest_paths=environment_runtime_manifest_paths,
        environment_composition_manifest_path=environment_composition_manifest_path,
        repo_root=repo_root,
    )


def build_experience_compile_plan_with_environment_validation(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
    environment_runtime_manifest_paths: Sequence[Path] = (),
    environment_composition_manifest_path: Path | None = None,
    repo_root: Path | None = None,
) -> ExperienceCompilePlan:
    package_root = snapshot.package_root.resolve()
    source_files = tuple(path.as_posix() for path in snapshot.source_files)
    program_source_files = select_program_source_files(snapshot.source_files)
    actor_role_contract: ExperienceActorRoleContract | None = None
    projection_truth_by_name = None
    projection_observable_truth_by_name = None
    if environment_runtime_manifest_paths and environment_composition_manifest_path:
        raise ValueError(
            "Pass environment_runtime_manifest_paths or "
            "environment_composition_manifest_path, not both"
        )
    if environment_runtime_manifest_paths:
        if repo_root is None:
            raise ValueError(
                "repo_root is required when environment runtime manifest validation "
                "is enabled"
            )
        actor_role_contract = load_actor_role_contract_from_runtime_manifests(
            environment_runtime_manifest_paths=environment_runtime_manifest_paths,
            repo_root=repo_root,
        )
        projection_truth_by_name = (
            load_environment_projection_truth_from_runtime_manifests(
                environment_runtime_manifest_paths=environment_runtime_manifest_paths,
                repo_root=repo_root,
            )
        )
        projection_observable_truth_by_name = (
            load_environment_projection_observable_truth_from_runtime_manifests(
                environment_runtime_manifest_paths=environment_runtime_manifest_paths,
                repo_root=repo_root,
            )
        )
    elif environment_composition_manifest_path is not None:
        if repo_root is None:
            raise ValueError(
                "repo_root is required when environment composition validation is enabled"
            )
        actor_role_contract = load_actor_role_contract(
            composition_manifest_path=environment_composition_manifest_path,
            repo_root=repo_root,
        )
        projection_truth_by_name = load_environment_projection_truth(
            composition_manifest_path=environment_composition_manifest_path,
            repo_root=repo_root,
        )
        projection_observable_truth_by_name = (
            load_environment_projection_observable_truth(
                composition_manifest_path=environment_composition_manifest_path,
                repo_root=repo_root,
            )
        )
    view_state_model_contracts = tuple(
        ExperienceViewStateModelContract(
            state_model_ref=contract.state_model_ref,
            class_config_id=contract.class_config_id,
            source_path=contract.source_path,
        )
        for contract in load_view_state_model_contracts_from_sources(
            package_root=package_root,
            source_files=snapshot.source_files,
            fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip(),
            package_name=(snapshot.spec.experience.package_name or "").strip(),
        )
    )
    role_ownership, actor_ownership, environment_actor_bindings = (
        load_actor_role_ownership_from_sources(
            package_root=package_root,
            source_files=snapshot.source_files,
        )
    )
    action_ownership = load_action_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
        package_name=(snapshot.spec.experience.package_name or "").strip() or None,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip() or None,
    ) + load_dependency_action_ownership_from_snapshot(snapshot=snapshot)
    connector_ownership = load_connector_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
        package_name=(snapshot.spec.experience.package_name or "").strip() or None,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip() or None,
    )
    action_target_ownership = load_dependency_connector_ownership_from_snapshot(
        snapshot=snapshot
    )
    environment_ownership = load_environment_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
    )
    if (
        role_ownership or actor_ownership or environment_actor_bindings
    ) and actor_role_contract is None:
        raise ValueError(
            "Actor/role declarations require ActorConfig+RoleConfig contracts in composed structure truth"
        )
    projection_experience_ownership = load_projection_experience_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
        projection_observable_truth_by_name=projection_observable_truth_by_name,
    )
    view_api_ownership = build_experience_view_api_ownership(
        package_name=(snapshot.spec.experience.package_name or "").strip(),
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip(),
        projection_experience_ownership=projection_experience_ownership,
        view_state_model_contracts=view_state_model_contracts,
    )
    if projection_experience_ownership and projection_observable_truth_by_name is None:
        raise ValueError(
            "Experience projection declarations require composed projection observable truth"
        )
    events = load_event_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
        projection_truth_by_name=projection_truth_by_name,
        package_name=(snapshot.spec.experience.package_name or "").strip() or None,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip() or None,
    ) + load_dependency_event_ownership_from_snapshot(
        snapshot=snapshot,
        projection_truth_by_name=projection_truth_by_name,
    )
    environment_profile_ownership: tuple[ExperienceEnvironmentProfileOwnership, ...] = (
        load_environment_profile_ownership_from_sources(
            package_root=package_root,
            source_files=snapshot.source_files,
            projection_experience_ownership=projection_experience_ownership,
            event_ownership=events,
            external_projection_experience_prefixes=(
                _dependency_projection_experience_prefixes(snapshot=snapshot)
            ),
        )
    )
    environment_profile_ownership = publish_environment_profile_actor_role_ownership(
        environment_profile_ownership=environment_profile_ownership,
        role_ownership=role_ownership,
        actor_ownership=actor_ownership,
        environment_actor_bindings=environment_actor_bindings,
        environment_ownership=environment_ownership,
    )
    graph_ownership = load_graph_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
        projection_experience_ownership=projection_experience_ownership,
    )
    # Fail closed: every compiled graph token must map to explicit ontology operations.
    _ = build_graph_ontology_plans(
        projection_experience_ownership=projection_experience_ownership,
        graph_ownership=graph_ownership,
    )
    projection_api_ownership: tuple[ExperienceProjectionAPIOwnership, ...] = ()
    programs = load_program_ownership_from_sources(
        package_root=package_root,
        source_files=program_source_files,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip(),
        projection_experience_ownership=projection_experience_ownership,
    )
    program_symbol_catalog = {
        _normalize_symbol(item.name)
        for item in programs
        if _normalize_symbol(item.name)
    }
    program_symbol_catalog.update(
        _normalize_symbol(item.ref) for item in programs if _normalize_symbol(item.ref)
    )
    for action_item in action_ownership:
        if action_item.is_dependency:
            continue
        for binding in action_item.program_bindings:
            program_symbol = _normalize_symbol(binding.program)
            if program_symbol and program_symbol not in program_symbol_catalog:
                raise ValueError(
                    f"Action declaration {action_item.symbol!r} references unknown program "
                    f"{binding.program!r} (source={action_item.source_path})"
                )
    if environment_ownership:
        event_ref_catalog: dict[str, ExperienceEventOwnership] = {}
        for item in events:
            if not item.is_dependency:
                _register_event_reference(
                    reference=item.symbol,
                    owner=item,
                    catalog=event_ref_catalog,
                )
                _register_event_reference(
                    reference=item.event_name,
                    owner=item,
                    catalog=event_ref_catalog,
                )
            for reference in _qualified_event_references(item):
                _register_event_reference(
                    reference=reference,
                    owner=item,
                    catalog=event_ref_catalog,
                )
        action_ownership_by_ref: dict[str, ExperienceActionOwnership] = {}
        for item in action_ownership:
            if not item.is_dependency:
                _register_action_reference(
                    reference=item.symbol,
                    owner=item,
                    catalog=action_ownership_by_ref,
                )
                _register_action_reference(
                    reference=item.action_name,
                    owner=item,
                    catalog=action_ownership_by_ref,
                )
            for reference in _qualified_action_references(item):
                _register_action_reference(
                    reference=reference,
                    owner=item,
                    catalog=action_ownership_by_ref,
                )
        experience_symbol_catalog = {
            _normalize_symbol(item.name)
            for item in projection_experience_ownership
            if _normalize_symbol(item.name)
        }
        for environment_item in environment_ownership:
            environment_program_config_catalog: set[str] = set()
            for experience_item in environment_item.experiences:
                experience_symbol = _normalize_symbol(experience_item)
                if (
                    experience_symbol
                    and experience_symbol not in experience_symbol_catalog
                ):
                    raise ValueError(
                        f"Environment declaration {environment_item.name!r} references unknown experience "
                        f"{experience_item!r} (source={environment_item.source_path})"
                    )
            for program_item in environment_item.programs:
                config_symbol = _normalize_symbol(program_item.program_config)
                if config_symbol and config_symbol not in program_symbol_catalog:
                    raise ValueError(
                        f"Environment declaration {environment_item.name!r} references unknown program_config "
                        f"{program_item.program_config!r} (source={environment_item.source_path})"
                    )
                if config_symbol:
                    environment_program_config_catalog.add(config_symbol)
                impl_symbol = _normalize_symbol(program_item.program_impl)
                if impl_symbol and impl_symbol not in program_symbol_catalog:
                    raise ValueError(
                        f"Environment declaration {environment_item.name!r} references unknown program_impl "
                        f"{program_item.program_impl!r} (source={environment_item.source_path})"
                    )
            for event_item in environment_item.events:
                event_ref_key = _event_reference_key(event_item.event)
                if event_ref_key and event_ref_key not in event_ref_catalog:
                    raise ValueError(
                        f"Environment declaration {environment_item.name!r} references unknown event "
                        f"{event_item.event!r} (source={environment_item.source_path})"
                    )
                for event_action_item in event_item.actions:
                    action_ref_key = _action_reference_key(event_action_item.action)
                    if action_ref_key and action_ref_key not in action_ownership_by_ref:
                        raise ValueError(
                            "Environment declaration "
                            f"{environment_item.name!r} event {event_item.event!r} references "
                            f"unknown action {event_action_item.action!r} "
                            f"(source={environment_item.source_path})"
                        )
                    owned_action = action_ownership_by_ref.get(action_ref_key)
                    if owned_action is None:
                        continue
                    if owned_action.is_dependency:
                        continue
                    for binding in owned_action.program_bindings:
                        binding_symbol = _normalize_symbol(binding.program)
                        if (
                            binding_symbol
                            and binding_symbol not in environment_program_config_catalog
                        ):
                            raise ValueError(
                                "Environment declaration "
                                f"{environment_item.name!r} action {event_action_item.action!r} binding "
                                f"program {binding.program!r} is not declared as environment program_config "
                                f"(source={environment_item.source_path})"
                            )
    return ExperienceCompilePlan(
        schema_version=1,
        package_name=(snapshot.spec.experience.package_name or "").strip(),
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip(),
        environment_handle=(snapshot.spec.build.environment_handle or "").strip(),
        source_files=source_files,
        view_state_model_contracts=view_state_model_contracts,
        view_api_ownership=view_api_ownership,
        actor_role_contract=actor_role_contract,
        role_ownership=role_ownership,
        actor_ownership=actor_ownership,
        environment_actor_bindings=environment_actor_bindings,
        action_ownership=action_ownership,
        connector_ownership=connector_ownership,
        action_target_ownership=action_target_ownership,
        environment_ownership=environment_ownership,
        projection_experience_ownership=projection_experience_ownership,
        environment_profile_ownership=environment_profile_ownership,
        projection_api_ownership=projection_api_ownership,
        graph_ownership=graph_ownership,
        program_ownership=programs,
        event_ownership=events,
    )


def publish_environment_profile_actor_role_ownership(
    *,
    environment_profile_ownership: tuple[ExperienceEnvironmentProfileOwnership, ...],
    role_ownership: tuple[ExperienceRoleOwnership, ...],
    actor_ownership: tuple[ExperienceActorOwnership, ...],
    environment_actor_bindings: tuple[ExperienceEnvironmentActorBinding, ...],
    environment_ownership: tuple[ExperienceEnvironmentOwnership, ...],
) -> tuple[ExperienceEnvironmentProfileOwnership, ...]:
    published_roles = tuple(
        sorted(
            (
                ExperienceEnvironmentProfileRoleSpec(
                    name=role.name,
                    capabilities=role.capabilities,
                )
                for role in role_ownership
            ),
            key=lambda item: item.name.casefold(),
        )
    )
    environments_by_key = {
        _normalize_symbol(item.name): item
        for item in environment_ownership
        if _normalize_symbol(item.name)
    }
    for binding in environment_actor_bindings:
        environment_key = _normalize_symbol(binding.environment)
        if environment_key and environment_key not in environments_by_key:
            raise ValueError(
                "Environment actor binding references unknown environment "
                f"{binding.environment!r} (source={binding.source_path})"
            )

    actor_ownership_by_name = {
        _normalize_symbol(item.name): item
        for item in actor_ownership
        if _normalize_symbol(item.name)
    }
    bindings_by_environment: dict[str, list[ExperienceEnvironmentActorBinding]] = {}
    for binding in environment_actor_bindings:
        environment_key = _normalize_symbol(binding.environment)
        if not environment_key:
            continue
        bindings_by_environment.setdefault(environment_key, []).append(binding)

    environments_by_experience: dict[str, list[ExperienceEnvironmentOwnership]] = {}
    for environment_item in environment_ownership:
        for experience_name in environment_item.experiences:
            experience_key = _normalize_symbol(experience_name)
            if not experience_key:
                continue
            environments_by_experience.setdefault(experience_key, []).append(
                environment_item
            )

    published_profiles: list[ExperienceEnvironmentProfileOwnership] = []
    for profile in environment_profile_ownership:
        experience_key = _normalize_symbol(profile.experience_name)
        matched_environments = environments_by_experience.get(experience_key, [])
        if len(matched_environments) > 1:
            binding_count = sum(
                len(bindings_by_environment.get(_normalize_symbol(item.name), ()))
                for item in matched_environments
            )
            if binding_count:
                raise ValueError(
                    "Experience profile actor publication is ambiguous across multiple environments for "
                    f"{profile.experience_name!r}: "
                    + ", ".join(sorted(item.name for item in matched_environments))
                )
        published_profiles.append(
            replace(
                profile,
                roles=published_roles,
                actors=(
                    _build_published_profile_actor_specs(
                        bindings=bindings_by_environment.get(
                            _normalize_symbol(matched_environments[0].name),
                            [],
                        ),
                        actor_ownership_by_name=actor_ownership_by_name,
                    )
                    if len(matched_environments) == 1
                    else ()
                ),
            )
        )
    return tuple(published_profiles)


def emit_experience_compile_plan_artifact(
    *,
    plan: ExperienceCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> ExperienceCompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_plan(plan=plan)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "experience.compile_plan.json").resolve()
    artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ExperienceCompilePlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def _encode_plan(*, plan: ExperienceCompilePlan) -> dict[str, object]:
    graph_ontology_payload = encode_graph_ontology_plan_payload(
        plans=build_graph_ontology_plans(
            projection_experience_ownership=plan.projection_experience_ownership,
            graph_ownership=plan.graph_ownership,
        )
    )
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "environment_handle": plan.environment_handle,
        "source_files": list(plan.source_files),
        "view_state_model_contracts": [
            {
                "state_model_ref": contract.state_model_ref,
                "class_config_id": str(contract.class_config_id),
                "source_path": contract.source_path,
            }
            for contract in plan.view_state_model_contracts
        ],
        "view_api_ownership": (
            _encode_view_api_ownership(view_api=plan.view_api_ownership)
            if plan.view_api_ownership is not None
            else None
        ),
        "actor_role_contract": (
            {
                "actor_config_class_fqn": plan.actor_role_contract.actor_config_class_fqn,
                "role_config_class_fqn": plan.actor_role_contract.role_config_class_fqn,
            }
            if plan.actor_role_contract is not None
            else None
        ),
        "role_ownership": [
            {
                "name": role.name,
                "source_path": role.source_path,
                "capabilities": list(role.capabilities),
            }
            for role in plan.role_ownership
        ],
        "actor_ownership": [
            {
                "name": actor.name,
                "kind": actor.kind,
                "roles": list(actor.roles),
                "source_path": actor.source_path,
            }
            for actor in plan.actor_ownership
        ],
        "environment_actor_bindings": [
            {
                "environment": binding.environment,
                "actor": binding.actor,
                "roles": list(binding.roles),
                "source_path": binding.source_path,
            }
            for binding in plan.environment_actor_bindings
        ],
        "action_ownership": [
            {
                "symbol": item.symbol,
                "action_name": item.action_name,
                "source_path": item.source_path,
                "package_name": item.package_name,
                "fqn_prefix": item.fqn_prefix,
                "is_dependency": item.is_dependency,
                "params": list(item.params),
                "program_bindings": [
                    {
                        "program": binding.program,
                        "args": list(binding.args),
                    }
                    for binding in item.program_bindings
                ],
            }
            for item in plan.action_ownership
        ],
        "connector_ownership": [
            _encode_connector_ownership(connector=connector)
            for connector in plan.connector_ownership
        ],
        "action_target_ownership": [
            _encode_connector_ownership(connector=connector)
            for connector in plan.action_target_ownership
        ],
        "environment_ownership": [
            {
                "name": item.name,
                "source_path": item.source_path,
                "experiences": list(item.experiences),
                "programs": [
                    {
                        "program_config": program.program_config,
                        "program_impl": program.program_impl,
                    }
                    for program in item.programs
                ],
                "events": [
                    {
                        "event": event.event,
                        "node_scopes": [
                            {"node_ref": node_scope.node_ref}
                            for node_scope in event.node_scopes
                        ],
                        "actions": [
                            {"action": action.action} for action in event.actions
                        ],
                    }
                    for event in item.events
                ],
            }
            for item in plan.environment_ownership
        ],
        "projection_experience_ownership": [
            {
                "name": item.name,
                "projection": item.projection,
                "source_path": item.source_path,
                "branches": [
                    {
                        "name": branch.name,
                        "is_default": branch.is_default,
                        "source_path": branch.source_path,
                    }
                    for branch in item.branches
                ],
                "observables": [
                    {
                        "key": observable.key,
                        "source_path": observable.source_path,
                        "views": [
                            {
                                "key": view.key,
                                "is_default": view.is_default,
                                "state_model_ref": view.state_model_ref,
                                "api_view_ref": view.api_view_ref,
                                "state_provider_ref": view.state_provider_ref,
                                "invocation_actions": [
                                    {
                                        "key": action.key,
                                        "api_view_capability_endpoint_id": (
                                            str(action.api_view_capability_endpoint_id)
                                            if action.api_view_capability_endpoint_id
                                            else None
                                        ),
                                        "endpoint_ref": action.endpoint_ref,
                                        "api_capability_endpoint_id": (
                                            str(action.api_capability_endpoint_id)
                                            if action.api_capability_endpoint_id
                                            else None
                                        ),
                                        "sdk_operation_api_view_capability_endpoint_id": (
                                            str(
                                                action.sdk_operation_api_view_capability_endpoint_id
                                            )
                                            if action.sdk_operation_api_view_capability_endpoint_id
                                            else None
                                        ),
                                        "sdk_operation_id": (
                                            str(action.sdk_operation_id)
                                            if action.sdk_operation_id
                                            else None
                                        ),
                                        "label": action.label,
                                        "receipt_policy": action.receipt_policy,
                                        "confirmation_policy": action.confirmation_policy,
                                        "optimistic_policy": action.optimistic_policy,
                                        "source_path": action.source_path,
                                    }
                                    for action in view.invocation_actions
                                ],
                                "source_path": view.source_path,
                            }
                            for view in observable.views
                        ],
                    }
                    for observable in item.observables
                ],
                "nodes": [
                    {
                        "name": node.name,
                        "node_ref": node.node_ref,
                        "source_path": node.source_path,
                        "params": [
                            {
                                "name": param.name,
                                "type_ref": param.type_ref,
                            }
                            for param in node.params
                        ],
                        "identities": [
                            {
                                "key": identity.key,
                                "source_path": identity.source_path,
                            }
                            for identity in node.identities
                        ],
                    }
                    for node in item.nodes
                ],
                "section_surfaces": [
                    {
                        "surface_key": surface.surface_key,
                        "section_key": surface.section_key,
                        "observable_key": surface.observable_key,
                        "view_key": surface.view_key,
                        "source_path": surface.source_path,
                        "source_surface_key": surface.source_surface_key,
                        "graph_identity_ref": surface.graph_identity_ref,
                        "node_identity_ref": surface.node_identity_ref,
                    }
                    for surface in item.section_surfaces
                ],
            }
            for item in plan.projection_experience_ownership
        ],
        "environment_profile_ownership": [
            {
                "experience_name": item.experience_name,
                "key": item.key,
                "source_path": item.source_path,
                "title": item.title,
                "description": item.description,
                "narrative": item.narrative,
                "roles": [
                    {
                        "name": role.name,
                        "description": role.description,
                        "capabilities": list(role.capabilities),
                    }
                    for role in item.roles
                ],
                "actors": [
                    {
                        "key": actor.key,
                        "title": actor.title,
                        "description": actor.description,
                        "type": actor.actor_type,
                        "role_names": list(actor.role_names),
                    }
                    for actor in item.actors
                ],
                "process_configs": [
                    {
                        "type": process.type,
                        "key": process.key,
                        "process_key": process.process_key,
                        "source_path": process.source_path,
                        "title": process.title,
                        "description": process.description,
                        "shape": process.shape,
                        "position": process.position,
                        "is_bootstrap_default": process.is_bootstrap_default,
                        "narrative": process.narrative,
                        "intent": process.intent,
                        "thread_configs": [
                            {
                                "key": thread.key,
                                "thread_key": thread.thread_key,
                                "source_path": thread.source_path,
                                "title": thread.title,
                                "description": thread.description,
                                "workspace_view_key": thread.workspace_view_key,
                                "position": thread.position,
                                "is_default": thread.is_default,
                                "narrative": thread.narrative,
                                "intent": thread.intent,
                                "state_prompt_template": thread.state_prompt_template,
                                "projection_experiences": [
                                    {
                                        "projection_experience_name": projection.projection_experience_name,
                                        "source_path": projection.source_path,
                                        "view_key": projection.view_key,
                                        "is_default": projection.is_default,
                                    }
                                    for projection in thread.projection_experiences
                                ],
                                "layout_configs": [
                                    {
                                        "layout_key": layout.layout_key,
                                        "source_path": layout.source_path,
                                        "key": layout.key,
                                        "position": layout.position,
                                        "is_default": layout.is_default,
                                        "narrative": layout.narrative,
                                        "intent": layout.intent,
                                        "sections": [
                                            {
                                                "section_key": section.section_key,
                                                "projection_experience_name": section.projection_experience_name,
                                                "view_key": section.view_key,
                                                "source_path": section.source_path,
                                                "key": section.key,
                                                "section_graph_binding_key": section.section_graph_binding_key,
                                                "position": section.position,
                                                "is_default": section.is_default,
                                                "narrative": section.narrative,
                                                "intent": section.intent,
                                            }
                                            for section in layout.sections
                                        ],
                                    }
                                    for layout in thread.layout_configs
                                ],
                            }
                            for thread in process.thread_configs
                        ],
                    }
                    for process in item.process_configs
                ],
                "view_event_transitions": [
                    {
                        "key": transition.key,
                        "source_projection_experience_name": (
                            transition.source_projection_experience_name
                        ),
                        "source_view_key": transition.source_view_key,
                        "trigger_event_ref": transition.trigger_event_ref,
                        "trigger_event_config_ref": transition.trigger_event_config_ref,
                        "target_projection_experience_name": (
                            transition.target_projection_experience_name
                        ),
                        "target_section_graph_binding_key": (
                            transition.target_section_graph_binding_key
                        ),
                        "source_path": transition.source_path,
                        "name": transition.name,
                        "rationale": transition.rationale,
                        "idempotency_policy": transition.idempotency_policy,
                    }
                    for transition in item.view_event_transitions
                ],
            }
            for item in plan.environment_profile_ownership
        ],
        "projection_api_ownership": [
            {
                "name": item.name,
                "projection": item.projection,
                "source_path": item.source_path,
                "contracts": [
                    {
                        "name": contract.name,
                        "source_path": contract.source_path,
                        "parent_class": contract.parent_class,
                        "relationship_attribute": contract.relationship_attribute,
                        "key_attribute": contract.key_attribute,
                        "params": [
                            {
                                "name": param.name,
                                "type_ref": param.type_ref,
                            }
                            for param in contract.params
                        ],
                    }
                    for contract in item.contracts
                ],
            }
            for item in plan.projection_api_ownership
        ],
        "graph_ownership": [
            {
                "name": item.name,
                "experience": item.experience,
                "source_path": item.source_path,
                "root": item.root,
                "edges": [
                    {
                        "parent": edge.parent,
                        "child": edge.child,
                        "source_path": edge.source_path,
                    }
                    for edge in item.edges
                ],
            }
            for item in plan.graph_ownership
        ],
        "graph_ontology": graph_ontology_payload,
        "program_ownership": [
            {
                "ref": p.ref,
                "name": p.name,
                "path": p.path,
                "dependencies": list(p.dependencies),
                "required_symbols": list(p.required_symbols),
                "optional_symbols": list(p.optional_symbols),
                "required_projection_ids": list(p.required_projection_ids),
                "required_projection_node_ids": list(p.required_projection_node_ids),
                "required_projection_node_identity_ids": list(
                    p.required_projection_node_identity_ids
                ),
                "invocation_plan_artifact": (
                    dict(p.invocation_plan_artifact)
                    if p.invocation_plan_artifact is not None
                    else None
                ),
                "program_config_plan_artifact": (
                    dict(p.program_config_plan_artifact)
                    if p.program_config_plan_artifact is not None
                    else None
                ),
                "program_apply_calls_artifact": (
                    dict(p.program_apply_calls_artifact)
                    if p.program_apply_calls_artifact is not None
                    else None
                ),
            }
            for p in plan.program_ownership
        ],
        "event_ownership": [
            {
                "symbol": e.symbol,
                "event_name": e.event_name,
                "renderer_key": e.renderer_key,
                "title": e.title,
                "description": e.description,
                "source_path": e.source_path,
                "package_name": e.package_name,
                "fqn_prefix": e.fqn_prefix,
                "is_dependency": e.is_dependency,
                "bindings": [
                    {
                        "projection": b.projection,
                        "type_ref": b.type_ref,
                        "class_fqn": b.class_fqn,
                        "operation": b.operation,
                        "attribute": b.attribute,
                    }
                    for b in e.bindings
                ],
            }
            for e in plan.event_ownership
        ],
    }


def _encode_connector_ownership(
    *,
    connector: ExperienceConnectorConfigOwnership,
) -> dict[str, object]:
    return {
        "connector_key": connector.connector_key,
        "connector_kind": connector.connector_kind,
        "source_path": connector.source_path,
        "package_name": connector.package_name,
        "fqn_prefix": connector.fqn_prefix,
        "is_dependency": connector.is_dependency,
        "label": connector.label,
        "description": connector.description,
        "providers": [
            _encode_connector_provider_ownership(provider=provider)
            for provider in connector.providers
        ],
        "sensor_configs": [
            _encode_sensor_config_ownership(sensor=sensor)
            for sensor in connector.sensor_configs
        ],
        "actuator_configs": [
            _encode_actuator_config_ownership(actuator=actuator)
            for actuator in connector.actuator_configs
        ],
    }


def _encode_connector_provider_ownership(
    *,
    provider: ExperienceConnectorProviderOwnership,
) -> dict[str, object]:
    return {
        "provider_key": provider.provider_key,
        "provider_kind": provider.provider_kind,
        "source_path": provider.source_path,
        "provider_ref": provider.provider_ref,
        "label": provider.label,
        "description": provider.description,
    }


def _encode_sensor_config_ownership(
    *,
    sensor: ExperienceSensorConfigOwnership,
) -> dict[str, object]:
    return {
        "sensor_key": sensor.sensor_key,
        "sensor_kind": sensor.sensor_kind,
        "source_path": sensor.source_path,
        "source_ref": sensor.source_ref,
        "observed_state_node_refs": list(sensor.observed_state_node_refs),
        "label": sensor.label,
        "description": sensor.description,
        "invocation_action_configs": [
            _encode_connector_invocation_action_config_ownership(invocation=invocation)
            for invocation in sensor.invocation_action_configs
        ],
    }


def _encode_actuator_config_ownership(
    *,
    actuator: ExperienceActuatorConfigOwnership,
) -> dict[str, object]:
    return {
        "actuator_key": actuator.actuator_key,
        "actuator_kind": actuator.actuator_kind,
        "source_path": actuator.source_path,
        "target_ref": actuator.target_ref,
        "affected_state_node_refs": list(actuator.affected_state_node_refs),
        "label": actuator.label,
        "description": actuator.description,
        "invocation_action_configs": [
            _encode_connector_invocation_action_config_ownership(invocation=invocation)
            for invocation in actuator.invocation_action_configs
        ],
    }


def _encode_connector_invocation_action_config_ownership(
    *,
    invocation: ExperienceConnectorInvocationActionConfigOwnership,
) -> dict[str, object]:
    return {
        "action_key": invocation.action_key,
        "action_kind": invocation.action_kind,
        "target_ref": invocation.target_ref,
        "source_path": invocation.source_path,
        "label": invocation.label,
        "receipt_policy": invocation.receipt_policy,
        "confirmation_policy": invocation.confirmation_policy,
        "optimistic_policy": invocation.optimistic_policy,
    }


def _encode_view_api_ownership(
    *,
    view_api: ExperienceViewApiOwnership,
) -> dict[str, object]:
    return {
        "package_name": view_api.package_name,
        "fqn_prefix": view_api.fqn_prefix,
        "api_name": view_api.api_name,
        "source_path": view_api.source_path,
        "views": [_encode_view_api_view(view=view) for view in view_api.views],
    }


def _encode_view_api_view(
    *,
    view: ExperienceViewApiViewOwnership,
) -> dict[str, object]:
    return {
        "api_name": view.api_name,
        "view_name": view.view_name,
        "experience_name": view.experience_name,
        "observable_key": view.observable_key,
        "view_key": view.view_key,
        "observable_ref": view.observable_ref,
        "view_ref": view.view_ref,
        "projection_view_key": view.projection_view_key,
        "state_model_ref": view.state_model_ref,
        "state_model_id": (
            str(view.state_model_id) if view.state_model_id is not None else None
        ),
        "is_default": view.is_default,
        "source_path": view.source_path,
        "invocation_actions": [
            {
                "key": action.key,
                "source_path": action.source_path,
                "endpoint_ref": action.endpoint_ref,
                "api_view_capability_endpoint_id": (
                    str(action.api_view_capability_endpoint_id)
                    if action.api_view_capability_endpoint_id is not None
                    else None
                ),
                "api_capability_endpoint_id": (
                    str(action.api_capability_endpoint_id)
                    if action.api_capability_endpoint_id is not None
                    else None
                ),
                "sdk_operation_api_view_capability_endpoint_id": (
                    str(action.sdk_operation_api_view_capability_endpoint_id)
                    if action.sdk_operation_api_view_capability_endpoint_id is not None
                    else None
                ),
                "sdk_operation_id": (
                    str(action.sdk_operation_id)
                    if action.sdk_operation_id is not None
                    else None
                ),
                "label": action.label,
                "receipt_policy": action.receipt_policy,
                "confirmation_policy": action.confirmation_policy,
                "optimistic_policy": action.optimistic_policy,
            }
            for action in view.invocation_actions
        ],
    }


def _build_published_profile_actor_specs(
    *,
    bindings: list[ExperienceEnvironmentActorBinding],
    actor_ownership_by_name: dict[str, ExperienceActorOwnership],
) -> tuple[ExperienceEnvironmentProfileActorSpec, ...]:
    actor_roles_by_name: dict[str, set[str]] = {}
    for binding in bindings:
        actor_key = _normalize_symbol(binding.actor)
        if not actor_key:
            continue
        actor_item = actor_ownership_by_name.get(actor_key)
        if actor_item is None:
            continue
        role_names = actor_roles_by_name.setdefault(actor_key, set(actor_item.roles))
        role_names.update(role_name for role_name in binding.roles if role_name)

    actor_specs: list[ExperienceEnvironmentProfileActorSpec] = []
    for actor_key, role_names in actor_roles_by_name.items():
        actor_item = actor_ownership_by_name[actor_key]
        actor_specs.append(
            ExperienceEnvironmentProfileActorSpec(
                key=actor_item.name,
                actor_type=(actor_item.kind or "").strip() or None,
                role_names=tuple(sorted(role_names, key=str.casefold)),
            )
        )
    actor_specs.sort(key=lambda item: item.key.casefold())
    return tuple(actor_specs)


def _normalize_symbol(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _dependency_projection_experience_prefixes(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
) -> tuple[str, ...]:
    prefixes: set[str] = set()
    for dependency in snapshot.spec.dependencies:
        if dependency.kind is not AwareExperienceDependencyKind.experience_package:
            continue
        package_name = (dependency.package_name or "").strip()
        if not package_name:
            continue
        prefixes.add(package_name)
        prefixes.add(package_name.replace("-", "_"))
        prefixes.add(package_name.replace("-", "."))
    return tuple(sorted(prefixes, key=str.casefold))


def _event_reference_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    return "".join(ch for ch in token.casefold() if ch.isalnum())


def _register_event_reference(
    *,
    reference: str,
    owner: ExperienceEventOwnership,
    catalog: dict[str, ExperienceEventOwnership],
) -> None:
    ref_key = _event_reference_key(reference)
    if not ref_key:
        return
    prior = catalog.get(ref_key)
    if prior is None or prior == owner:
        catalog[ref_key] = owner
        return
    raise ValueError(
        "Ambiguous event reference key "
        f"{ref_key!r} between events {prior.symbol!r} ({prior.event_name!r}) "
        f"and {owner.symbol!r} ({owner.event_name!r}); use disambiguated event names/symbols"
    )


def _qualified_event_references(owner: ExperienceEventOwnership) -> tuple[str, ...]:
    prefixes = _event_owner_prefixes(owner)
    references: list[str] = []
    for prefix in prefixes:
        references.append(f"{prefix}.{owner.symbol}")
        references.append(f"{prefix}.{owner.event_name}")
    return tuple(dict.fromkeys(references))


def _event_owner_prefixes(owner: ExperienceEventOwnership) -> tuple[str, ...]:
    prefixes: list[str] = []
    for raw in (owner.fqn_prefix, owner.package_name):
        token = _event_owner_prefix(raw)
        if token:
            prefixes.append(token)
    return tuple(dict.fromkeys(prefixes))


def _event_owner_prefix(raw: str | None) -> str:
    return (raw or "").strip().replace("-", "_")


def _action_reference_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    return "".join(ch for ch in token.casefold() if ch.isalnum())


def _register_action_reference(
    *,
    reference: str,
    owner: ExperienceActionOwnership,
    catalog: dict[str, ExperienceActionOwnership],
) -> None:
    ref_key = _action_reference_key(reference)
    if not ref_key:
        return
    prior = catalog.get(ref_key)
    if prior is None or prior == owner:
        catalog[ref_key] = owner
        return
    raise ValueError(
        "Ambiguous action reference key "
        f"{ref_key!r} between actions {prior.symbol!r} ({prior.action_name!r}) "
        f"and {owner.symbol!r} ({owner.action_name!r}); use disambiguated action refs"
    )


def _qualified_action_references(owner: ExperienceActionOwnership) -> tuple[str, ...]:
    prefixes = _action_owner_prefixes(owner)
    references: list[str] = []
    for prefix in prefixes:
        references.append(f"{prefix}.{owner.symbol}")
        references.append(f"{prefix}.{owner.action_name}")
    return tuple(dict.fromkeys(references))


def _action_owner_prefixes(owner: ExperienceActionOwnership) -> tuple[str, ...]:
    prefixes: list[str] = []
    for raw in (owner.fqn_prefix, owner.package_name):
        token = _action_owner_prefix(raw)
        if token:
            prefixes.append(token)
    return tuple(dict.fromkeys(prefixes))


def _action_owner_prefix(raw: str | None) -> str:
    return (raw or "").strip().replace("-", "_")


__all__ = [
    "ExperienceCompilePlan",
    "ExperienceCompilePlanArtifact",
    "ExperienceActionOwnership",
    "ExperienceActionProgramBindingOwnership",
    "ExperienceActorOwnership",
    "ExperienceActorRoleContract",
    "ExperienceEnvironmentEventActionOwnership",
    "ExperienceEnvironmentEventOwnership",
    "ExperienceEnvironmentProfileActorSpec",
    "ExperienceEnvironmentProfileRoleSpec",
    "ExperienceEnvironmentOwnership",
    "ExperienceEnvironmentProgramOwnership",
    "ExperienceEnvironmentActorBinding",
    "ExperienceEventBindingOwnership",
    "ExperienceEventOwnership",
    "ExperienceProgramOwnership",
    "ExperienceProjectionBranchOwnership",
    "ExperienceProjectionAPIOwnership",
    "ExperienceProjectionAPIContractOwnership",
    "ExperienceProjectionAPIContractParamOwnership",
    "ExperienceProjectionExperienceOwnership",
    "ExperienceProjectionObservableOwnership",
    "ExperienceProjectionViewOwnership",
    "ExperienceRoleOwnership",
    "build_experience_compile_plan",
    "build_experience_compile_plan_with_environment_validation",
    "emit_experience_compile_plan_artifact",
    "publish_environment_profile_actor_role_ownership",
]
