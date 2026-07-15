from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aware_code.types.json import JsonArray, JsonObject, JsonValue
from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_id,
)
from aware_experience_ontology.stable_ids import (
    stable_environment_topology_process_seed_id,
    stable_environment_topology_seed_id,
    stable_environment_topology_thread_layout_seed_id,
    stable_environment_topology_thread_seed_id,
    stable_environment_experience_id as stable_hosted_environment_experience_id,
    stable_environment_experience_profile_id as stable_hosted_environment_experience_profile_id,
    stable_program_config_id as stable_experience_program_config_id,
)
from aware_environment_ontology.stable_ids import (
    stable_environment_profile_id,
    stable_process_config_id,
    stable_thread_config_id,
    stable_thread_config_layout_config_id,
    stable_thread_layout_id,
)
from aware_experience.materialization.service import (
    ProfileActorMaterializationSpec,
    ProfileRoleMaterializationSpec,
    materialize_environment_experience_profile_actor_role_ontology,
    materialize_experience_compile_plan_actions,
    materialize_experience_compile_plan_connector_configs,
    materialize_experience_compile_plan_graphs,
    materialize_experience_compile_plan_projections,
    resolve_profile_role_capability_target,
)
from aware_api_runtime.compile_materialization.service import (
    materialize_api_compile_plan_ontology,
)
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
)
from aware_experience_service_dto.experience.program import RunProgramRequest
from aware_meta.materialization import MaterializationLaneContext
from aware_experience.program.service import SubmitProgramTurnOperation
from aware_experience.environment_profile.runtime_support import (
    EnvironmentRuntimeResolverLike,
    invoke_support,
    lane_support,
    ocg_support,
    oig_support,
    stable_ids,
)


class _EnvironmentExperienceDto(BaseModel):
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


def _attribute_payload(value: object) -> object:
    if isinstance(value, BaseModel):
        return _attribute_payload(value.model_dump(mode="python"))
    if isinstance(value, Mapping):
        return SimpleNamespace(
            **{str(key): _attribute_payload(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return [_attribute_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_attribute_payload(item) for item in value)
    return value


def _environment_profile_payload(value: object) -> object:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python")
    if isinstance(value, Mapping):
        value = {
            key: item
            for key, item in value.items()
            if str(key) not in {"events", "experiences", "view_event_transitions"}
        }
    return _attribute_payload(value)


class EnvironmentExperienceRoleSpec(_EnvironmentExperienceDto):
    name: str
    description: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class EnvironmentExperienceActorSpec(_EnvironmentExperienceDto):
    key: str
    title: str | None = None
    description: str | None = None
    type: str | None = None
    role_names: list[str] = Field(default_factory=list)


class EnvironmentExperienceLayoutConfigSpec(_EnvironmentExperienceDto):
    key: str | None = None
    layout_key: str
    position: int | None = None
    narrative: str | None = None
    intent: str | None = None


class EnvironmentExperienceRuntimeMountReceipt(_EnvironmentExperienceDto):
    environment_id: UUID
    environment_experience_profile_id: UUID
    topology_seed_key: str
    process_config_id: UUID | None = None
    process_key: str
    process_id: UUID
    thread_config_id: UUID | None = None
    thread_key: str
    thread_id: UUID
    thread_layout_config_id: UUID | None = None
    layout_key: str | None = None
    layout_config_id: UUID | None = None
    layout_id: UUID | None = None
    thread_layout_id: UUID | None = None
    activate_on_seed: bool | None = None
    status: str


_ENVIRONMENT_EXPERIENCE_PROJECTION_NAME = "EnvironmentExperience"
_ENVIRONMENT_EXPERIENCE_PROFILE_PROJECTION_NAME = "EnvironmentExperienceProfile"
_ENVIRONMENT_TOPOLOGY_SEED_PROJECTION_NAME = "EnvironmentTopologySeed"


@dataclass(frozen=True, slots=True)
class EnvironmentExperienceProjectionBranches:
    environment_experience: str
    environment_experience_profile: str
    environment_topology_seed: str


def resolve_environment_experience_projection_branches(
    *,
    index: Any,
) -> EnvironmentExperienceProjectionBranches:
    return EnvironmentExperienceProjectionBranches(
        environment_experience=ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name=_ENVIRONMENT_EXPERIENCE_PROJECTION_NAME,
        ),
        environment_experience_profile=ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name=_ENVIRONMENT_EXPERIENCE_PROFILE_PROJECTION_NAME,
        ),
        environment_topology_seed=ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name=_ENVIRONMENT_TOPOLOGY_SEED_PROJECTION_NAME,
        ),
    )


class EnvironmentExperienceProgramApplyReceipt(_EnvironmentExperienceDto):
    key: str
    phase: str
    program_ref: str
    position: int | None = None
    status: str
    error: str | None = None
    program_run_id: UUID | None = None
    turn_id: UUID | None = None
    deduped: bool = False
    resolved_branch_id: UUID | None = None
    resolved_projection_hash: str | None = None
    lane_resolution_source: str | None = None


class UpsertEnvironmentExperienceRequest(_EnvironmentExperienceDto):
    operation: str = "upsert_environment_experience"
    actor_id: UUID | None = None
    environment_id: UUID
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    profile: Any
    topology_seeds: list[Any] = Field(default_factory=list)
    validate_only: bool = False

    @field_validator("profile", mode="before")
    @classmethod
    def _coerce_profile_payload(cls, value: object) -> object:
        return _environment_profile_payload(value)

    @field_validator("topology_seeds", mode="before")
    @classmethod
    def _coerce_topology_seed_payloads(cls, value: object) -> object:
        return _attribute_payload(value)


class UpsertEnvironmentExperienceResponse(_EnvironmentExperienceDto):
    operation: str = "upsert_environment_experience"
    actor_id: UUID | None = None
    environment_id: UUID
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    status: str
    error: str | None = None
    environment_experience_profile_id: UUID | None = None
    process_config_ids: list[UUID] = Field(default_factory=list)
    thread_config_ids: list[UUID] = Field(default_factory=list)
    thread_projection_association_ids: list[UUID] = Field(default_factory=list)
    thread_layout_config_ids: list[UUID] = Field(default_factory=list)
    topology_seed_ids: list[UUID] = Field(default_factory=list)
    topology_process_seed_ids: list[UUID] = Field(default_factory=list)
    topology_thread_seed_ids: list[UUID] = Field(default_factory=list)
    topology_thread_layout_seed_ids: list[UUID] = Field(default_factory=list)


class ProvisionEnvironmentExperienceRequest(_EnvironmentExperienceDto):
    operation: str = "provision_environment_experience"
    actor_id: UUID | None = None
    environment_id: UUID
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    environment_experience_profile_id: UUID | None = None
    topology_seed_key: str
    validate_only: bool = False


class ProvisionEnvironmentExperienceResponse(_EnvironmentExperienceDto):
    operation: str = "provision_environment_experience"
    actor_id: UUID | None = None
    environment_id: UUID
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    status: str
    error: str | None = None
    environment_experience_profile_id: UUID | None = None
    process_ids: list[UUID] = Field(default_factory=list)
    thread_ids: list[UUID] = Field(default_factory=list)
    thread_layout_ids: list[UUID] = Field(default_factory=list)
    runtime_mounts: list[EnvironmentExperienceRuntimeMountReceipt] = Field(
        default_factory=list
    )


class ApplyEnvironmentExperienceProgramsRequest(_EnvironmentExperienceDto):
    operation: str = "apply_environment_experience_programs"
    actor_id: UUID | None = None
    environment_id: UUID
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    environment_experience_profile_id: UUID | None = None
    phase: str
    target_actor_id: UUID | None = None
    validate_only: bool = False


class ApplyEnvironmentExperienceProgramsResponse(_EnvironmentExperienceDto):
    operation: str = "apply_environment_experience_programs"
    actor_id: UUID | None = None
    environment_id: UUID
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    status: str
    error: str | None = None
    environment_experience_profile_id: UUID | None = None
    phase: str
    target_actor_id: UUID | None = None
    receipts: list[EnvironmentExperienceProgramApplyReceipt] = Field(
        default_factory=list
    )


def _normalize_required_key(*, value: str | None, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _dedupe_ids(ids: list[UUID]) -> list[UUID]:
    seen: set[UUID] = set()
    ordered: list[UUID] = []
    for value in ids:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _build_environment_experience_runtime_mount_receipts(
    *,
    environment_id: UUID,
    profile_id: UUID,
    topology_seed_key: str,
    planned_processes: list[dict[str, Any]],
) -> list[EnvironmentExperienceRuntimeMountReceipt]:
    receipts: list[EnvironmentExperienceRuntimeMountReceipt] = []
    for process_plan in planned_processes:
        for thread_plan in process_plan["threads"]:
            planned_layouts = tuple(thread_plan["layouts"])
            if not planned_layouts:
                receipts.append(
                    EnvironmentExperienceRuntimeMountReceipt(
                        environment_id=environment_id,
                        environment_experience_profile_id=profile_id,
                        topology_seed_key=topology_seed_key,
                        process_config_id=process_plan.get("process_config_id"),
                        process_key=str(process_plan["process_key"]),
                        process_id=process_plan["process_id"],
                        thread_config_id=thread_plan.get("thread_config_id"),
                        thread_key=str(thread_plan["thread_key"]),
                        thread_id=thread_plan["thread_id"],
                        status="succeeded",
                    )
                )
                continue
            for layout_plan in planned_layouts:
                receipts.append(
                    EnvironmentExperienceRuntimeMountReceipt(
                        environment_id=environment_id,
                        environment_experience_profile_id=profile_id,
                        topology_seed_key=topology_seed_key,
                        process_config_id=process_plan.get("process_config_id"),
                        process_key=str(process_plan["process_key"]),
                        process_id=process_plan["process_id"],
                        thread_config_id=thread_plan.get("thread_config_id"),
                        thread_key=str(thread_plan["thread_key"]),
                        thread_id=thread_plan["thread_id"],
                        thread_layout_config_id=layout_plan.get(
                            "thread_layout_config_id"
                        ),
                        layout_key=str(layout_plan["layout_key"]),
                        layout_config_id=layout_plan["layout_config_id"],
                        layout_id=layout_plan["layout_id"],
                        thread_layout_id=layout_plan["thread_layout_id"],
                        activate_on_seed=bool(layout_plan["activate_on_seed"]),
                        status="succeeded",
                    )
                )
    return receipts


def _coerce_optional_int(*, value: object, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            raise RuntimeError(f"{field_name} must be an Int") from exc
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{field_name} must be an Int") from exc


def _coerce_bool(*, value: object, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"", "false", "0", "no", "off"}:
            return False
        if normalized in {"true", "1", "yes", "on"}:
            return True
    raise RuntimeError(f"{field_name} must be a Bool")


def _normalize_program_ref(*, value: str, field_name: str) -> tuple[str, str]:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    if ":" not in normalized:
        raise ValueError(
            f"{field_name} must use '<experience_fqn_prefix>:<program_name>' format"
        )
    namespace, program_key = normalized.split(":", 1)
    normalized_namespace = namespace.strip()
    normalized_program_key = program_key.strip()
    if not normalized_namespace or not normalized_program_key:
        raise ValueError(
            f"{field_name} must use '<experience_fqn_prefix>:<program_name>' format"
        )
    return f"{normalized_namespace}:{normalized_program_key}", normalized_program_key


def _hosted_environment_experience_fqn_prefix(*, environment_id: UUID) -> str:
    return f"aware://runtime/environment-experience/{environment_id}"


def _resolve_hosted_environment_experience_ids(
    *,
    environment_id: UUID,
    profile_key: str,
) -> tuple[str, UUID, UUID]:
    fqn_prefix = _hosted_environment_experience_fqn_prefix(
        environment_id=environment_id
    )
    environment_experience_id = stable_hosted_environment_experience_id(
        fqn_prefix=fqn_prefix,
    )
    environment_profile_id = stable_environment_profile_id(
        environment_id=environment_id,
        key=profile_key,
    )
    environment_experience_profile_id = stable_hosted_environment_experience_profile_id(
        environment_experience_id=environment_experience_id,
        environment_profile_id=environment_profile_id,
        key=profile_key,
    )
    return fqn_prefix, environment_experience_id, environment_experience_profile_id


def _is_retired_environment_create_profile_error(*, error: str | None) -> bool:
    if error is None:
        return False
    normalized_error = error.strip().lower()
    return (
        "environment.create_experience_profile" in normalized_error
        and "runtime is retired" in normalized_error
    )


def _try_resolve_public_function_id(
    *,
    index,
    class_name_suffix: str,
    function_name: str,
) -> UUID | None:
    try:
        return ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix=class_name_suffix,
            function_name=function_name,
        )
    except ValueError:
        return None


def _normalize_json_object_mapping(
    *, value: object, field_name: str
) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{field_name} must be a JsonObject mapping")
    return {str(key): raw_value for key, raw_value in value.items()}


def _normalize_optional_text(*, value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _class_instance_source_id(class_instance: Any) -> UUID | None:
    raw = getattr(class_instance, "source_object_id", None)
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except (TypeError, ValueError):
        return None


def _normalize_layout_assoc_key(
    *,
    layout_spec: EnvironmentExperienceLayoutConfigSpec,
    layout_key: str,
) -> str:
    return (layout_spec.key or "").strip() or layout_key


def _stable_layout_id_from_layout_key(*, layout_key: str) -> UUID:
    return stable_layout_id(key=layout_key)


def _normalize_actor_type_token(*, value: str | None, field_name: str) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    normalized_key = normalized.casefold()
    if "." in normalized_key:
        normalized_key = normalized_key.rsplit(".", 1)[-1]
    if normalized_key not in {
        "agent",
        "agent_process_thread",
        "human",
        "organization",
        "system",
    }:
        raise ValueError(f"{field_name} must resolve to a supported ActorType")
    return normalized


def _normalize_profile_actor_role_materialization_specs(
    *,
    index,
    roles: list[EnvironmentExperienceRoleSpec] | None,
    actors: list[EnvironmentExperienceActorSpec] | None,
) -> tuple[
    tuple[ProfileRoleMaterializationSpec, ...],
    tuple[ProfileActorMaterializationSpec, ...],
]:
    role_specs_by_name: dict[str, ProfileRoleMaterializationSpec] = {}
    for role_index, role_spec in enumerate(list(roles or [])):
        role_name = _normalize_required_key(
            value=role_spec.name,
            field_name=f"profile.roles[{role_index}].name",
        ).casefold()
        if role_name in role_specs_by_name:
            raise ValueError(
                "upsert_environment_experience requires unique profile.roles[].name: "
                f"{role_name!r}"
            )

        capabilities: list[str] = []
        seen_capability_refs: set[str] = set()
        for capability_index, capability_value in enumerate(
            list(role_spec.capabilities or [])
        ):
            capability_ref = _normalize_required_key(
                value=capability_value,
                field_name=f"profile.roles[{role_index}].capabilities[{capability_index}]",
            )
            capability_ref_key = capability_ref.casefold()
            if capability_ref_key in seen_capability_refs:
                raise ValueError(
                    "upsert_environment_experience requires unique capability refs per role: "
                    f"role={role_name!r} capability_ref={capability_ref!r}"
                )
            _ = resolve_profile_role_capability_target(
                index=index,
                capability_ref=capability_ref,
            )
            seen_capability_refs.add(capability_ref_key)
            capabilities.append(capability_ref)

        role_specs_by_name[role_name] = ProfileRoleMaterializationSpec(
            name=role_name,
            description=_normalize_optional_text(
                value=getattr(role_spec, "description", None)
            ),
            capabilities=tuple(capabilities),
        )

    actor_specs: list[ProfileActorMaterializationSpec] = []
    seen_actor_keys: set[str] = set()
    for actor_index, actor_spec in enumerate(list(actors or [])):
        actor_key = _normalize_required_key(
            value=actor_spec.key,
            field_name=f"profile.actors[{actor_index}].key",
        ).casefold()
        if actor_key in seen_actor_keys:
            raise ValueError(
                "upsert_environment_experience requires unique profile.actors[].key: "
                f"{actor_key!r}"
            )
        seen_actor_keys.add(actor_key)

        role_names: list[str] = []
        seen_actor_role_names: set[str] = set()
        for role_index, role_name_value in enumerate(list(actor_spec.role_names or [])):
            role_name = _normalize_required_key(
                value=role_name_value,
                field_name=f"profile.actors[{actor_index}].role_names[{role_index}]",
            ).casefold()
            if role_name in seen_actor_role_names:
                raise ValueError(
                    "upsert_environment_experience requires unique role names per actor: "
                    f"actor={actor_key!r} role_name={role_name!r}"
                )
            if role_name not in role_specs_by_name:
                raise ValueError(
                    "profile.actors[].role_names[] must reference declared profile.roles[].name: "
                    f"actor={actor_key!r} role_name={role_name!r}"
                )
            seen_actor_role_names.add(role_name)
            role_names.append(role_name)

        actor_specs.append(
            ProfileActorMaterializationSpec(
                key=actor_key,
                title=_normalize_optional_text(
                    value=getattr(actor_spec, "title", None)
                ),
                description=_normalize_optional_text(
                    value=getattr(actor_spec, "description", None)
                ),
                actor_type=_normalize_actor_type_token(
                    value=actor_spec.type,
                    field_name=f"profile.actors[{actor_index}].type",
                ),
                role_names=tuple(role_names),
            )
        )

    return tuple(role_specs_by_name.values()), tuple(actor_specs)


async def _load_environment_experience_profile_graph(
    *,
    index,
    lane_branch_id: UUID,
    requested_profile_id: UUID | None,
) -> tuple[str, Any, UUID, UUID]:
    projection_branches = resolve_environment_experience_projection_branches(
        index=index
    )
    environment_experience_profile_projection_hash = (
        projection_branches.environment_experience_profile
    )

    from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
    from aware_meta.graph.instance.commit.materialization_cache import (
        CachedLaneMaterializer,
    )

    profile_head = await FSCommitStore().head(
        branch_id=lane_branch_id,
        projection_hash=environment_experience_profile_projection_hash,
    )
    if profile_head is None or not profile_head.get("commit_id"):
        raise RuntimeError(
            "EnvironmentExperienceProfile lane is not initialized for environment experience operations. "
            "Run upsert_environment_experience first."
        )

    profile_opg = index.opg_by_hash.get(environment_experience_profile_projection_hash)
    if profile_opg is None:
        raise RuntimeError(
            "EnvironmentExperienceProfile OPG not found in runtime index: "
            f"projection_hash={environment_experience_profile_projection_hash}"
        )

    profile_commit_id = UUID(str(profile_head["commit_id"]))
    profile_oig_id_raw = profile_head.get("object_instance_graph_id")
    profile_oig_id = UUID(str(profile_oig_id_raw)) if profile_oig_id_raw else None
    profile_oig, _idx = await CachedLaneMaterializer().get(
        branch_id=lane_branch_id,
        ocg=index.ocg,
        opg=profile_opg,
        commit_id=profile_commit_id,
        oig_id=profile_oig_id,
    )

    profile_root_id = profile_oig.root_class_instance_id
    if profile_root_id is None:
        raise RuntimeError(
            "EnvironmentExperienceProfile lane root_class_instance_id is required "
            "for environment experience operations"
        )

    profile_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_experience_profile.EnvironmentExperienceProfile"
        ),
    )
    profile_ids_in_graph = {
        ci.id
        for ci in profile_oig.class_instances
        if ci.class_config_id == profile_class_id
    }
    ci_by_id: dict[UUID, Any] = {ci.id: ci for ci in profile_oig.class_instances}
    profile_id_by_source_id = {
        source_id: ci.id
        for ci in profile_oig.class_instances
        if ci.class_config_id == profile_class_id
        for source_id in [_class_instance_source_id(ci)]
        if source_id is not None
    }
    profile_ids_from_root = [profile_root_id]
    if profile_root_id not in profile_ids_in_graph:
        raise RuntimeError(
            "EnvironmentExperienceProfile lane root is not an EnvironmentExperienceProfile instance: "
            f"root_id={profile_root_id}"
        )

    if requested_profile_id is not None:
        if requested_profile_id in profile_ids_from_root:
            resolved_profile_id = requested_profile_id
        else:
            resolved_profile_id = profile_id_by_source_id.get(requested_profile_id)
        if (
            resolved_profile_id is None
            or resolved_profile_id not in profile_ids_from_root
        ):
            raise RuntimeError(
                "Requested environment_experience_profile_id is not present in the "
                "environment_experience_profile lane: "
                f"requested={requested_profile_id}"
            )
        profile_id = resolved_profile_id
    else:
        if len(profile_ids_from_root) != 1:
            raise RuntimeError(
                "EnvironmentExperience operation requires exactly one profile "
                "when environment_experience_profile_id is omitted: "
                f"count={len(profile_ids_from_root)}"
            )
        profile_id = profile_ids_from_root[0]

    profile_ci = ci_by_id.get(profile_id)
    profile_source_id = (
        _class_instance_source_id(profile_ci) if profile_ci is not None else None
    )

    return (
        environment_experience_profile_projection_hash,
        profile_oig,
        profile_id,
        (profile_source_id or profile_id),
    )


async def _load_committed_environment_experience_projection_oig(
    *,
    index: Any,
    lane_branch_id: UUID,
    projection_hash: str,
    projection_name: str,
) -> Any:
    from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
    from aware_meta.graph.instance.commit.materialization_cache import (
        CachedLaneMaterializer,
    )

    head = await FSCommitStore().head(
        branch_id=lane_branch_id,
        projection_hash=projection_hash,
    )
    if head is None or not head.get("commit_id"):
        raise RuntimeError(
            f"{projection_name} lane is not initialized for environment experience operations. "
            "Run upsert_environment_experience first."
        )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{projection_name} OPG not found in runtime index: "
            f"projection_hash={projection_hash}"
        )

    commit_id = UUID(str(head["commit_id"]))
    oig_id_raw = head.get("object_instance_graph_id")
    oig_id = UUID(str(oig_id_raw)) if oig_id_raw else None
    oig, _idx = await CachedLaneMaterializer().get(
        branch_id=lane_branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        oig_id=oig_id,
    )
    return oig


async def _ensure_attention_layout_instance(
    *,
    runtime: Any,
    index,
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    branch_id: UUID,
    layout_key: str,
    title: str | None,
    description: str | None,
) -> UUID:
    layout_id = _stable_layout_id_from_layout_key(layout_key=layout_key)
    layout_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="Layout",
    )
    layout_opg = index.opg_by_hash.get(layout_projection_hash)
    if layout_opg is None:
        raise RuntimeError(
            "Attention Layout OPG not found in runtime index: "
            f"projection_hash={layout_projection_hash}"
        )

    layout_build_fn_id = ocg_support.resolve_single_opg_constructor_function_id(
        index=index,
        object_projection_graph_id=layout_opg.id,
    )
    layout_title = _normalize_optional_text(value=title) or layout_key
    request = InvokeFunctionRequest(
        operation="invoke_function",
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        projection_hash=layout_projection_hash,
        call_target=InvokeFunctionCallTarget.opg_constructor,
        object_id=None,
        object_projection_graph_id=layout_opg.id,
        function_id=layout_build_fn_id,
        args=JsonArray(),
        kwargs=JsonObject(
            {
                "key": layout_key,
                "title": layout_title,
                "description": description,
            }
        ),
        expected_graph_hash_pre=None,
        expected_head_commit_id=None,
        commit=True,
        publish=False,
    )
    response = await runtime.invoker.invoke_function_with_index(
        index=index, request=request
    )
    invoke_support.assert_invoke_succeeded(
        response=response,
        label=f"Layout.build({layout_key})",
    )
    return layout_id


def _build_program_apply_plans(
    *,
    index,
    env_exp_oig,
    profile_id: UUID,
    environment_id: UUID,
    phase: str,
) -> list[dict[str, object]]:
    program_apply_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_experience_program_apply.EnvironmentExperienceProgramApply"
        ),
    )
    program_config_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix="aware_experience_ontology.program.program_config.ProgramConfig",
    )
    program_apply_attr_name_by_id = ocg_support.build_attr_name_by_id_for_class_config(
        index=index,
        class_config_id=program_apply_class_id,
    )
    program_config_attr_name_by_id = ocg_support.build_attr_name_by_id_for_class_config(
        index=index,
        class_config_id=program_config_class_id,
    )

    ci_by_id: dict[UUID, Any] = {ci.id: ci for ci in env_exp_oig.class_instances}
    program_apply_ids_in_graph = {
        ci.id
        for ci in env_exp_oig.class_instances
        if ci.class_config_id == program_apply_class_id
    }
    program_config_ids_in_graph = {
        ci.id
        for ci in env_exp_oig.class_instances
        if ci.class_config_id == program_config_class_id
    }
    requested_phase = _normalize_required_key(value=phase, field_name="phase")
    requested_phase_norm = requested_phase.casefold()
    environment_experience_fqn_prefix = _hosted_environment_experience_fqn_prefix(
        environment_id=environment_id
    )

    planned_apply_ids = _dedupe_ids(
        [
            rel.target_class_instance_id
            for rel in env_exp_oig.class_instance_relationships
            if rel.source_class_instance_id == profile_id
            and rel.target_class_instance_id in program_apply_ids_in_graph
        ]
    )
    planned_applies: list[dict[str, object]] = []
    for apply_id in planned_apply_ids:
        apply_ci = ci_by_id.get(apply_id)
        if apply_ci is None:
            continue

        apply_key = _normalize_required_key(
            value=oig_support.extract_attr_scalar(
                class_instance=apply_ci,
                attr_name_by_id=program_apply_attr_name_by_id,
                name="key",
            ),
            field_name=f"EnvironmentExperienceProgramApply.key({apply_id})",
        )
        apply_phase = _normalize_required_key(
            value=oig_support.extract_attr_scalar(
                class_instance=apply_ci,
                attr_name_by_id=program_apply_attr_name_by_id,
                name="phase",
            ),
            field_name=f"EnvironmentExperienceProgramApply.phase({apply_key})",
        )
        if apply_phase.casefold() != requested_phase_norm:
            continue

        program_config_ids = _dedupe_ids(
            [
                rel.target_class_instance_id
                for rel in env_exp_oig.class_instance_relationships
                if rel.source_class_instance_id == apply_id
                and rel.target_class_instance_id in program_config_ids_in_graph
            ]
        )
        if not program_config_ids:
            raise RuntimeError(
                "EnvironmentExperienceProgramApply requires one linked ProgramConfig: "
                f"apply_key={apply_key!r}"
            )
        if len(program_config_ids) != 1:
            raise RuntimeError(
                "EnvironmentExperienceProgramApply must resolve exactly one ProgramConfig: "
                f"apply_key={apply_key!r} count={len(program_config_ids)}"
            )
        program_config_id = program_config_ids[0]
        program_config_ci = ci_by_id.get(program_config_id)
        if program_config_ci is None:
            raise RuntimeError(
                "ProgramConfig instance missing from EnvironmentExperience projection: "
                f"program_config_id={program_config_id}"
            )
        program_key = _normalize_required_key(
            value=oig_support.extract_attr_scalar(
                class_instance=program_config_ci,
                attr_name_by_id=program_config_attr_name_by_id,
                name="key",
            ),
            field_name=f"ProgramConfig.key({program_config_id})",
        )
        position = _coerce_optional_int(
            value=oig_support.extract_attr_scalar(
                class_instance=apply_ci,
                attr_name_by_id=program_apply_attr_name_by_id,
                name="position",
            ),
            field_name=f"EnvironmentExperienceProgramApply.position({apply_key})",
        )
        planned_applies.append(
            {
                "key": apply_key,
                "phase": apply_phase,
                "position": position,
                "program_config_id": program_config_id,
                "program_ref": f"{environment_experience_fqn_prefix}:{program_key}",
                "message": oig_support.extract_attr_scalar(
                    class_instance=apply_ci,
                    attr_name_by_id=program_apply_attr_name_by_id,
                    name="message",
                ),
                "symbols": _normalize_json_object_mapping(
                    value=oig_support.extract_attr_scalar(
                        class_instance=apply_ci,
                        attr_name_by_id=program_apply_attr_name_by_id,
                        name="symbols",
                    ),
                    field_name=f"EnvironmentExperienceProgramApply.symbols({apply_key})",
                ),
            }
        )

    planned_applies.sort(
        key=lambda plan: (
            plan["position"] is None,
            _coerce_optional_int(
                value=plan["position"],
                field_name=f"EnvironmentExperienceProgramApply.position({plan['key']})",
            )
            or 0,
            str(plan["key"]).casefold(),
        )
    )
    return planned_applies


async def upsert_environment_experience(
    resolver: EnvironmentRuntimeResolverLike,
    request: UpsertEnvironmentExperienceRequest,
) -> UpsertEnvironmentExperienceResponse:
    runtime = await resolver.get_runtime(environment_id=request.environment_id)
    index = runtime.invoker.get_index()

    environment_id = request.environment_id
    profile_spec = request.profile

    boot_process_id = stable_ids.stable_boot_process_id(environment_id=environment_id)
    boot_thread_id = stable_ids.stable_boot_thread_id(environment_id=environment_id)
    boot_branch_id = stable_ids.stable_branch_id(
        environment_id=environment_id, thread_id=boot_thread_id
    )

    lane_branch_id = request.branch_id or boot_branch_id
    context_process_id = request.process_id or boot_process_id
    context_thread_id = request.thread_id or boot_thread_id

    environment_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index, projection_name="Environment"
    )
    projection_branches = resolve_environment_experience_projection_branches(
        index=index
    )
    environment_experience_projection_hash = projection_branches.environment_experience
    environment_experience_profile_projection_hash = (
        projection_branches.environment_experience_profile
    )
    environment_topology_seed_projection_hash = (
        projection_branches.environment_topology_seed
    )
    opgi_by_key = ocg_support.build_opgi_index(index=index)

    profile_key = _normalize_required_key(
        value=profile_spec.key,
        field_name="profile.key",
    )
    installed_program_plans_by_ref: dict[str, dict[str, Any]] = {}
    for program_index, program_spec in enumerate(list(profile_spec.programs or [])):
        program_ref, program_key = _normalize_program_ref(
            value=program_spec.program_ref,
            field_name=f"profile.programs[{program_index}].program_ref",
        )
        if program_ref in installed_program_plans_by_ref:
            raise ValueError(
                "upsert_environment_experience requires unique profile.programs[].program_ref: "
                f"{program_ref!r}"
            )
        installed_program_plans_by_ref[program_ref] = {
            "spec": program_spec,
            "program_ref": program_ref,
            "program_key": program_key,
            "program_config_id": stable_experience_program_config_id(key=program_key),
        }
    planned_programs = list(installed_program_plans_by_ref.values())

    planned_program_applies: list[dict[str, Any]] = []
    seen_program_apply_keys: set[str] = set()
    for apply_index, program_apply_spec in enumerate(
        list(profile_spec.program_applies or [])
    ):
        apply_key = _normalize_required_key(
            value=program_apply_spec.key,
            field_name=f"profile.program_applies[{apply_index}].key",
        )
        if apply_key in seen_program_apply_keys:
            raise ValueError(
                "upsert_environment_experience requires unique profile.program_applies[].key: "
                f"{apply_key!r}"
            )
        seen_program_apply_keys.add(apply_key)
        apply_program_ref, _apply_program_key = _normalize_program_ref(
            value=program_apply_spec.program_ref,
            field_name=f"profile.program_applies[{apply_index}].program_ref",
        )
        installed_program_plan = installed_program_plans_by_ref.get(apply_program_ref)
        if installed_program_plan is None:
            raise ValueError(
                "profile.program_applies[].program_ref must reference an installed profile.programs[] entry: "
                f"{apply_program_ref!r}"
            )
        apply_phase = _normalize_required_key(
            value=program_apply_spec.phase,
            field_name=f"profile.program_applies[{apply_index}].phase",
        )
        planned_program_applies.append(
            {
                "spec": program_apply_spec,
                "key": apply_key,
                "phase": apply_phase,
                "program_ref": apply_program_ref,
                "program_plan": installed_program_plan,
            }
        )
    (
        environment_experience_fqn_prefix,
        environment_experience_id,
        profile_id,
    ) = _resolve_hosted_environment_experience_ids(
        environment_id=environment_id,
        profile_key=profile_key,
    )
    environment_profile_id = stable_environment_profile_id(
        environment_id=environment_id,
        key=profile_key,
    )
    if planned_programs or planned_program_applies:
        raise ValueError(
            "profile.programs and profile.program_applies are retired for "
            "Experience profile materialization. Install programs under "
            "EnvironmentExperienceThreadConfig bridges and execute them through "
            "the Experience runtime run_program boundary."
        )
    planned_role_specs, planned_actor_specs = (
        _normalize_profile_actor_role_materialization_specs(
            index=index,
            roles=list(profile_spec.roles or []),
            actors=list(profile_spec.actors or []),
        )
    )
    process_config_ids: list[UUID] = []
    thread_config_ids: list[UUID] = []
    thread_projection_association_ids: list[UUID] = []
    thread_layout_config_ids: list[UUID] = []
    topology_seed_ids: list[UUID] = []
    topology_process_seed_ids: list[UUID] = []
    topology_thread_seed_ids: list[UUID] = []
    topology_thread_layout_seed_ids: list[UUID] = []

    planned_processes: list[dict[str, Any]] = []
    process_plans_by_key: dict[str, dict[str, Any]] = {}
    process_specs = list(profile_spec.process_configs or [])
    if process_specs:
        raise ValueError(
            "profile.process_configs is retired for Experience profile materialization. "
            "Create Environment-owned ProcessConfig/ThreadConfig topology through "
            "the Environment profile rail, then link Environment process_config_id "
            "with EnvironmentExperienceProfile.add_process_config."
        )

    for process_index, process_spec in enumerate(process_specs):
        process_config_key = _normalize_required_key(
            value=process_spec.key,
            field_name=f"profile.process_configs[{process_index}].key",
        )
        process_config_key_lookup = process_config_key.casefold()
        if process_config_key_lookup in process_plans_by_key:
            raise ValueError(
                "upsert_environment_experience requires unique profile.process_configs[].key: "
                f"{process_config_key!r}"
            )
        process_type = _normalize_required_key(
            value=process_spec.type,
            field_name=f"profile.process_configs[{process_index}].type",
        )
        process_config_id = stable_process_config_id(
            environment_experience_profile_id=profile_id,
            key=process_config_key,
        )
        process_config_ids.append(process_config_id)

        planned_threads: list[dict[str, Any]] = []
        thread_plans_by_key: dict[str, dict[str, Any]] = {}
        thread_specs = list(process_spec.thread_configs or [])

        for thread_index, thread_spec in enumerate(thread_specs):
            thread_config_key = _normalize_required_key(
                value=thread_spec.key,
                field_name=(
                    f"profile.process_configs[{process_index}]."
                    f"thread_configs[{thread_index}].key"
                ),
            )
            thread_config_key_lookup = thread_config_key.casefold()
            if thread_config_key_lookup in thread_plans_by_key:
                raise ValueError(
                    "upsert_environment_experience requires unique thread config keys per process config: "
                    f"process_config_key={process_config_key!r} thread_config_key={thread_config_key!r}"
                )
            thread_config_id = stable_thread_config_id(
                process_config_id=process_config_id,
                key=thread_config_key,
            )
            thread_config_ids.append(thread_config_id)

            planned_projection_specs: list[dict[str, Any]] = []
            projection_specs = list(thread_spec.projection_identities or [])
            default_projection_count = sum(
                1
                for projection_spec in projection_specs
                if bool(projection_spec.is_default)
            )
            if default_projection_count > 1:
                raise ValueError(
                    "upsert_environment_experience allows at most one default projection identity per thread config"
                )

            for projection_spec in projection_specs:
                projection_identity_key = _normalize_required_key(
                    value=projection_spec.projection_identity_key,
                    field_name=(
                        "profile.process_configs[].thread_configs[]."
                        "projection_identities[].projection_identity_key"
                    ),
                )
                opgi_entry = opgi_by_key.get(projection_identity_key)
                if opgi_entry is None:
                    raise ValueError(
                        "Unknown projection_identity_key for hosted environment: "
                        f"{projection_identity_key!r}"
                    )
                opgi_id, opgi_view_keys = opgi_entry
                normalized_view_key = (projection_spec.view_key or "").strip() or None
                if (
                    normalized_view_key is not None
                    and opgi_view_keys
                    and normalized_view_key not in opgi_view_keys
                ):
                    raise ValueError(
                        "projection view_key does not resolve for projection_identity_key: "
                        f"{projection_identity_key!r} view_key={normalized_view_key!r}"
                    )

                assoc_id = stable_ids.stable_thread_config_projection_assoc_id(
                    thread_config_id=thread_config_id,
                    object_projection_graph_identity_id=opgi_id,
                )
                thread_projection_association_ids.append(assoc_id)

                planned_projection_specs.append(
                    {
                        "spec": projection_spec,
                        "opgi_id": opgi_id,
                        "view_key": normalized_view_key,
                    }
                )

            planned_layout_specs: list[dict[str, Any]] = []
            layout_plans_by_key: dict[str, dict[str, Any]] = {}
            layout_specs = list(thread_spec.layout_configs or [])
            seen_layout_keys: set[str] = set()
            for layout_index, layout_spec in enumerate(layout_specs):
                layout_key = _normalize_required_key(
                    value=layout_spec.layout_key,
                    field_name=(
                        "profile.process_configs[].thread_configs[]."
                        f"layout_configs[{layout_index}].layout_key"
                    ),
                )
                layout_key_lookup = layout_key.casefold()
                if layout_key_lookup in seen_layout_keys:
                    raise ValueError(
                        "upsert_environment_experience requires unique layout configs per thread config: "
                        f"thread_config_key={thread_config_key!r} layout_key={layout_key!r}"
                    )
                seen_layout_keys.add(layout_key_lookup)

                layout_config_id = stable_layout_config_id(key=layout_key)
                assoc_id = stable_thread_config_layout_config_id(
                    thread_config_id=thread_config_id,
                    layout_config_id=layout_config_id,
                )
                thread_layout_config_ids.append(assoc_id)
                layout_plan = {
                    "spec": layout_spec,
                    "layout_key": layout_key,
                    "layout_config_id": layout_config_id,
                    "key": _normalize_layout_assoc_key(
                        layout_spec=layout_spec,
                        layout_key=layout_key,
                    ),
                }
                planned_layout_specs.append(layout_plan)
                layout_plans_by_key[layout_key_lookup] = layout_plan

            thread_plan = {
                "spec": thread_spec,
                "thread_config_key": thread_config_key,
                "thread_config_id": thread_config_id,
                "projections": planned_projection_specs,
                "layouts": planned_layout_specs,
                "layouts_by_key": layout_plans_by_key,
            }
            planned_threads.append(thread_plan)
            thread_plans_by_key[thread_config_key_lookup] = thread_plan

        process_plan = {
            "spec": process_spec,
            "process_config_key": process_config_key,
            "process_type": process_type,
            "process_config_id": process_config_id,
            "threads": planned_threads,
            "threads_by_key": thread_plans_by_key,
        }
        planned_processes.append(process_plan)
        process_plans_by_key[process_config_key_lookup] = process_plan

    planned_topology_seeds: list[dict[str, Any]] = []
    seen_topology_seed_keys: set[str] = set()
    for seed_index, topology_seed_spec in enumerate(list(request.topology_seeds or [])):
        seed_key = _normalize_required_key(
            value=topology_seed_spec.key,
            field_name=f"topology_seeds[{seed_index}].key",
        )
        seed_key_lookup = seed_key.casefold()
        if seed_key_lookup in seen_topology_seed_keys:
            raise ValueError(
                f"upsert_environment_experience requires unique topology_seeds[].key: {seed_key!r}"
            )
        seen_topology_seed_keys.add(seed_key_lookup)
        topology_seed_id = stable_environment_topology_seed_id(
            environment_experience_id=environment_experience_id,
            environment_experience_profile_id=profile_id,
            key=seed_key,
        )
        topology_seed_ids.append(topology_seed_id)

        planned_process_seeds: list[dict[str, Any]] = []
        seen_process_seed_keys: set[str] = set()
        for process_seed_index, process_seed_spec in enumerate(
            list(topology_seed_spec.process_seeds or [])
        ):
            process_config_key = _normalize_required_key(
                value=process_seed_spec.process_config_key,
                field_name=(
                    f"topology_seeds[{seed_index}]."
                    f"process_seeds[{process_seed_index}].process_config_key"
                ),
            )
            process_plan = process_plans_by_key.get(process_config_key.casefold())
            if process_plan is None:
                raise ValueError(
                    "topology process seed references unknown profile process config key: "
                    f"{process_config_key!r}"
                )
            process_key = _normalize_required_key(
                value=process_seed_spec.process_key,
                field_name=(
                    f"topology_seeds[{seed_index}]."
                    f"process_seeds[{process_seed_index}].process_key"
                ),
            )
            process_key_lookup = process_key.casefold()
            if process_key_lookup in seen_process_seed_keys:
                raise ValueError(
                    "topology seed process_key values must be unique per topology seed: "
                    f"topology_seed={seed_key!r} process_key={process_key!r}"
                )
            seen_process_seed_keys.add(process_key_lookup)
            process_seed_id = stable_environment_topology_process_seed_id(
                environment_topology_seed_id=topology_seed_id,
                process_config_id=process_plan["process_config_id"],
                process_key=process_key,
            )
            topology_process_seed_ids.append(process_seed_id)

            planned_thread_seeds: list[dict[str, Any]] = []
            seen_thread_seed_keys: set[str] = set()
            main_thread_seed_count = 0
            for thread_seed_index, thread_seed_spec in enumerate(
                list(process_seed_spec.thread_seeds or [])
            ):
                thread_config_key = _normalize_required_key(
                    value=thread_seed_spec.thread_config_key,
                    field_name=(
                        f"topology_seeds[{seed_index}].process_seeds[{process_seed_index}]."
                        f"thread_seeds[{thread_seed_index}].thread_config_key"
                    ),
                )
                thread_plan = process_plan["threads_by_key"].get(
                    thread_config_key.casefold()
                )
                if thread_plan is None:
                    raise ValueError(
                        "topology thread seed references unknown profile thread config key: "
                        f"process_config_key={process_config_key!r} thread_config_key={thread_config_key!r}"
                    )
                thread_key = _normalize_required_key(
                    value=thread_seed_spec.thread_key,
                    field_name=(
                        f"topology_seeds[{seed_index}].process_seeds[{process_seed_index}]."
                        f"thread_seeds[{thread_seed_index}].thread_key"
                    ),
                )
                thread_key_lookup = thread_key.casefold()
                if thread_key_lookup in seen_thread_seed_keys:
                    raise ValueError(
                        "topology seed thread_key values must be unique per process seed: "
                        f"process_key={process_key!r} thread_key={thread_key!r}"
                    )
                seen_thread_seed_keys.add(thread_key_lookup)
                if bool(thread_seed_spec.is_main):
                    main_thread_seed_count += 1
                thread_seed_id = stable_environment_topology_thread_seed_id(
                    environment_topology_process_seed_id=process_seed_id,
                    thread_config_id=thread_plan["thread_config_id"],
                    thread_key=thread_key,
                )
                topology_thread_seed_ids.append(thread_seed_id)

                planned_layout_seeds: list[dict[str, Any]] = []
                seen_layout_seed_keys: set[str] = set()
                active_layout_seed_count = 0
                for layout_seed_index, layout_seed_spec in enumerate(
                    list(thread_seed_spec.layout_seeds or [])
                ):
                    layout_key = _normalize_required_key(
                        value=layout_seed_spec.layout_key,
                        field_name=(
                            f"topology_seeds[{seed_index}].process_seeds[{process_seed_index}]."
                            f"thread_seeds[{thread_seed_index}].layout_seeds[{layout_seed_index}].layout_key"
                        ),
                    )
                    layout_plan = thread_plan["layouts_by_key"].get(
                        layout_key.casefold()
                    )
                    if layout_plan is None:
                        raise ValueError(
                            "topology layout seed references a layout not declared by the ThreadConfig: "
                            f"thread_config_key={thread_config_key!r} layout_key={layout_key!r}"
                        )
                    layout_key_lookup = layout_key.casefold()
                    if layout_key_lookup in seen_layout_seed_keys:
                        raise ValueError(
                            "topology layout seed layout_key values must be unique per thread seed: "
                            f"thread_key={thread_key!r} layout_key={layout_key!r}"
                        )
                    seen_layout_seed_keys.add(layout_key_lookup)
                    if bool(layout_seed_spec.activate_on_seed):
                        active_layout_seed_count += 1
                    layout_seed_id = stable_environment_topology_thread_layout_seed_id(
                        environment_topology_thread_seed_id=thread_seed_id,
                        layout_config_id=layout_plan["layout_config_id"],
                    )
                    topology_thread_layout_seed_ids.append(layout_seed_id)
                    planned_layout_seeds.append(
                        {
                            "spec": layout_seed_spec,
                            "layout_key": layout_key,
                            "layout_config_id": layout_plan["layout_config_id"],
                            "layout_seed_id": layout_seed_id,
                        }
                    )
                if active_layout_seed_count > 1:
                    raise ValueError(
                        "topology thread seed allows a single activate_on_seed layout: "
                        f"thread_key={thread_key!r}"
                    )
                planned_thread_seeds.append(
                    {
                        "spec": thread_seed_spec,
                        "thread_key": thread_key,
                        "thread_seed_id": thread_seed_id,
                        "thread_plan": thread_plan,
                        "layout_seeds": planned_layout_seeds,
                    }
                )
            if main_thread_seed_count > 1:
                raise ValueError(
                    "topology process seed allows a single main thread seed: "
                    f"process_key={process_key!r}"
                )
            planned_process_seeds.append(
                {
                    "spec": process_seed_spec,
                    "process_key": process_key,
                    "process_seed_id": process_seed_id,
                    "process_plan": process_plan,
                    "thread_seeds": planned_thread_seeds,
                }
            )

        planned_topology_seeds.append(
            {
                "spec": topology_seed_spec,
                "key": seed_key,
                "topology_seed_id": topology_seed_id,
                "process_seeds": planned_process_seeds,
            }
        )

    if request.validate_only:
        return UpsertEnvironmentExperienceResponse(
            operation="upsert_environment_experience",
            actor_id=request.actor_id,
            environment_id=environment_id,
            process_id=context_process_id,
            thread_id=context_thread_id,
            branch_id=lane_branch_id,
            projection_hash=environment_experience_projection_hash,
            status="succeeded",
            error=None,
            environment_experience_profile_id=profile_id,
            process_config_ids=_dedupe_ids(process_config_ids),
            thread_config_ids=_dedupe_ids(thread_config_ids),
            thread_projection_association_ids=_dedupe_ids(
                thread_projection_association_ids
            ),
            thread_layout_config_ids=_dedupe_ids(thread_layout_config_ids),
            topology_seed_ids=_dedupe_ids(topology_seed_ids),
            topology_process_seed_ids=_dedupe_ids(topology_process_seed_ids),
            topology_thread_seed_ids=_dedupe_ids(topology_thread_seed_ids),
            topology_thread_layout_seed_ids=_dedupe_ids(
                topology_thread_layout_seed_ids
            ),
        )

    existing_environment_lane_ids = await lane_support.materialize_lane_instance_ids(
        index=index,
        branch_id=lane_branch_id,
        projection_hash=environment_projection_hash,
    )
    if environment_id not in existing_environment_lane_ids:
        raise RuntimeError(
            "Environment lane is not initialized for upsert_environment_experience. "
            "Run ensure_ready first."
        )

    environment_create_profile_fn_id = _try_resolve_public_function_id(
        index=index,
        class_name_suffix="aware_environment_ontology.environment.environment.Environment",
        function_name="create_experience_profile",
    )
    profile_create_process_config_fn_id: UUID | None = None
    profile_add_program_fn_id: UUID | None = None
    environment_experience_create_profile_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment.environment_experience.EnvironmentExperience"
        ),
        function_name="create_profile",
    )
    environment_experience_create_topology_seed_fn_id: UUID | None = None
    topology_seed_add_process_seed_fn_id: UUID | None = None
    topology_process_seed_add_thread_seed_fn_id: UUID | None = None
    topology_thread_seed_add_layout_seed_fn_id: UUID | None = None
    if planned_topology_seeds:
        environment_experience_create_topology_seed_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix=(
                "aware_experience_ontology.environment.environment_experience.EnvironmentExperience"
            ),
            function_name="create_topology_seed",
        )
        topology_seed_add_process_seed_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix=(
                "aware_experience_ontology.environment.environment_topology_seed.EnvironmentTopologySeed"
            ),
            function_name="add_process_seed",
        )
        topology_process_seed_add_thread_seed_fn_id = (
            ocg_support.resolve_public_function_id(
                index=index,
                class_name_suffix=(
                    "aware_experience_ontology.environment."
                    "environment_topology_process_seed.EnvironmentTopologyProcessSeed"
                ),
                function_name="add_thread_seed",
            )
        )
        topology_thread_seed_add_layout_seed_fn_id = (
            ocg_support.resolve_public_function_id(
                index=index,
                class_name_suffix=(
                    "aware_experience_ontology.environment."
                    "environment_topology_thread_seed.EnvironmentTopologyThreadSeed"
                ),
                function_name="add_layout_seed",
            )
        )
    profile_add_program_apply_fn_id: UUID | None = None
    if planned_program_applies:
        profile_add_program_apply_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix=(
                "aware_experience_ontology.environment."
                "environment_experience_profile.EnvironmentExperienceProfile"
            ),
            function_name="add_program_apply",
        )
    process_config_create_thread_config_fn_id: UUID | None = None
    if planned_processes:
        process_config_create_thread_config_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="aware_environment_ontology.process.process_config.ProcessConfig",
            function_name="create_thread_config",
        )
    has_thread_projection_associations = any(
        bool(thread_plan["projections"])
        for process_plan in planned_processes
        for thread_plan in process_plan["threads"]
    )
    thread_config_add_projection_fn_id: UUID | None = None
    if has_thread_projection_associations:
        thread_config_add_projection_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="aware_environment_ontology.thread.thread_config.ThreadConfig",
            function_name="add_projection_graph_identity",
        )
    has_thread_layout_configs = any(
        bool(thread_plan["layouts"])
        for process_plan in planned_processes
        for thread_plan in process_plan["threads"]
    )
    thread_config_add_layout_config_fn_id: UUID | None = None
    if has_thread_layout_configs:
        thread_config_add_layout_config_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="aware_environment_ontology.thread.thread_config.ThreadConfig",
            function_name="add_layout_config",
        )

    if environment_create_profile_fn_id is not None:
        create_profile_result = (
            await invoke_support.invoke_instance_environment_function(
                runtime=runtime,
                index=index,
                actor_id=request.actor_id,
                environment_id=environment_id,
                process_id=context_process_id,
                thread_id=context_thread_id,
                branch_id=lane_branch_id,
                projection_hash=environment_projection_hash,
                object_id=environment_id,
                function_id=environment_create_profile_fn_id,
                args=[
                    profile_spec.key,
                    profile_spec.title,
                    profile_spec.description,
                    profile_spec.narrative,
                ],
                commit=True,
            )
        )
        if create_profile_result.status != "succeeded":
            if not _is_retired_environment_create_profile_error(
                error=create_profile_result.error
            ):
                invoke_support.assert_invoke_succeeded(
                    response=create_profile_result,
                    label="Environment.create_experience_profile",
                )

    # The EnvironmentExperience projection is intentionally portal-separated from the
    # Environment territory lane. Creating/binding the profile via Environment does not
    # initialize the EnvironmentExperience lane HEAD, so the first instance call on the
    # profile would fail closed ("no head commit"). Initialize the lane via the profile
    # root constructor when empty so subsequent instance mutations are commit-backed.
    from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore

    env_exp_head = await FSCommitStore().head(
        branch_id=lane_branch_id,
        projection_hash=environment_experience_projection_hash,
    )
    if env_exp_head is None or not env_exp_head.get("commit_id"):
        env_exp_opg = index.opg_by_hash.get(environment_experience_projection_hash)
        if env_exp_opg is None:
            raise RuntimeError(
                "EnvironmentExperience OPG not found in runtime index: "
                f"projection_hash={environment_experience_projection_hash}"
            )

        profile_build_fn_id = ocg_support.resolve_single_opg_constructor_function_id(
            index=index,
            object_projection_graph_id=env_exp_opg.id,
        )
        init_req = InvokeFunctionRequest(
            operation="invoke_function",
            actor_id=request.actor_id,
            environment_id=environment_id,
            process_id=context_process_id,
            thread_id=context_thread_id,
            branch_id=lane_branch_id,
            projection_hash=environment_experience_projection_hash,
            call_target=InvokeFunctionCallTarget.opg_constructor,
            object_id=None,
            object_projection_graph_id=env_exp_opg.id,
            function_id=profile_build_fn_id,
            args=JsonArray(),
            kwargs=JsonObject(
                {
                    "fqn_prefix": environment_experience_fqn_prefix,
                }
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        )
        init_resp = await runtime.invoker.invoke_function_with_index(
            index=index, request=init_req
        )
        invoke_support.assert_invoke_succeeded(
            response=init_resp,
            label="EnvironmentExperience.build(opg_constructor)",
        )

    create_profile_result = await invoke_support.invoke_instance_environment_function(
        runtime=runtime,
        index=index,
        actor_id=request.actor_id,
        environment_id=environment_id,
        process_id=context_process_id,
        thread_id=context_thread_id,
        branch_id=lane_branch_id,
        projection_hash=environment_experience_projection_hash,
        object_id=environment_experience_id,
        function_id=environment_experience_create_profile_fn_id,
        args=[
            environment_profile_id,
            profile_key,
            None,
            profile_spec.title,
            profile_spec.description,
            profile_spec.narrative,
        ],
        commit=True,
    )
    invoke_support.assert_invoke_succeeded(
        response=create_profile_result,
        label=f"EnvironmentExperience.create_profile({profile_key})",
    )

    await materialize_environment_experience_profile_actor_role_ontology(
        runtime=runtime,
        index=index,
        actor_id=request.actor_id,
        lane=MaterializationLaneContext(
            branch_id=lane_branch_id,
            projection_hash=environment_experience_profile_projection_hash,
        ),
        environment_experience_profile_id=profile_id,
        role_specs=planned_role_specs,
        actor_specs=planned_actor_specs,
    )

    for program_plan in planned_programs:
        program_ref = program_plan["program_ref"]
        program_config_id = program_plan["program_config_id"]
        add_program_result = await invoke_support.invoke_instance_environment_function(
            runtime=runtime,
            index=index,
            actor_id=request.actor_id,
            environment_id=environment_id,
            process_id=context_process_id,
            thread_id=context_thread_id,
            branch_id=lane_branch_id,
            projection_hash=environment_experience_profile_projection_hash,
            object_id=profile_id,
            function_id=profile_add_program_fn_id,
            args=[program_config_id],
            commit=True,
        )
        invoke_support.assert_invoke_succeeded(
            response=add_program_result,
            label=f"EnvironmentExperienceProfile.add_program({program_ref})",
        )

    for program_apply_plan in planned_program_applies:
        if profile_add_program_apply_fn_id is None:
            raise RuntimeError(
                "EnvironmentExperienceProfile.add_program_apply function id is required when "
                "profile program applies are planned"
            )
        program_apply_spec = program_apply_plan["spec"]
        installed_program_plan = program_apply_plan["program_plan"]
        add_program_apply_result = (
            await invoke_support.invoke_instance_environment_function(
                runtime=runtime,
                index=index,
                actor_id=request.actor_id,
                environment_id=environment_id,
                process_id=context_process_id,
                thread_id=context_thread_id,
                branch_id=lane_branch_id,
                projection_hash=environment_experience_profile_projection_hash,
                object_id=profile_id,
                function_id=profile_add_program_apply_fn_id,
                args=[
                    installed_program_plan["program_config_id"],
                    program_apply_plan["key"],
                    program_apply_plan["phase"],
                    program_apply_spec.position,
                    program_apply_spec.message,
                    dict(program_apply_spec.symbols or {}),
                ],
                commit=True,
            )
        )
        invoke_support.assert_invoke_succeeded(
            response=add_program_apply_result,
            label=(
                "EnvironmentExperienceProfile.add_program_apply("
                + f"{program_apply_plan['key']}:{program_apply_plan['program_ref']})"
            ),
        )

    for process_plan in planned_processes:
        process_spec = process_plan["spec"]
        process_config_key = process_plan["process_config_key"]
        process_type = process_plan["process_type"]
        process_config_id = process_plan["process_config_id"]
        thread_plans = process_plan["threads"]

        profile_create_process_config_result = (
            await invoke_support.invoke_instance_environment_function(
                runtime=runtime,
                index=index,
                actor_id=request.actor_id,
                environment_id=environment_id,
                process_id=context_process_id,
                thread_id=context_thread_id,
                branch_id=lane_branch_id,
                projection_hash=environment_experience_profile_projection_hash,
                object_id=profile_id,
                function_id=profile_create_process_config_fn_id,
                args=[
                    process_type,
                    process_config_key,
                    process_spec.title,
                    process_spec.description,
                    process_spec.shape,
                    process_spec.position,
                    process_spec.narrative,
                    process_spec.intent,
                ],
                commit=True,
            )
        )
        invoke_support.assert_invoke_succeeded(
            response=profile_create_process_config_result,
            label=f"EnvironmentExperienceProfile.create_process_config({process_config_key})",
        )

        for thread_plan in thread_plans:
            thread_spec = thread_plan["spec"]
            thread_config_key = thread_plan["thread_config_key"]
            thread_config_id = thread_plan["thread_config_id"]
            projection_plans = thread_plan["projections"]
            layout_plans = thread_plan["layouts"]

            process_config_create_thread_result = (
                await invoke_support.invoke_instance_environment_function(
                    runtime=runtime,
                    index=index,
                    actor_id=request.actor_id,
                    environment_id=environment_id,
                    process_id=context_process_id,
                    thread_id=context_thread_id,
                    branch_id=lane_branch_id,
                    projection_hash=environment_experience_profile_projection_hash,
                    object_id=process_config_id,
                    function_id=process_config_create_thread_config_fn_id,
                    args=[
                        thread_config_key,
                        thread_spec.title,
                        thread_spec.description,
                        thread_spec.workspace_view_key,
                        thread_spec.position,
                        thread_spec.narrative,
                        thread_spec.intent,
                        thread_spec.state_prompt_template,
                    ],
                    commit=True,
                )
            )
            invoke_support.assert_invoke_succeeded(
                response=process_config_create_thread_result,
                label=f"ProcessConfig.create_thread_config({thread_config_key})",
            )

            for projection_plan in projection_plans:
                projection_spec = projection_plan["spec"]
                opgi_id = projection_plan["opgi_id"]
                if thread_config_add_projection_fn_id is None:
                    raise RuntimeError(
                        "ThreadConfig.add_projection_graph_identity function id is required when "
                        "thread projection associations are planned"
                    )
                projection_add_result = (
                    await invoke_support.invoke_instance_environment_function(
                        runtime=runtime,
                        index=index,
                        actor_id=request.actor_id,
                        environment_id=environment_id,
                        process_id=context_process_id,
                        thread_id=context_thread_id,
                        branch_id=lane_branch_id,
                        projection_hash=environment_experience_profile_projection_hash,
                        object_id=thread_config_id,
                        function_id=thread_config_add_projection_fn_id,
                        args=[
                            opgi_id,
                            projection_plan["view_key"],
                            projection_spec.position,
                            projection_spec.is_default,
                            projection_spec.narrative,
                            projection_spec.intent,
                        ],
                        commit=True,
                    )
                )
                invoke_support.assert_invoke_succeeded(
                    response=projection_add_result,
                    label=f"ThreadConfig.add_projection_graph_identity({thread_config_key})",
                )

            for layout_plan in layout_plans:
                layout_spec = layout_plan["spec"]
                if thread_config_add_layout_config_fn_id is None:
                    raise RuntimeError(
                        "ThreadConfig.add_layout_config function id is required when "
                        "thread layout configs are planned"
                    )
                layout_add_result = (
                    await invoke_support.invoke_instance_environment_function(
                        runtime=runtime,
                        index=index,
                        actor_id=request.actor_id,
                        environment_id=environment_id,
                        process_id=context_process_id,
                        thread_id=context_thread_id,
                        branch_id=lane_branch_id,
                        projection_hash=environment_experience_profile_projection_hash,
                        object_id=thread_config_id,
                        function_id=thread_config_add_layout_config_fn_id,
                        args=[
                            layout_plan["layout_config_id"],
                            layout_plan["key"],
                            layout_spec.position,
                            layout_spec.narrative,
                            layout_spec.intent,
                        ],
                        commit=True,
                    )
                )
                invoke_support.assert_invoke_succeeded(
                    response=layout_add_result,
                    label=f"ThreadConfig.add_layout_config({thread_config_key})",
                )

    for topology_seed_plan in planned_topology_seeds:
        if environment_experience_create_topology_seed_fn_id is None:
            raise RuntimeError(
                "EnvironmentExperience.create_topology_seed function id is required when topology seeds are planned"
            )
        topology_seed_spec = topology_seed_plan["spec"]
        create_topology_seed_result = (
            await invoke_support.invoke_instance_environment_function(
                runtime=runtime,
                index=index,
                actor_id=request.actor_id,
                environment_id=environment_id,
                process_id=context_process_id,
                thread_id=context_thread_id,
                branch_id=lane_branch_id,
                projection_hash=environment_experience_projection_hash,
                object_id=environment_experience_id,
                function_id=environment_experience_create_topology_seed_fn_id,
                args=[
                    profile_id,
                    topology_seed_plan["key"],
                    topology_seed_spec.title,
                    topology_seed_spec.description,
                    topology_seed_spec.narrative,
                ],
                commit=True,
            )
        )
        invoke_support.assert_invoke_succeeded(
            response=create_topology_seed_result,
            label=f"EnvironmentExperience.create_topology_seed({topology_seed_plan['key']})",
        )

        for process_seed_plan in topology_seed_plan["process_seeds"]:
            if topology_seed_add_process_seed_fn_id is None:
                raise RuntimeError(
                    "EnvironmentTopologySeed.add_process_seed function id is required when process seeds are planned"
                )
            process_seed_spec = process_seed_plan["spec"]
            process_plan = process_seed_plan["process_plan"]
            add_process_seed_result = (
                await invoke_support.invoke_instance_environment_function(
                    runtime=runtime,
                    index=index,
                    actor_id=request.actor_id,
                    environment_id=environment_id,
                    process_id=context_process_id,
                    thread_id=context_thread_id,
                    branch_id=lane_branch_id,
                    projection_hash=environment_topology_seed_projection_hash,
                    object_id=topology_seed_plan["topology_seed_id"],
                    function_id=topology_seed_add_process_seed_fn_id,
                    args=[
                        process_plan["process_config_id"],
                        process_seed_plan["process_key"],
                        process_seed_spec.key,
                        process_seed_spec.title,
                        process_seed_spec.description,
                        process_seed_spec.position,
                        process_seed_spec.narrative,
                        process_seed_spec.intent,
                    ],
                    commit=True,
                )
            )
            invoke_support.assert_invoke_succeeded(
                response=add_process_seed_result,
                label=f"EnvironmentTopologySeed.add_process_seed({process_seed_plan['process_key']})",
            )

            for thread_seed_plan in process_seed_plan["thread_seeds"]:
                if topology_process_seed_add_thread_seed_fn_id is None:
                    raise RuntimeError(
                        "EnvironmentTopologyProcessSeed.add_thread_seed function id is required when "
                        "thread seeds are planned"
                    )
                thread_seed_spec = thread_seed_plan["spec"]
                thread_plan = thread_seed_plan["thread_plan"]
                add_thread_seed_result = (
                    await invoke_support.invoke_instance_environment_function(
                        runtime=runtime,
                        index=index,
                        actor_id=request.actor_id,
                        environment_id=environment_id,
                        process_id=context_process_id,
                        thread_id=context_thread_id,
                        branch_id=lane_branch_id,
                        projection_hash=environment_topology_seed_projection_hash,
                        object_id=process_seed_plan["process_seed_id"],
                        function_id=topology_process_seed_add_thread_seed_fn_id,
                        args=[
                            thread_plan["thread_config_id"],
                            thread_seed_plan["thread_key"],
                            thread_seed_spec.key,
                            thread_seed_spec.title,
                            thread_seed_spec.description,
                            thread_seed_spec.position,
                            thread_seed_spec.is_main,
                            thread_seed_spec.narrative,
                            thread_seed_spec.intent,
                        ],
                        commit=True,
                    )
                )
                invoke_support.assert_invoke_succeeded(
                    response=add_thread_seed_result,
                    label=f"EnvironmentTopologyProcessSeed.add_thread_seed({thread_seed_plan['thread_key']})",
                )

                for layout_seed_plan in thread_seed_plan["layout_seeds"]:
                    if topology_thread_seed_add_layout_seed_fn_id is None:
                        raise RuntimeError(
                            "EnvironmentTopologyThreadSeed.add_layout_seed function id is required when "
                            "layout seeds are planned"
                        )
                    layout_seed_spec = layout_seed_plan["spec"]
                    add_layout_seed_result = (
                        await invoke_support.invoke_instance_environment_function(
                            runtime=runtime,
                            index=index,
                            actor_id=request.actor_id,
                            environment_id=environment_id,
                            process_id=context_process_id,
                            thread_id=context_thread_id,
                            branch_id=lane_branch_id,
                            projection_hash=environment_topology_seed_projection_hash,
                            object_id=thread_seed_plan["thread_seed_id"],
                            function_id=topology_thread_seed_add_layout_seed_fn_id,
                            args=[
                                layout_seed_plan["layout_config_id"],
                                layout_seed_spec.key,
                                layout_seed_spec.position,
                                layout_seed_spec.activate_on_seed,
                                layout_seed_spec.narrative,
                                layout_seed_spec.intent,
                            ],
                            commit=True,
                        )
                    )
                    invoke_support.assert_invoke_succeeded(
                        response=add_layout_seed_result,
                        label=f"EnvironmentTopologyThreadSeed.add_layout_seed({layout_seed_plan['layout_key']})",
                    )

    return UpsertEnvironmentExperienceResponse(
        operation="upsert_environment_experience",
        actor_id=request.actor_id,
        environment_id=environment_id,
        process_id=context_process_id,
        thread_id=context_thread_id,
        branch_id=lane_branch_id,
        projection_hash=environment_experience_profile_projection_hash,
        status="succeeded",
        error=None,
        environment_experience_profile_id=profile_id,
        process_config_ids=_dedupe_ids(process_config_ids),
        thread_config_ids=_dedupe_ids(thread_config_ids),
        thread_projection_association_ids=_dedupe_ids(
            thread_projection_association_ids
        ),
        thread_layout_config_ids=_dedupe_ids(thread_layout_config_ids),
        topology_seed_ids=_dedupe_ids(topology_seed_ids),
        topology_process_seed_ids=_dedupe_ids(topology_process_seed_ids),
        topology_thread_seed_ids=_dedupe_ids(topology_thread_seed_ids),
        topology_thread_layout_seed_ids=_dedupe_ids(topology_thread_layout_seed_ids),
    )


async def provision_environment_experience(
    resolver: EnvironmentRuntimeResolverLike,
    request: ProvisionEnvironmentExperienceRequest,
) -> ProvisionEnvironmentExperienceResponse:
    runtime = await resolver.get_runtime(environment_id=request.environment_id)
    index = runtime.invoker.get_index()

    environment_id = request.environment_id

    boot_process_id = stable_ids.stable_boot_process_id(environment_id=environment_id)
    boot_thread_id = stable_ids.stable_boot_thread_id(environment_id=environment_id)
    boot_branch_id = stable_ids.stable_branch_id(
        environment_id=environment_id, thread_id=boot_thread_id
    )

    lane_branch_id = request.branch_id or boot_branch_id
    context_process_id = request.process_id or boot_process_id
    context_thread_id = request.thread_id or boot_thread_id

    environment_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index, projection_name="Environment"
    )
    (
        environment_experience_profile_projection_hash,
        profile_oig,
        profile_id,
        profile_source_id,
    ) = await _load_environment_experience_profile_graph(
        index=index,
        lane_branch_id=lane_branch_id,
        requested_profile_id=request.environment_experience_profile_id,
    )
    projection_branches = resolve_environment_experience_projection_branches(
        index=index
    )
    topology_oig = await _load_committed_environment_experience_projection_oig(
        index=index,
        lane_branch_id=lane_branch_id,
        projection_hash=projection_branches.environment_topology_seed,
        projection_name=_ENVIRONMENT_TOPOLOGY_SEED_PROJECTION_NAME,
    )

    process_config_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix="aware_environment_ontology.process.process_config.ProcessConfig",
    )
    thread_config_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix="aware_environment_ontology.thread.thread_config.ThreadConfig",
    )
    thread_layout_config_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.thread."
            "aware_environment_ontology.thread.thread_config_layout_config.ThreadConfigLayoutConfig"
        ),
    )
    topology_seed_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment.environment_topology_seed.EnvironmentTopologySeed"
        ),
    )
    topology_process_seed_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_topology_process_seed.EnvironmentTopologyProcessSeed"
        ),
    )
    topology_thread_seed_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_topology_thread_seed.EnvironmentTopologyThreadSeed"
        ),
    )
    topology_thread_layout_seed_class_id = ocg_support.resolve_class_config_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_topology_thread_layout_seed.EnvironmentTopologyThreadLayoutSeed"
        ),
    )
    process_attr_name_by_id = ocg_support.build_attr_name_by_id_for_class_config(
        index=index, class_config_id=process_config_class_id
    )
    thread_attr_name_by_id = ocg_support.build_attr_name_by_id_for_class_config(
        index=index, class_config_id=thread_config_class_id
    )
    thread_layout_attr_name_by_id = ocg_support.build_attr_name_by_id_for_class_config(
        index=index,
        class_config_id=thread_layout_config_class_id,
    )
    topology_seed_attr_name_by_id = ocg_support.build_attr_name_by_id_for_class_config(
        index=index, class_config_id=topology_seed_class_id
    )
    topology_process_seed_attr_name_by_id = (
        ocg_support.build_attr_name_by_id_for_class_config(
            index=index, class_config_id=topology_process_seed_class_id
        )
    )
    topology_thread_seed_attr_name_by_id = (
        ocg_support.build_attr_name_by_id_for_class_config(
            index=index, class_config_id=topology_thread_seed_class_id
        )
    )
    topology_thread_layout_seed_attr_name_by_id = (
        ocg_support.build_attr_name_by_id_for_class_config(
            index=index, class_config_id=topology_thread_layout_seed_class_id
        )
    )

    ci_by_id: dict[UUID, Any] = {
        ci.id: ci
        for ci in tuple(profile_oig.class_instances)
        + tuple(topology_oig.class_instances)
    }
    process_config_ids_in_graph = {
        ci.id
        for ci in profile_oig.class_instances
        if ci.class_config_id == process_config_class_id
    }
    thread_config_ids_in_graph = {
        ci.id
        for ci in profile_oig.class_instances
        if ci.class_config_id == thread_config_class_id
    }
    thread_layout_config_ids_in_graph = {
        ci.id
        for ci in profile_oig.class_instances
        if ci.class_config_id == thread_layout_config_class_id
    }
    topology_seed_key = _normalize_required_key(
        value=request.topology_seed_key,
        field_name="topology_seed_key",
    )
    selected_topology_seed_ci = None
    for ci in topology_oig.class_instances:
        if ci.class_config_id != topology_seed_class_id:
            continue
        candidate_key = (
            oig_support.extract_attr_scalar(
                class_instance=ci,
                attr_name_by_id=topology_seed_attr_name_by_id,
                name="key",
            )
            or ""
        ).strip()
        if candidate_key.casefold() != topology_seed_key.casefold():
            continue
        candidate_profile_id_raw = oig_support.extract_attr_scalar(
            class_instance=ci,
            attr_name_by_id=topology_seed_attr_name_by_id,
            name="environment_experience_profile_id",
        )
        if candidate_profile_id_raw is not None and UUID(
            str(candidate_profile_id_raw)
        ) not in {profile_id, profile_source_id}:
            continue
        selected_topology_seed_ci = ci
        break
    if selected_topology_seed_ci is None:
        raise RuntimeError(
            "provision_environment_experience could not resolve topology seed: "
            f"profile_id={profile_id} topology_seed_key={topology_seed_key!r}"
        )

    thread_config_ids_by_process_config_id: dict[UUID, set[UUID]] = {}
    thread_layout_config_ids_by_thread_config_id: dict[UUID, list[UUID]] = {}
    for rel in profile_oig.class_instance_relationships:
        if (
            rel.source_class_instance_id in process_config_ids_in_graph
            and rel.target_class_instance_id in thread_config_ids_in_graph
        ):
            thread_config_ids_by_process_config_id.setdefault(
                rel.source_class_instance_id, set()
            ).add(rel.target_class_instance_id)
        if (
            rel.source_class_instance_id in thread_config_ids_in_graph
            and rel.target_class_instance_id in thread_layout_config_ids_in_graph
        ):
            thread_layout_config_ids_by_thread_config_id.setdefault(
                rel.source_class_instance_id, []
            ).append(rel.target_class_instance_id)

    planned_processes: list[dict[str, Any]] = []
    process_ids: list[UUID] = []
    thread_ids: list[UUID] = []
    thread_layout_ids: list[UUID] = []
    planned_process_seed_ids = _dedupe_ids(
        [
            rel.target_class_instance_id
            for rel in topology_oig.class_instance_relationships
            if rel.source_class_instance_id == selected_topology_seed_ci.id
            and rel.target_class_instance_id
            in {
                ci.id
                for ci in topology_oig.class_instances
                if ci.class_config_id == topology_process_seed_class_id
            }
        ]
    )
    for process_seed_id in planned_process_seed_ids:
        process_seed_ci = ci_by_id.get(process_seed_id)
        if process_seed_ci is None:
            continue
        process_config_id_raw = oig_support.extract_attr_scalar(
            class_instance=process_seed_ci,
            attr_name_by_id=topology_process_seed_attr_name_by_id,
            name="process_config_id",
        )
        if process_config_id_raw is None:
            raise RuntimeError(
                f"EnvironmentTopologyProcessSeed.process_config_id is required: {process_seed_id}"
            )
        process_config_id = UUID(str(process_config_id_raw))
        process_ci = ci_by_id.get(process_config_id)
        if process_ci is None or process_config_id not in process_config_ids_in_graph:
            raise RuntimeError(
                "EnvironmentTopologyProcessSeed references unknown ProcessConfig: "
                f"process_seed_id={process_seed_id} process_config_id={process_config_id}"
            )
        process_key = _normalize_required_key(
            value=cast(
                str | None,
                oig_support.extract_attr_scalar(
                    class_instance=process_seed_ci,
                    attr_name_by_id=topology_process_seed_attr_name_by_id,
                    name="process_key",
                ),
            ),
            field_name=f"EnvironmentTopologyProcessSeed.process_key({process_seed_id})",
        )
        process_id = stable_ids.stable_process_id_for_key(
            environment_id=environment_id, process_key=process_key
        )

        planned_thread_seed_ids = _dedupe_ids(
            [
                rel.target_class_instance_id
                for rel in topology_oig.class_instance_relationships
                if rel.source_class_instance_id == process_seed_id
                and rel.target_class_instance_id
                in {
                    ci.id
                    for ci in topology_oig.class_instances
                    if ci.class_config_id == topology_thread_seed_class_id
                }
            ]
        )

        planned_threads: list[dict[str, Any]] = []
        for thread_seed_id in planned_thread_seed_ids:
            thread_seed_ci = ci_by_id.get(thread_seed_id)
            if thread_seed_ci is None:
                continue
            thread_config_id_raw = oig_support.extract_attr_scalar(
                class_instance=thread_seed_ci,
                attr_name_by_id=topology_thread_seed_attr_name_by_id,
                name="thread_config_id",
            )
            if thread_config_id_raw is None:
                raise RuntimeError(
                    f"EnvironmentTopologyThreadSeed.thread_config_id is required: {thread_seed_id}"
                )
            thread_config_id = UUID(str(thread_config_id_raw))
            thread_ci = ci_by_id.get(thread_config_id)
            if thread_ci is None or thread_config_id not in thread_config_ids_in_graph:
                raise RuntimeError(
                    "EnvironmentTopologyThreadSeed references unknown ThreadConfig: "
                    f"thread_seed_id={thread_seed_id} thread_config_id={thread_config_id}"
                )
            if thread_config_id not in thread_config_ids_by_process_config_id.get(
                process_config_id, set()
            ):
                raise RuntimeError(
                    "EnvironmentTopologyThreadSeed thread_config_id is not under the referenced ProcessConfig: "
                    f"process_config_id={process_config_id} thread_config_id={thread_config_id}"
                )
            thread_key = _normalize_required_key(
                value=cast(
                    str | None,
                    oig_support.extract_attr_scalar(
                        class_instance=thread_seed_ci,
                        attr_name_by_id=topology_thread_seed_attr_name_by_id,
                        name="thread_key",
                    ),
                ),
                field_name=f"EnvironmentTopologyThreadSeed.thread_key({thread_seed_id})",
            )
            thread_id = stable_ids.stable_thread_id_for_key(
                environment_id=environment_id, thread_key=thread_key
            )

            layout_candidates_by_config_id: dict[UUID, dict[str, Any]] = {}
            for thread_layout_config_id in _dedupe_ids(
                thread_layout_config_ids_by_thread_config_id.get(thread_config_id, [])
            ):
                thread_layout_ci = ci_by_id.get(thread_layout_config_id)
                if thread_layout_ci is None:
                    continue
                layout_key = (
                    oig_support.extract_attr_scalar(
                        class_instance=thread_layout_ci,
                        attr_name_by_id=thread_layout_attr_name_by_id,
                        name="key",
                    )
                    or ""
                ).strip()
                if not layout_key:
                    raise RuntimeError(
                        "Environment ThreadConfigLayoutConfig.key must carry the Attention LayoutConfig key "
                        f"(thread_config_id={thread_config_id} layout_assoc_id={thread_layout_config_id})"
                    )
                layout_config_id_raw = oig_support.extract_attr_scalar(
                    class_instance=thread_layout_ci,
                    attr_name_by_id=thread_layout_attr_name_by_id,
                    name="layout_config_id",
                )
                layout_config_id = (
                    UUID(str(layout_config_id_raw))
                    if layout_config_id_raw is not None
                    else stable_layout_config_id(key=layout_key)
                )
                layout_candidates_by_config_id[layout_config_id] = {
                    "thread_layout_config_id": thread_layout_config_id,
                    "layout_key": layout_key,
                    "layout_config_id": layout_config_id,
                    "position": _coerce_optional_int(
                        value=oig_support.extract_attr_scalar(
                            class_instance=thread_layout_ci,
                            attr_name_by_id=thread_layout_attr_name_by_id,
                            name="position",
                        ),
                        field_name=f"EnvironmentThreadConfigLayoutConfig.position({layout_key})",
                    ),
                    "narrative": oig_support.extract_attr_scalar(
                        class_instance=thread_layout_ci,
                        attr_name_by_id=thread_layout_attr_name_by_id,
                        name="narrative",
                    ),
                }

            planned_layout_seed_ids = _dedupe_ids(
                [
                    rel.target_class_instance_id
                    for rel in topology_oig.class_instance_relationships
                    if rel.source_class_instance_id == thread_seed_id
                    and rel.target_class_instance_id
                    in {
                        ci.id
                        for ci in topology_oig.class_instances
                        if ci.class_config_id == topology_thread_layout_seed_class_id
                    }
                ]
            )
            planned_layouts: list[dict[str, Any]] = []
            active_layout_count = 0
            for layout_seed_id in planned_layout_seed_ids:
                layout_seed_ci = ci_by_id.get(layout_seed_id)
                if layout_seed_ci is None:
                    continue
                layout_config_id_raw = oig_support.extract_attr_scalar(
                    class_instance=layout_seed_ci,
                    attr_name_by_id=topology_thread_layout_seed_attr_name_by_id,
                    name="layout_config_id",
                )
                if layout_config_id_raw is None:
                    raise RuntimeError(
                        f"EnvironmentTopologyThreadLayoutSeed.layout_config_id is required: {layout_seed_id}"
                    )
                layout_config_id = UUID(str(layout_config_id_raw))
                layout_candidate = layout_candidates_by_config_id.get(layout_config_id)
                if layout_candidate is None:
                    raise RuntimeError(
                        "EnvironmentTopologyThreadLayoutSeed references a LayoutConfig not declared "
                        "by the selected ThreadConfig: "
                        f"thread_config_id={thread_config_id} layout_config_id={layout_config_id}"
                    )
                activate_on_seed = _coerce_bool(
                    value=oig_support.extract_attr_scalar(
                        class_instance=layout_seed_ci,
                        attr_name_by_id=topology_thread_layout_seed_attr_name_by_id,
                        name="activate_on_seed",
                    ),
                    field_name=f"EnvironmentTopologyThreadLayoutSeed.activate_on_seed({layout_seed_id})",
                )
                if activate_on_seed:
                    active_layout_count += 1
                layout_key = str(layout_candidate["layout_key"])
                layout_id = _stable_layout_id_from_layout_key(layout_key=layout_key)
                thread_layout_id = stable_thread_layout_id(
                    thread_id=thread_id,
                    layout_id=layout_id,
                )
                thread_layout_ids.append(thread_layout_id)
                planned_layouts.append(
                    {
                        **layout_candidate,
                        "layout_seed_id": layout_seed_id,
                        "layout_id": layout_id,
                        "thread_layout_id": thread_layout_id,
                        "activate_on_seed": activate_on_seed,
                    }
                )
            if active_layout_count > 1:
                raise RuntimeError(
                    "EnvironmentTopologyThreadSeed allows one active layout seed: "
                    f"thread_key={thread_key!r}"
                )

            thread_ids.append(thread_id)
            planned_threads.append(
                {
                    "thread_config_id": thread_config_id,
                    "thread_key": thread_key,
                    "thread_id": thread_id,
                    "title": oig_support.extract_attr_scalar(
                        class_instance=thread_seed_ci,
                        attr_name_by_id=topology_thread_seed_attr_name_by_id,
                        name="title",
                    )
                    or oig_support.extract_attr_scalar(
                        class_instance=thread_ci,
                        attr_name_by_id=thread_attr_name_by_id,
                        name="title",
                    ),
                    "description": oig_support.extract_attr_scalar(
                        class_instance=thread_seed_ci,
                        attr_name_by_id=topology_thread_seed_attr_name_by_id,
                        name="description",
                    )
                    or oig_support.extract_attr_scalar(
                        class_instance=thread_ci,
                        attr_name_by_id=thread_attr_name_by_id,
                        name="description",
                    ),
                    "layouts": planned_layouts,
                }
            )

        process_ids.append(process_id)
        planned_processes.append(
            {
                "process_config_id": process_config_id,
                "process_key": process_key,
                "process_id": process_id,
                "title": oig_support.extract_attr_scalar(
                    class_instance=process_seed_ci,
                    attr_name_by_id=topology_process_seed_attr_name_by_id,
                    name="title",
                )
                or oig_support.extract_attr_scalar(
                    class_instance=process_ci,
                    attr_name_by_id=process_attr_name_by_id,
                    name="title",
                )
                or process_key,
                "description": oig_support.extract_attr_scalar(
                    class_instance=process_seed_ci,
                    attr_name_by_id=topology_process_seed_attr_name_by_id,
                    name="description",
                )
                or oig_support.extract_attr_scalar(
                    class_instance=process_ci,
                    attr_name_by_id=process_attr_name_by_id,
                    name="description",
                ),
                "threads": planned_threads,
            }
        )

    runtime_mounts = _build_environment_experience_runtime_mount_receipts(
        environment_id=environment_id,
        profile_id=profile_id,
        topology_seed_key=topology_seed_key,
        planned_processes=planned_processes,
    )

    if request.validate_only:
        return ProvisionEnvironmentExperienceResponse(
            operation="provision_environment_experience",
            actor_id=request.actor_id,
            environment_id=environment_id,
            process_id=context_process_id,
            thread_id=context_thread_id,
            branch_id=lane_branch_id,
            projection_hash=environment_projection_hash,
            status="succeeded",
            error=None,
            environment_experience_profile_id=profile_id,
            process_ids=_dedupe_ids(process_ids),
            thread_ids=_dedupe_ids(thread_ids),
            thread_layout_ids=_dedupe_ids(thread_layout_ids),
            runtime_mounts=runtime_mounts,
        )

    existing_environment_lane_ids = await lane_support.materialize_lane_instance_ids(
        index=index,
        branch_id=lane_branch_id,
        projection_hash=environment_projection_hash,
    )
    if environment_id not in existing_environment_lane_ids:
        raise RuntimeError(
            "Environment lane is not initialized for provision_environment_experience. "
            "Run ensure_ready first."
        )

    environment_create_profile_fn_id = _try_resolve_public_function_id(
        index=index,
        class_name_suffix="aware_environment_ontology.environment.environment.Environment",
        function_name="create_experience_profile",
    )
    environment_create_process_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix="aware_environment_ontology.environment.environment.Environment",
        function_name="create_process",
    )
    process_create_thread_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix="aware_environment_ontology.process.process.Process",
        function_name="create_thread",
    )
    has_thread_layouts = any(
        bool(thread_plan["layouts"])
        for process_plan in planned_processes
        for thread_plan in process_plan["threads"]
    )
    thread_add_layout_fn_id: UUID | None = None
    thread_set_active_layout_fn_id: UUID | None = None
    if has_thread_layouts:
        thread_add_layout_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="aware_environment_ontology.thread.thread.Thread",
            function_name="add_layout",
        )
        thread_set_active_layout_fn_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="aware_environment_ontology.thread.thread.Thread",
            function_name="set_active_layout",
        )

    if environment_create_profile_fn_id is not None:
        ensure_profile_result = (
            await invoke_support.invoke_instance_environment_function(
                runtime=runtime,
                index=index,
                actor_id=request.actor_id,
                environment_id=environment_id,
                process_id=context_process_id,
                thread_id=context_thread_id,
                branch_id=lane_branch_id,
                projection_hash=environment_projection_hash,
                object_id=environment_id,
                function_id=environment_create_profile_fn_id,
                args=[None, None, None, None],
                commit=True,
            )
        )
        if ensure_profile_result.status != "succeeded":
            if not _is_retired_environment_create_profile_error(
                error=ensure_profile_result.error
            ):
                invoke_support.assert_invoke_succeeded(
                    response=ensure_profile_result,
                    label="Environment.create_experience_profile",
                )

    existing_process_and_thread_ids = set(existing_environment_lane_ids)

    for process_plan in planned_processes:
        process_id = process_plan["process_id"]
        process_key = process_plan["process_key"]
        title = process_plan["title"] or process_key
        description = process_plan["description"]

        if process_id not in existing_process_and_thread_ids:
            create_process_result = (
                await invoke_support.invoke_instance_environment_function(
                    runtime=runtime,
                    index=index,
                    actor_id=request.actor_id,
                    environment_id=environment_id,
                    process_id=context_process_id,
                    thread_id=context_thread_id,
                    branch_id=lane_branch_id,
                    projection_hash=environment_projection_hash,
                    object_id=environment_id,
                    function_id=environment_create_process_fn_id,
                    args=[process_key, title, description],
                    commit=True,
                )
            )
            invoke_support.assert_invoke_succeeded(
                response=create_process_result,
                label=f"Environment.create_process({process_key})",
            )
            existing_process_and_thread_ids.add(process_id)

        for thread_plan in process_plan["threads"]:
            thread_id = thread_plan["thread_id"]
            thread_key = thread_plan["thread_key"]
            if thread_id not in existing_process_and_thread_ids:
                create_thread_result = (
                    await invoke_support.invoke_instance_environment_function(
                        runtime=runtime,
                        index=index,
                        actor_id=request.actor_id,
                        environment_id=environment_id,
                        process_id=context_process_id,
                        thread_id=context_thread_id,
                        branch_id=lane_branch_id,
                        projection_hash=environment_projection_hash,
                        object_id=process_id,
                        function_id=process_create_thread_fn_id,
                        args=[
                            thread_key,
                            thread_plan["title"],
                            thread_plan["description"],
                            False,
                        ],
                        commit=True,
                    )
                )
                invoke_support.assert_invoke_succeeded(
                    response=create_thread_result,
                    label=f"Process.create_thread({thread_key})",
                )
                existing_process_and_thread_ids.add(thread_id)

            for layout_plan in thread_plan["layouts"]:
                layout_key = str(layout_plan["layout_key"])
                layout_id = await _ensure_attention_layout_instance(
                    runtime=runtime,
                    index=index,
                    actor_id=request.actor_id,
                    environment_id=environment_id,
                    process_id=context_process_id,
                    thread_id=context_thread_id,
                    branch_id=lane_branch_id,
                    layout_key=layout_key,
                    title=layout_key,
                    description=cast(str | None, layout_plan["narrative"]),
                )
                if thread_add_layout_fn_id is None:
                    raise RuntimeError(
                        "Thread.add_layout function id is required when thread layouts are planned"
                    )
                add_layout_result = (
                    await invoke_support.invoke_instance_environment_function(
                        runtime=runtime,
                        index=index,
                        actor_id=request.actor_id,
                        environment_id=environment_id,
                        process_id=context_process_id,
                        thread_id=context_thread_id,
                        branch_id=lane_branch_id,
                        projection_hash=environment_projection_hash,
                        object_id=thread_id,
                        function_id=thread_add_layout_fn_id,
                        args=[layout_id, layout_key],
                        commit=True,
                    )
                )
                invoke_support.assert_invoke_succeeded(
                    response=add_layout_result,
                    label=f"Thread.add_layout({thread_key}:{layout_key})",
                )
                if bool(layout_plan["activate_on_seed"]):
                    if thread_set_active_layout_fn_id is None:
                        raise RuntimeError(
                            "Thread.set_active_layout function id is required when default layouts are planned"
                        )
                    set_active_layout_result = (
                        await invoke_support.invoke_instance_environment_function(
                            runtime=runtime,
                            index=index,
                            actor_id=request.actor_id,
                            environment_id=environment_id,
                            process_id=context_process_id,
                            thread_id=context_thread_id,
                            branch_id=lane_branch_id,
                            projection_hash=environment_projection_hash,
                            object_id=thread_id,
                            function_id=thread_set_active_layout_fn_id,
                            args=[layout_id],
                            commit=True,
                        )
                    )
                    invoke_support.assert_invoke_succeeded(
                        response=set_active_layout_result,
                        label=f"Thread.set_active_layout({thread_key}:{layout_key})",
                    )

    materialization_lane = MaterializationLaneContext(
        branch_id=lane_branch_id,
        projection_hash=environment_projection_hash,
    )

    _ = await materialize_experience_compile_plan_actions(
        runtime=runtime,
        index=index,
        actor_id=request.actor_id,
        lane=materialization_lane,
        planned_processes=planned_processes,
    )
    _ = await materialize_experience_compile_plan_projections(
        runtime=runtime,
        index=index,
        actor_id=request.actor_id,
        lane=materialization_lane,
        planned_processes=planned_processes,
    )
    _ = await materialize_experience_compile_plan_connector_configs(
        runtime=runtime,
        index=index,
        actor_id=request.actor_id,
        lane=materialization_lane,
        planned_processes=planned_processes,
    )
    _ = await materialize_experience_compile_plan_graphs(
        runtime=runtime,
        index=index,
        actor_id=request.actor_id,
        lane=materialization_lane,
        planned_processes=planned_processes,
    )
    _ = await materialize_api_compile_plan_ontology(
        runtime=runtime,
        index=index,
        actor_id=request.actor_id,
        lane=materialization_lane,
    )

    return ProvisionEnvironmentExperienceResponse(
        operation="provision_environment_experience",
        actor_id=request.actor_id,
        environment_id=environment_id,
        process_id=context_process_id,
        thread_id=context_thread_id,
        branch_id=lane_branch_id,
        projection_hash=environment_projection_hash,
        status="succeeded",
        error=None,
        environment_experience_profile_id=profile_id,
        process_ids=_dedupe_ids(process_ids),
        thread_ids=_dedupe_ids(thread_ids),
        thread_layout_ids=_dedupe_ids(thread_layout_ids),
        runtime_mounts=runtime_mounts,
    )


async def apply_environment_experience_programs(
    resolver: EnvironmentRuntimeResolverLike,
    request: ApplyEnvironmentExperienceProgramsRequest,
    *,
    submit_program_turn_op: SubmitProgramTurnOperation | None = None,
) -> ApplyEnvironmentExperienceProgramsResponse:
    runtime = await resolver.get_runtime(environment_id=request.environment_id)
    index = runtime.invoker.get_index()

    environment_id = request.environment_id

    boot_process_id = stable_ids.stable_boot_process_id(environment_id=environment_id)
    boot_thread_id = stable_ids.stable_boot_thread_id(environment_id=environment_id)
    boot_branch_id = stable_ids.stable_branch_id(
        environment_id=environment_id, thread_id=boot_thread_id
    )

    lane_branch_id = request.branch_id or boot_branch_id
    context_process_id = request.process_id or boot_process_id
    context_thread_id = request.thread_id or boot_thread_id
    phase = _normalize_required_key(value=request.phase, field_name="phase")
    target_actor_id = (
        request.target_actor_id
        if request.target_actor_id is not None
        else request.actor_id
    )
    if target_actor_id is None:
        raise ValueError(
            "actor_id is required for apply_environment_experience_programs"
        )

    (
        environment_experience_projection_hash,
        env_exp_oig,
        profile_id,
        _profile_source_id,
    ) = await _load_environment_experience_profile_graph(
        index=index,
        lane_branch_id=lane_branch_id,
        requested_profile_id=request.environment_experience_profile_id,
    )
    planned_applies = _build_program_apply_plans(
        index=index,
        env_exp_oig=env_exp_oig,
        profile_id=profile_id,
        environment_id=environment_id,
        phase=phase,
    )
    receipts: list[EnvironmentExperienceProgramApplyReceipt] = []

    if request.validate_only:
        for apply_plan in planned_applies:
            receipts.append(
                EnvironmentExperienceProgramApplyReceipt(
                    key=str(apply_plan["key"]),
                    phase=str(apply_plan["phase"]),
                    program_ref=str(apply_plan["program_ref"]),
                    position=_coerce_optional_int(
                        value=apply_plan["position"],
                        field_name=f"EnvironmentExperienceProgramApply.position({apply_plan['key']})",
                    ),
                    status="planned",
                    error=None,
                    program_run_id=None,
                    turn_id=None,
                    deduped=False,
                    resolved_branch_id=None,
                    resolved_projection_hash=None,
                    lane_resolution_source=None,
                )
            )
        return ApplyEnvironmentExperienceProgramsResponse(
            operation="apply_environment_experience_programs",
            actor_id=request.actor_id,
            environment_id=environment_id,
            process_id=context_process_id,
            thread_id=context_thread_id,
            branch_id=lane_branch_id,
            projection_hash=environment_experience_projection_hash,
            status="succeeded",
            error=None,
            environment_experience_profile_id=profile_id,
            phase=phase,
            target_actor_id=target_actor_id,
            receipts=receipts,
        )

    from aware_experience.program.operations import run_program as run_program_op

    response_status = "succeeded"
    response_error: str | None = None
    for apply_plan in planned_applies:
        apply_key = str(apply_plan["key"])
        apply_phase = str(apply_plan["phase"])
        apply_program_ref = str(apply_plan["program_ref"])
        apply_position = _coerce_optional_int(
            value=apply_plan["position"],
            field_name=f"EnvironmentExperienceProgramApply.position({apply_key})",
        )
        raw_symbols = _normalize_json_object_mapping(
            value=apply_plan["symbols"],
            field_name=f"EnvironmentExperienceProgramApply.symbols({apply_key})",
        )
        symbols = JsonObject()
        for symbol_key, symbol_value in raw_symbols.items():
            coerced_symbol_value = (
                symbol_value
                if isinstance(
                    symbol_value, (type(None), bool, int, float, str, list, dict)
                )
                else str(symbol_value)
            )
            symbols[symbol_key] = cast(JsonValue, coerced_symbol_value)
        symbols["plan.program_config_id"] = str(apply_plan["program_config_id"])
        symbols["plan.environment_experience_profile_id"] = str(profile_id)
        symbols["plan.environment_experience_program_apply_key"] = apply_key
        symbols["plan.environment_experience_program_apply_phase"] = apply_phase
        if apply_position is not None:
            symbols["plan.environment_experience_program_apply_position"] = (
                apply_position
            )

        run_request = RunProgramRequest(
            actor_id=request.actor_id,
            environment_id=environment_id,
            process_id=context_process_id,
            thread_id=context_thread_id,
            branch_id=None,
            projection_hash=None,
            target_actor_id=target_actor_id,
            program_ref=apply_program_ref,
            symbols=symbols,
            message=str(apply_plan["message"] or ""),
            turn_index=1,
            mailbox_key=None,
            idempotency_key=(
                "environment_experience_profile:"
                + f"{profile_id}:program_apply:{apply_key}:phase:{apply_phase.casefold()}"
            ),
            max_attempts=1,
            wait_for_terminal=True,
        )
        try:
            run_response = await run_program_op(
                resolver=resolver,
                request=run_request,
                submit_program_turn_op=submit_program_turn_op,
            )
        except Exception as exc:  # noqa: BLE001
            error_text = str(exc) or f"run_program failed for apply {apply_key!r}"
            receipts.append(
                EnvironmentExperienceProgramApplyReceipt(
                    key=apply_key,
                    phase=apply_phase,
                    program_ref=apply_program_ref,
                    position=apply_position,
                    status="failed",
                    error=error_text,
                    program_run_id=None,
                    turn_id=None,
                    deduped=False,
                    resolved_branch_id=None,
                    resolved_projection_hash=None,
                    lane_resolution_source=None,
                )
            )
            response_status = "failed"
            response_error = error_text
            break

        receipts.append(
            EnvironmentExperienceProgramApplyReceipt(
                key=apply_key,
                phase=apply_phase,
                program_ref=apply_program_ref,
                position=apply_position,
                status=str(getattr(run_response, "status", "")),
                error=getattr(run_response, "error", None),
                program_run_id=getattr(run_response, "program_run_id", None),
                turn_id=getattr(run_response, "turn_id", None),
                deduped=bool(getattr(run_response, "deduped", False)),
                resolved_branch_id=getattr(run_response, "resolved_branch_id", None),
                resolved_projection_hash=getattr(
                    run_response, "resolved_projection_hash", None
                ),
                lane_resolution_source=getattr(
                    run_response, "lane_resolution_source", None
                ),
            )
        )
        if (
            str(getattr(run_response, "status", "") or "").strip().casefold()
            != "succeeded"
        ):
            response_status = "failed"
            response_error = str(
                getattr(run_response, "error", None) or ""
            ).strip() or (
                "apply_environment_experience_programs failed for "
                + f"key={apply_key!r}"
            )
            break

    return ApplyEnvironmentExperienceProgramsResponse(
        operation="apply_environment_experience_programs",
        actor_id=request.actor_id,
        environment_id=environment_id,
        process_id=context_process_id,
        thread_id=context_thread_id,
        branch_id=lane_branch_id,
        projection_hash=environment_experience_projection_hash,
        status=response_status,
        error=response_error,
        environment_experience_profile_id=profile_id,
        phase=phase,
        target_actor_id=target_actor_id,
        receipts=receipts,
    )
