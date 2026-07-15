from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast
from uuid import UUID, NAMESPACE_URL, uuid5

from pydantic import ValidationError

from aware_experience.environment_profile.runtime_support import ocg_support
from aware_experience.materialization.compile_plan_payloads import (
    _ActorMaterializationStepPayload,
    _CompileActorOwnershipRow,
    _CompileEnvironmentActorBindingRow,
    _CompileRoleOwnershipRow,
    _expect_list,
    _expect_mapping,
    _format_compile_payload_validation_error,
    _format_step_payload_validation_error,
    load_experience_compile_plan_payloads,
)
from aware_experience.program.registry_index import find_repo_root
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_identity_ontology.actor.actor_config import ActorConfig
from aware_identity_ontology.actor.actor_enums import ActorType
from aware_identity_ontology.role.role_config import RoleConfig
from aware_identity_ontology.role.role_enums import AccessLevelType
from aware_identity_ontology.stable_ids import stable_role_config_id
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex


class RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...


class MaterializationRuntimeLane(Protocol):
    last_commit_id: UUID | None
    last_head_commit_id: UUID | None

    def activate(
        self,
        *,
        commit: bool,
        publish: bool,
    ) -> AbstractContextManager[None]: ...


class BindMetaGraphRuntimeLane(Protocol):
    def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        branch_id: UUID,
        projection: str,
        actor_id: UUID | None,
    ) -> MaterializationRuntimeLane: ...


class ResolveProjectionHashForClassSuffix(Protocol):
    def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        class_name_suffix: str,
        preferred_projection_name: str | None = None,
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class ActorMaterializationDependencies:
    bind_meta_graph_runtime_lane: BindMetaGraphRuntimeLane
    resolve_projection_hash_for_class_suffix: ResolveProjectionHashForClassSuffix


@dataclass(frozen=True, slots=True)
class ActorMaterializationSpec:
    actor_name: str
    actor_kind: str
    role_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProfileRoleMaterializationSpec:
    name: str
    description: str | None = None
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProfileActorMaterializationSpec:
    key: str
    title: str | None = None
    description: str | None = None
    actor_type: str | None = None
    role_names: tuple[str, ...] = ()


def resolve_actor_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ActorMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    role_catalog: set[str] = set()
    actor_rows_by_key: dict[str, _CompileActorOwnershipRow] = {}
    actor_role_keys_by_actor: dict[str, set[str]] = {}

    for payload in compile_plan_payloads:
        role_rows_raw = _expect_list(
            payload.get("role_ownership", []),
            field_name="role_ownership",
        )
        for role_row_obj in role_rows_raw:
            role_row_map = _expect_mapping(role_row_obj, field_name="role_ownership[]")
            try:
                role_row = _CompileRoleOwnershipRow.model_validate(role_row_map)
            except ValidationError as exc:
                raise RuntimeError(
                    _format_compile_payload_validation_error(
                        exc=exc, path="role_ownership[]"
                    )
                ) from exc
            role_catalog.add(role_row.name.casefold())

        actor_rows_raw = _expect_list(
            payload.get("actor_ownership", []),
            field_name="actor_ownership",
        )
        for actor_row_obj in actor_rows_raw:
            actor_row_map = _expect_mapping(
                actor_row_obj, field_name="actor_ownership[]"
            )
            try:
                actor_row = _CompileActorOwnershipRow.model_validate(actor_row_map)
            except ValidationError as exc:
                raise RuntimeError(
                    _format_compile_payload_validation_error(
                        exc=exc, path="actor_ownership[]"
                    )
                ) from exc
            actor_key = actor_row.name.casefold()
            existing_actor_row = actor_rows_by_key.get(actor_key)
            if existing_actor_row is not None and existing_actor_row != actor_row:
                raise RuntimeError(
                    "Invalid experience compile plan: duplicate actor ownership entries disagree "
                    + f"(actor={actor_row.name!r})"
                )
            actor_rows_by_key[actor_key] = actor_row
            role_bucket = actor_role_keys_by_actor.setdefault(actor_key, set())
            for role_name in actor_row.roles:
                role_bucket.add(role_name.casefold())

        environment_rows_raw = _expect_list(
            payload.get("environment_actor_bindings", []),
            field_name="environment_actor_bindings",
        )
        for binding_obj in environment_rows_raw:
            binding_map = _expect_mapping(
                binding_obj, field_name="environment_actor_bindings[]"
            )
            try:
                binding_row = _CompileEnvironmentActorBindingRow.model_validate(
                    binding_map
                )
            except ValidationError as exc:
                raise RuntimeError(
                    _format_compile_payload_validation_error(
                        exc=exc,
                        path="environment_actor_bindings[]",
                    )
                ) from exc
            actor_key = binding_row.actor.casefold()
            if actor_key not in actor_rows_by_key:
                raise RuntimeError(
                    "Invalid experience compile plan: environment actor binding references unknown actor "
                    + f"{binding_row.actor!r}"
                )
            role_bucket = actor_role_keys_by_actor.setdefault(actor_key, set())
            for role_name in binding_row.roles:
                role_bucket.add(role_name.casefold())

    if not actor_rows_by_key:
        return ()

    specs: list[ActorMaterializationSpec] = []
    for actor_key, actor_row in sorted(
        actor_rows_by_key.items(), key=lambda item: item[0]
    ):
        normalized_roles = actor_role_keys_by_actor.get(actor_key, set())
        unknown_roles = sorted(
            role for role in normalized_roles if role not in role_catalog
        )
        if unknown_roles:
            raise RuntimeError(
                "Invalid experience compile plan: actor role bindings reference unknown role declarations "
                + f"(actor={actor_row.name!r}, roles={unknown_roles!r})"
            )
        specs.append(
            ActorMaterializationSpec(
                actor_name=actor_row.name,
                actor_kind=actor_row.kind,
                role_keys=tuple(sorted(normalized_roles)),
            )
        )
    return tuple(specs)


def build_actor_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ActorMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"actor:{spec.actor_name}",
            step_kind="experience.actor",
            payload=encode_actor_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.actor",
        lane=lane,
        steps=steps,
    )


def encode_actor_materialization_step_payload(
    *,
    spec: ActorMaterializationSpec,
) -> dict[str, object]:
    payload = _ActorMaterializationStepPayload(
        actor_name=spec.actor_name,
        actor_kind=spec.actor_kind,
        role_keys=spec.role_keys,
    )
    return cast(dict[str, object], payload.model_dump(mode="json"))


def decode_actor_materialization_step_payload(
    payload: Mapping[str, object],
) -> ActorMaterializationSpec:
    try:
        step_payload = _ActorMaterializationStepPayload.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(
            _format_step_payload_validation_error(exc=exc, prefix="actor")
        ) from exc

    role_keys_seen: set[str] = set()
    normalized_role_keys: list[str] = []
    for role_key in step_payload.role_keys:
        role_key_casefolded = role_key.casefold()
        if role_key_casefolded in role_keys_seen:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate actor role binding "
                + f"(actor={step_payload.actor_name!r}, role={role_key!r})"
            )
        role_keys_seen.add(role_key_casefolded)
        normalized_role_keys.append(role_key_casefolded)

    return ActorMaterializationSpec(
        actor_name=step_payload.actor_name,
        actor_kind=step_payload.actor_kind,
        role_keys=tuple(normalized_role_keys),
    )


async def materialize_experience_actor_ontology(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_experience_profile_config_id: UUID,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    dependencies: ActorMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    specs = resolve_actor_materialization_specs(
        compile_plan_payloads=compile_plan_payloads
    )
    if not specs:
        return None

    actor_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ActorConfig",
    )
    environment_experience_profile_config_projection_hash = (
        dependencies.resolve_projection_hash_for_class_suffix(
            index=index,
            class_name_suffix=(
                "aware_experience_ontology.environment."
                "environment_experience_profile_config."
                "EnvironmentExperienceProfileConfig"
            ),
            preferred_projection_name="EnvironmentExperienceProfileConfig",
        )
    )
    actor_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=actor_projection_hash,
    )
    plan = build_actor_materialization_plan(lane=actor_lane, specs=specs)

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = decode_actor_materialization_step_payload(step.payload)
        actor_type = _resolve_actor_type(kind=spec.actor_kind)
        actor_branch_id = _derive_actor_materialization_branch_id(
            base_branch_id=plan.lane.branch_id,
            actor_name=spec.actor_name,
        )

        runtime_lane = dependencies.bind_meta_graph_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=actor_branch_id,
            projection=plan.lane.projection_hash,
            actor_id=actor_id,
        )

        with runtime_lane.activate(
            commit=True,
            publish=False,
        ):
            actor_config = await ActorConfig.create(
                key=spec.actor_name,
                type=actor_type,
            )
            for role_key in spec.role_keys:
                role_config_id = _resolve_role_config_id(role_name=role_key)
                _ = await actor_config.add_role_config(role_config_id=role_config_id)

        profile_lane = dependencies.bind_meta_graph_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=plan.lane.branch_id,
            projection=environment_experience_profile_config_projection_hash,
            actor_id=actor_id,
        )
        with profile_lane.activate(commit=True, publish=False):
            profile_config = EnvironmentExperienceProfileConfig.model_construct(
                id=environment_experience_profile_config_id
            )
            _ = await profile_config.add_actor_config(actor_config_id=actor_config.id)

        return MaterializationStepResult(
            details={
                "actor_name": spec.actor_name,
                "actor_kind": spec.actor_kind,
                "role_count": len(spec.role_keys),
                "branch_id": str(actor_branch_id),
                "environment_experience_profile_config_id": str(
                    environment_experience_profile_config_id
                ),
                "profile_binding_commit_id": (
                    str(profile_lane.last_commit_id)
                    if profile_lane.last_commit_id is not None
                    else None
                ),
            },
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
        )

    executor = MaterializationExecutor()
    return await executor.run(plan=plan, runner=_runner)


def resolve_profile_role_capability_target(
    *,
    index: MetaGraphRuntimeIndex,
    capability_ref: str,
) -> tuple[UUID, UUID | None]:
    normalized_capability_ref = (capability_ref or "").strip()
    if not normalized_capability_ref:
        raise RuntimeError(
            "EnvironmentExperience role capability refs require a non-empty value"
        )

    try:
        class_config_id = ocg_support.resolve_class_config_id(
            index=index,
            class_name_suffix=normalized_capability_ref,
        )
    except ValueError:
        class_ref, separator, function_name = normalized_capability_ref.rpartition(".")
        if not separator:
            raise RuntimeError(
                "EnvironmentExperience role capability ref could not resolve class or function "
                + f"(capability_ref={normalized_capability_ref!r})"
            ) from None
        try:
            class_config_id = ocg_support.resolve_class_config_id(
                index=index,
                class_name_suffix=class_ref,
            )
            function_config_id = ocg_support.resolve_public_function_id(
                index=index,
                class_name_suffix=class_ref,
                function_name=function_name,
            )
        except ValueError as exc:
            raise RuntimeError(
                "EnvironmentExperience role capability ref could not resolve class/function "
                + f"(capability_ref={normalized_capability_ref!r})"
            ) from exc
        return class_config_id, function_config_id

    return class_config_id, None


async def materialize_environment_experience_profile_actor_role_ontology(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_experience_profile_config_id: UUID,
    role_specs: Sequence[ProfileRoleMaterializationSpec],
    actor_specs: Sequence[ProfileActorMaterializationSpec],
    dependencies: ActorMaterializationDependencies,
) -> None:
    if not role_specs and not actor_specs:
        return None

    role_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="RoleConfig",
    )
    actor_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ActorConfig",
    )
    environment_experience_profile_config_projection_hash = (
        dependencies.resolve_projection_hash_for_class_suffix(
            index=index,
            class_name_suffix=(
                "aware_experience_ontology.environment."
                "environment_experience_profile_config."
                "EnvironmentExperienceProfileConfig"
            ),
            preferred_projection_name="EnvironmentExperienceProfileConfig",
        )
    )

    role_config_id_by_name: dict[str, UUID] = {}
    role_lane = dependencies.bind_meta_graph_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=lane.branch_id,
        projection=role_projection_hash,
        actor_id=actor_id,
    )
    for role_spec in role_specs:
        with role_lane.activate(commit=True, publish=False):
            role_config = await RoleConfig.create(
                name=role_spec.name,
                description=role_spec.description,
            )
            for capability_ref in role_spec.capabilities:
                class_config_id, function_config_id = (
                    resolve_profile_role_capability_target(
                        index=index,
                        capability_ref=capability_ref,
                    )
                )
                class_policy = await role_config.upsert_class_config_policy(
                    class_config_id=class_config_id,
                    access_level=AccessLevelType.admin,
                )
                if function_config_id is not None:
                    _ = await class_policy.upsert_function_config_policy(
                        function_config_id=function_config_id,
                        access_level=AccessLevelType.admin,
                    )
        if role_config.id is None:
            raise RuntimeError(
                "EnvironmentExperience profile actor-role materialization requires RoleConfig.id"
            )
        role_config_id_by_name[role_spec.name.casefold()] = role_config.id

    profile_lane = dependencies.bind_meta_graph_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=lane.branch_id,
        projection=environment_experience_profile_config_projection_hash,
        actor_id=actor_id,
    )
    for actor_spec in actor_specs:
        actor_branch_id = _derive_actor_materialization_branch_id(
            base_branch_id=lane.branch_id,
            actor_name=actor_spec.key,
        )
        actor_lane = dependencies.bind_meta_graph_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=actor_branch_id,
            projection=actor_projection_hash,
            actor_id=actor_id,
        )

        with actor_lane.activate(commit=True, publish=False):
            actor_config = await ActorConfig.create(
                key=actor_spec.key,
                title=actor_spec.title,
                description=actor_spec.description,
                type=_resolve_actor_type_optional(kind=actor_spec.actor_type),
            )
            for role_name in actor_spec.role_names:
                role_config_id = role_config_id_by_name.get(role_name.casefold())
                if role_config_id is None:
                    raise RuntimeError(
                        "EnvironmentExperience actor-role materialization could not resolve published role "
                        + f"(actor={actor_spec.key!r}, role={role_name!r})"
                    )
                _ = await actor_config.add_role_config(role_config_id=role_config_id)

        if actor_config.id is None:
            raise RuntimeError(
                "EnvironmentExperience profile actor-role materialization requires ActorConfig.id"
            )
        with profile_lane.activate(commit=True, publish=False):
            profile_config = EnvironmentExperienceProfileConfig.model_construct(
                id=environment_experience_profile_config_id
            )
            _ = await profile_config.add_actor_config(actor_config_id=actor_config.id)


async def materialize_experience_compile_plan_actors(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_experience_profile_config_id: UUID,
    planned_processes: Sequence[Mapping[str, object]],
    dependencies: ActorMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    _ = planned_processes
    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_actor_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_experience_profile_config_id=(
            environment_experience_profile_config_id
        ),
        compile_plan_payloads=compile_plan_payloads,
        dependencies=dependencies,
    )


def _derive_actor_materialization_branch_id(
    *, base_branch_id: UUID, actor_name: str
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"aware:experience:actor_materialization:{base_branch_id}:{actor_name.casefold()}",
    )


def _resolve_actor_type(*, kind: str) -> ActorType:
    kind_key = kind.strip().casefold()
    if "." in kind_key:
        kind_key = kind_key.rsplit(".", 1)[-1]
    actor_type_map: dict[str, ActorType] = {
        "agent": ActorType.agent_process_thread,
        "agent_process_thread": ActorType.agent_process_thread,
        "human": ActorType.human,
        "organization": ActorType.organization,
        "system": ActorType.system,
    }
    resolved = actor_type_map.get(kind_key)
    if resolved is None:
        raise RuntimeError(
            "Invalid experience compile plan: actor kind is not supported by ActorType "
            + f"(kind={kind!r})"
        )
    return resolved


def _resolve_actor_type_optional(*, kind: str | None) -> ActorType | None:
    normalized_kind = (kind or "").strip()
    if not normalized_kind:
        return None
    return _resolve_actor_type(kind=normalized_kind)


def _resolve_role_config_id(*, role_name: str) -> UUID:
    return stable_role_config_id(name=role_name)
