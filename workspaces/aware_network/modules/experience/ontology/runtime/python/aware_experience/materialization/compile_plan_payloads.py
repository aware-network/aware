from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import tomllib
from typing import Any, ClassVar, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictStr, ValidationError, field_validator

from aware_experience.action.compiler import (
    load_action_ownership_from_sources,
    load_dependency_action_ownership_from_snapshot,
)
from aware_experience.actor.compiler import load_actor_role_ownership_from_sources
from aware_experience.compiler.builder import (
    publish_environment_profile_actor_role_ownership,
)
from aware_experience.compiler.models import (
    ExperienceActionOwnership,
    ExperienceConnectorConfigOwnership,
    ExperienceConnectorInvocationActionConfigOwnership,
    ExperienceEnvironmentOwnership,
    ExperienceEnvironmentProfileOwnership,
    ExperienceGraphOwnership,
    ExperienceProjectionExperienceOwnership,
    ExperienceViewApiOwnership,
    ExperienceViewApiViewOwnership,
    ExperienceViewStateModelContract,
)
from aware_experience.connector.compiler import (
    load_connector_ownership_from_sources,
    load_dependency_connector_ownership_from_snapshot,
)
from aware_experience.environment.compiler import (
    load_environment_ownership_from_sources,
)
from aware_experience.environment_profile.compiler import (
    load_environment_profile_ownership_from_sources,
)
from aware_experience.event.compiler import (
    load_dependency_event_ownership_from_snapshot,
    load_event_ownership_from_sources,
)
from aware_experience.graph.compiler import load_graph_ownership_from_sources
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
from aware_experience.view_api import build_experience_view_api_ownership
from aware_experience.view_contracts import (
    load_view_state_model_contracts_from_sources,
)


class _ActorMaterializationStepPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    actor_name: StrictStr
    actor_kind: StrictStr
    role_keys: tuple[StrictStr, ...] = ()

    @field_validator("actor_name", "actor_kind", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("role_keys", mode="before")
    @classmethod
    def _validate_role_keys(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("role_keys must be a list")
        value_items = cast(Sequence[object], value)
        return tuple(_required_step_payload_token(item) for item in value_items)


class _CompileRoleOwnershipRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    name: StrictStr

    @field_validator("name", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _CompileActorOwnershipRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    name: StrictStr
    kind: StrictStr
    roles: tuple[StrictStr, ...] = ()

    @field_validator("name", "kind", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("roles", mode="before")
    @classmethod
    def _validate_roles(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("roles must be a list")
        value_items = cast(Sequence[object], value)
        return tuple(_required_step_payload_token(item) for item in value_items)


class _CompileEnvironmentActorBindingRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    actor: StrictStr
    roles: tuple[StrictStr, ...] = ()

    @field_validator("actor", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("roles", mode="before")
    @classmethod
    def _validate_roles(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("roles must be a list")
        value_items = cast(Sequence[object], value)
        return tuple(_required_step_payload_token(item) for item in value_items)


class _ConnectorInvocationRequestFieldPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    attribute: StrictStr
    source_ref: StrictStr
    required: bool = True

    @field_validator("attribute", "source_ref", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _ConnectorInvocationActionConfigPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    action_key: StrictStr
    action_kind: StrictStr
    target_ref: StrictStr
    materialized_action_key: StrictStr
    source_path: StrictStr
    label: StrictStr | None = None
    receipt_policy: StrictStr | None = None
    confirmation_policy: StrictStr | None = None
    optimistic_policy: StrictStr | None = None
    request_fields: tuple[_ConnectorInvocationRequestFieldPayload, ...] = ()

    @field_validator(
        "action_key",
        "target_ref",
        "materialized_action_key",
        "source_path",
        mode="before",
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("action_kind", mode="before")
    @classmethod
    def _validate_action_kind(cls, value: object) -> str:
        action_kind = _required_step_payload_token(value)
        if action_kind not in {"sdk", "api"}:
            raise ValueError("action_kind must be sdk or api")
        return action_kind


class _ConnectorProviderMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    provider_key: StrictStr
    provider_kind: StrictStr
    source_path: StrictStr
    provider_ref: StrictStr | None = None
    label: StrictStr | None = None
    description: StrictStr | None = None

    @field_validator("provider_key", "provider_kind", "source_path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _SensorConfigMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    sensor_key: StrictStr
    sensor_kind: StrictStr
    source_path: StrictStr
    source_ref: StrictStr | None = None
    observed_state_node_refs: tuple[StrictStr, ...] = ()
    label: StrictStr | None = None
    description: StrictStr | None = None
    invocation_action_configs: tuple[_ConnectorInvocationActionConfigPayload, ...] = ()

    @field_validator("sensor_key", "sensor_kind", "source_path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("observed_state_node_refs", mode="before")
    @classmethod
    def _validate_state_node_refs(cls, value: object) -> tuple[str, ...]:
        return _validate_state_node_ref_tuple(value=value)


class _ActuatorConfigMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    actuator_key: StrictStr
    actuator_kind: StrictStr
    source_path: StrictStr
    target_ref: StrictStr | None = None
    affected_state_node_refs: tuple[StrictStr, ...] = ()
    label: StrictStr | None = None
    description: StrictStr | None = None
    invocation_action_configs: tuple[_ConnectorInvocationActionConfigPayload, ...] = ()

    @field_validator("actuator_key", "actuator_kind", "source_path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("affected_state_node_refs", mode="before")
    @classmethod
    def _validate_state_node_refs(cls, value: object) -> tuple[str, ...]:
        return _validate_state_node_ref_tuple(value=value)


class _ConnectorConfigMaterializationStepPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    connector_key: StrictStr
    connector_kind: StrictStr
    source_path: StrictStr
    projection_experience_name: StrictStr
    projection_key: StrictStr
    label: StrictStr | None = None
    description: StrictStr | None = None
    providers: tuple[_ConnectorProviderMaterializationPayload, ...] = ()
    sensor_configs: tuple[_SensorConfigMaterializationPayload, ...] = ()
    actuator_configs: tuple[_ActuatorConfigMaterializationPayload, ...] = ()

    @field_validator(
        "connector_key",
        "connector_kind",
        "source_path",
        "projection_experience_name",
        "projection_key",
        mode="before",
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _ProjectionMaterializationViewInvocationActionPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    key: StrictStr
    api_view_capability_endpoint_id: UUID | None = None
    endpoint_ref: StrictStr
    api_capability_endpoint_id: UUID
    sdk_operation_api_view_capability_endpoint_id: UUID | None = None
    sdk_operation_id: UUID | None = None
    source_path: StrictStr
    label: StrictStr | None = None
    receipt_policy: StrictStr | None = None
    confirmation_policy: StrictStr | None = None
    optimistic_policy: StrictStr | None = None

    @field_validator("key", "endpoint_ref", "source_path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator(
        "label",
        "receipt_policy",
        "confirmation_policy",
        "optimistic_policy",
        mode="before",
    )
    @classmethod
    def _validate_optional_token(cls, value: object) -> str | None:
        if value is None:
            return None
        token = str(value).strip()
        return token or None


class _ProjectionMaterializationViewPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    observable_key: StrictStr
    view_key: StrictStr
    api_name: StrictStr
    api_view_name: StrictStr
    api_view_ref: StrictStr
    state_model_ref: StrictStr | None = None
    state_provider_ref: StrictStr | None = None
    invocation_actions: tuple[
        _ProjectionMaterializationViewInvocationActionPayload, ...
    ] = ()

    @field_validator(
        "observable_key",
        "view_key",
        "api_name",
        "api_view_name",
        "api_view_ref",
        mode="before",
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("state_model_ref", "state_provider_ref", mode="before")
    @classmethod
    def _validate_optional_token(cls, value: object) -> str | None:
        if value is None:
            return None
        token = str(value).strip()
        return token or None


class _ProjectionMaterializationNodePayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name: StrictStr
    node_ref: StrictStr
    identity_keys: tuple[StrictStr, ...]

    @field_validator("name", "node_ref", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("identity_keys", mode="before")
    @classmethod
    def _validate_identity_keys(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("identity_keys must be a list")
        value_items = cast(Sequence[object], value)
        normalized_keys = tuple(
            _required_step_payload_token(item) for item in value_items
        )
        if not normalized_keys:
            raise ValueError("identity_keys requires at least one entry")
        return normalized_keys


class _ProjectionMaterializationStepPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    experience_name: StrictStr
    projection_key: StrictStr
    runtime_opgi_id: UUID | None = None
    branches: tuple[StrictStr, ...] = ()
    views: tuple[_ProjectionMaterializationViewPayload, ...] = ()
    nodes: tuple[_ProjectionMaterializationNodePayload, ...] = ()

    @field_validator("experience_name", "projection_key", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("branches", mode="before")
    @classmethod
    def _validate_branches(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("branches must be a list")
        value_items = cast(Sequence[object], value)
        return tuple(_required_step_payload_token(item) for item in value_items)


class _ProjectionSectionSurfaceBindingPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    surface_key: StrictStr
    section_key: StrictStr
    observable_key: StrictStr
    view_key: StrictStr
    source_path: StrictStr
    layout_config_section_config_id: UUID | None = None
    source_surface_key: StrictStr | None = None
    graph_identity_ref: StrictStr | None = None
    node_identity_ref: StrictStr | None = None

    @field_validator(
        "surface_key",
        "section_key",
        "observable_key",
        "view_key",
        "source_path",
        mode="before",
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _ProjectionLayoutGraphBindingPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    layout_config_id: UUID
    binding_key: StrictStr
    section_graph_binding_keys: tuple[StrictStr, ...] = ()

    @field_validator("binding_key", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("section_graph_binding_keys", mode="before")
    @classmethod
    def _validate_section_graph_binding_keys(
        cls, value: object
    ) -> tuple[str, ...] | object:
        if not isinstance(value, (list, tuple)):
            raise ValueError("section_graph_binding_keys must be a list")
        value_items = cast(Sequence[object], value)
        return tuple(_required_step_payload_token(item) for item in value_items)


class _ProjectionSectionSurfaceMaterializationStepPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    experience_name: StrictStr
    projection_key: StrictStr
    runtime_opgi_id: UUID | None = None
    layout_bindings: tuple[_ProjectionLayoutGraphBindingPayload, ...] = ()
    surfaces: tuple[_ProjectionSectionSurfaceBindingPayload, ...] = ()

    @field_validator("experience_name", "projection_key", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator("surfaces", mode="before")
    @classmethod
    def _validate_surfaces(
        cls, value: object
    ) -> tuple[_ProjectionSectionSurfaceBindingPayload, ...] | object:
        if not isinstance(value, (list, tuple)):
            raise ValueError("surfaces must be a list")
        return value

    @field_validator("layout_bindings", mode="before")
    @classmethod
    def _validate_layout_bindings(
        cls, value: object
    ) -> tuple[_ProjectionLayoutGraphBindingPayload, ...] | object:
        if not isinstance(value, (list, tuple)):
            raise ValueError("layout_bindings must be a list")
        return value


class _EnvironmentProfileThreadProjectionMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    projection_experience_name: StrictStr
    projection_key: StrictStr
    source_path: StrictStr
    view_key: StrictStr | None = None
    position: int | None = None
    is_default: bool = False
    narrative: StrictStr | None = None
    intent: StrictStr | None = None

    @field_validator(
        "projection_experience_name", "projection_key", "source_path", mode="before"
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _EnvironmentProfileThreadLayoutSectionMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    section_key: StrictStr
    projection_experience_name: StrictStr
    projection_key: StrictStr
    view_key: StrictStr
    source_path: StrictStr
    key: StrictStr | None = None
    section_graph_binding_key: StrictStr | None = None
    position: int | None = None
    is_default: bool = False
    narrative: StrictStr | None = None
    intent: StrictStr | None = None

    @field_validator(
        "section_key",
        "projection_experience_name",
        "projection_key",
        "view_key",
        "source_path",
        mode="before",
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _EnvironmentProfileThreadLayoutMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    layout_key: StrictStr
    layout_config_id: UUID | None = None
    source_path: StrictStr
    key: StrictStr | None = None
    position: int | None = None
    is_default: bool = False
    narrative: StrictStr | None = None
    intent: StrictStr | None = None
    sections: tuple[
        _EnvironmentProfileThreadLayoutSectionMaterializationPayload, ...
    ] = ()

    @field_validator("layout_key", "source_path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _EnvironmentProfileThreadMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    key: StrictStr
    thread_key: StrictStr
    source_path: StrictStr
    title: StrictStr | None = None
    description: StrictStr | None = None
    workspace_view_key: StrictStr | None = None
    position: int | None = None
    is_default: bool = False
    narrative: StrictStr | None = None
    intent: StrictStr | None = None
    state_prompt_template: StrictStr | None = None
    projection_experiences: tuple[
        _EnvironmentProfileThreadProjectionMaterializationPayload, ...
    ] = ()
    layout_configs: tuple[
        _EnvironmentProfileThreadLayoutMaterializationPayload, ...
    ] = ()

    @field_validator("key", "thread_key", "source_path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _EnvironmentProfileProcessMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    type: StrictStr
    key: StrictStr
    process_key: StrictStr
    source_path: StrictStr
    title: StrictStr | None = None
    description: StrictStr | None = None
    shape: StrictStr | None = None
    position: int | None = None
    is_bootstrap_default: bool = False
    narrative: StrictStr | None = None
    intent: StrictStr | None = None
    thread_configs: tuple[_EnvironmentProfileThreadMaterializationPayload, ...] = ()

    @field_validator("type", "key", "process_key", "source_path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _EnvironmentProfileViewEventTransitionMaterializationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    key: StrictStr
    source_projection_experience_name: StrictStr
    source_view_key: StrictStr
    trigger_event_config_ref: StrictStr
    target_projection_experience_name: StrictStr
    target_section_graph_binding_key: StrictStr
    source_path: StrictStr
    name: StrictStr | None = None
    rationale: StrictStr | None = None
    idempotency_policy: StrictStr | None = None

    @field_validator(
        "key",
        "source_projection_experience_name",
        "source_view_key",
        "trigger_event_config_ref",
        "target_projection_experience_name",
        "target_section_graph_binding_key",
        "source_path",
        mode="before",
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _EnvironmentProfileMaterializationStepPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    fqn_prefix: StrictStr
    experience_name: StrictStr
    key: StrictStr
    source_path: StrictStr
    title: StrictStr | None = None
    description: StrictStr | None = None
    narrative: StrictStr | None = None
    process_configs: tuple[_EnvironmentProfileProcessMaterializationPayload, ...] = ()
    view_event_transitions: tuple[
        _EnvironmentProfileViewEventTransitionMaterializationPayload, ...
    ] = ()

    @field_validator(
        "fqn_prefix", "experience_name", "key", "source_path", mode="before"
    )
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)


class _ProgramMaterializationStepPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    ref: StrictStr
    name: StrictStr
    path: StrictStr
    dependencies: tuple[StrictStr, ...] = ()
    required_symbols: tuple[StrictStr, ...] = ()
    optional_symbols: tuple[StrictStr, ...] = ()
    invocation_plan_artifact: dict[str, object]
    program_config_plan_artifact: dict[str, object] | None = None
    program_apply_calls_artifact: dict[str, object] | None = None

    @field_validator("ref", "name", "path", mode="before")
    @classmethod
    def _validate_required_token(cls, value: object) -> str:
        return _required_step_payload_token(value)

    @field_validator(
        "dependencies",
        "required_symbols",
        "optional_symbols",
        mode="before",
    )
    @classmethod
    def _validate_string_list(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, (list, tuple)):
            raise ValueError("value must be a list")
        value_items = cast(Sequence[object], value)
        return tuple(_required_step_payload_token(item) for item in value_items)

    @field_validator(
        "invocation_plan_artifact",
        "program_config_plan_artifact",
        "program_apply_calls_artifact",
        mode="before",
    )
    @classmethod
    def _validate_optional_mapping(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise ValueError("artifact must be an object")
        return dict(cast(Mapping[str, object], value))


def load_experience_compile_plan_payloads(
    *, repo_root: Path
) -> list[dict[str, object]]:
    runtime_root = (repo_root / ".aware" / "experience" / "runtime").resolve()
    if not runtime_root.exists() or not runtime_root.is_dir():
        return []

    payloads: list[dict[str, object]] = []
    for compile_plan_path in sorted(
        runtime_root.glob("*/experience.compile_plan.json")
    ):
        if not compile_plan_path.is_file():
            continue
        try:
            payload_obj = cast(
                object,
                json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}"),
            )
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise RuntimeError(
                f"Invalid experience compile plan at {compile_plan_path}: {exc}"
            ) from exc
        payload_map = _expect_mapping(
            payload_obj, field_name=f"{compile_plan_path}:root"
        )
        payloads.append(dict(payload_map))
    return payloads


def load_api_compile_plan_payloads_for_workspace(
    *, workspace_root: Path
) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for root in _declared_workspace_dependency_roots(workspace_root=workspace_root):
        payloads.extend(_load_api_compile_plan_payloads_from_root(repo_root=root))
    return payloads


def _declared_workspace_dependency_roots(*, workspace_root: Path) -> tuple[Path, ...]:
    resolved_workspace_root = workspace_root.resolve()
    roots: list[Path] = [resolved_workspace_root]
    workspace_toml_path = resolved_workspace_root / "aware.workspace.toml"
    if not workspace_toml_path.is_file():
        return tuple(roots)
    payload = tomllib.loads(workspace_toml_path.read_text(encoding="utf-8"))
    workspace_payload = payload.get("workspace")
    if not isinstance(workspace_payload, Mapping):
        return tuple(roots)
    dependencies = workspace_payload.get("dependencies", ())
    if not isinstance(dependencies, Sequence) or isinstance(dependencies, (str, bytes)):
        return tuple(roots)
    for dependency in dependencies:
        if not isinstance(dependency, Mapping):
            continue
        source = str(dependency.get("source") or "").strip()
        if not source.startswith("workspace://"):
            continue
        dependency_handle = source.removeprefix("workspace://").split("#", 1)[0]
        if not dependency_handle:
            continue
        dependency_root = (resolved_workspace_root.parent / dependency_handle).resolve()
        if dependency_root.is_dir() and dependency_root not in roots:
            roots.append(dependency_root)
    return tuple(roots)


def _load_api_compile_plan_payloads_from_root(
    *, repo_root: Path
) -> list[dict[str, object]]:
    runtime_root = (repo_root / ".aware" / "api" / "runtime").resolve()
    if not runtime_root.exists() or not runtime_root.is_dir():
        return []

    payloads: list[dict[str, object]] = []
    for compile_plan_path in sorted(runtime_root.glob("*/api.compile_plan.json")):
        if not compile_plan_path.is_file():
            continue
        try:
            payload_obj = cast(
                object,
                json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}"),
            )
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise RuntimeError(
                f"Invalid api compile plan at {compile_plan_path}: {exc}"
            ) from exc
        payload_map = _expect_mapping(
            payload_obj, field_name=f"{compile_plan_path}:root"
        )
        payloads.append(dict(payload_map))
    return payloads


def _build_source_experience_compile_plan_payload(
    *,
    snapshot: Any,
) -> dict[str, object]:
    projection_experience_ownership = load_projection_experience_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    view_state_model_contracts = load_view_state_model_contracts_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip(),
        package_name=(snapshot.spec.experience.package_name or "").strip(),
    )
    graph_ownership: tuple[ExperienceGraphOwnership, ...] = ()
    if projection_experience_ownership:
        graph_ownership = load_graph_ownership_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
            projection_experience_ownership=projection_experience_ownership,
        )
    program_ownership = load_program_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=select_program_source_files(snapshot.source_files),
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip(),
        projection_experience_ownership=projection_experience_ownership,
    )
    action_ownership = load_action_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        package_name=(snapshot.spec.experience.package_name or "").strip() or None,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip() or None,
    ) + load_dependency_action_ownership_from_snapshot(snapshot=snapshot)
    connector_ownership = load_connector_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        package_name=(snapshot.spec.experience.package_name or "").strip() or None,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip() or None,
    )
    action_target_ownership = load_dependency_connector_ownership_from_snapshot(
        snapshot=snapshot
    )
    event_ownership = load_event_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        package_name=(snapshot.spec.experience.package_name or "").strip() or None,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip() or None,
    ) + load_dependency_event_ownership_from_snapshot(snapshot=snapshot)
    environment_profile_ownership = load_environment_profile_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        projection_experience_ownership=projection_experience_ownership,
        event_ownership=event_ownership,
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
    environment_profile_ownership = publish_environment_profile_actor_role_ownership(
        environment_profile_ownership=environment_profile_ownership,
        role_ownership=role_ownership,
        actor_ownership=actor_ownership,
        environment_actor_bindings=environment_actor_bindings,
        environment_ownership=environment_ownership,
    )
    package_name = (snapshot.spec.experience.package_name or "").strip()
    fqn_prefix = (snapshot.spec.experience.fqn_prefix or "").strip()
    view_api_ownership = build_experience_view_api_ownership(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        projection_experience_ownership=projection_experience_ownership,
        view_state_model_contracts=tuple(
            ExperienceViewStateModelContract(
                state_model_ref=contract.state_model_ref,
                class_config_id=contract.class_config_id,
                source_path=contract.source_path,
            )
            for contract in view_state_model_contracts
        ),
    )

    return {
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "environment_handle": (snapshot.spec.build.environment_handle or "").strip(),
        "source_files": [path.as_posix() for path in snapshot.source_files],
        "view_state_model_contracts": [
            {
                "state_model_ref": contract.state_model_ref,
                "class_config_id": str(contract.class_config_id),
                "source_path": contract.source_path,
            }
            for contract in view_state_model_contracts
        ],
        "projection_experience_ownership": _encode_projection_experience_ownership_rows(
            ownerships=projection_experience_ownership,
        ),
        "view_api_ownership": (
            _encode_view_api_ownership_payload(view_api=view_api_ownership)
            if view_api_ownership is not None
            else None
        ),
        "connector_ownership": _encode_connector_ownership_rows(
            ownerships=connector_ownership,
        ),
        "action_target_ownership": _encode_connector_ownership_rows(
            ownerships=action_target_ownership,
        ),
        "action_ownership": _encode_action_ownership_rows(
            ownerships=action_ownership,
        ),
        "environment_ownership": _encode_environment_ownership_rows(
            ownerships=environment_ownership,
        ),
        "graph_ontology": encode_graph_ontology_plan_payload(
            plans=build_graph_ontology_plans(
                projection_experience_ownership=projection_experience_ownership,
                graph_ownership=graph_ownership,
            )
        ),
        "environment_profile_ownership": _encode_environment_profile_ownership_rows(
            ownerships=environment_profile_ownership,
        ),
        "program_ownership": [
            {
                "ref": item.ref,
                "name": item.name,
                "path": item.path,
                "dependencies": list(item.dependencies),
                "required_symbols": list(item.required_symbols),
                "optional_symbols": list(item.optional_symbols),
                "required_projection_ids": list(item.required_projection_ids),
                "required_projection_node_ids": list(item.required_projection_node_ids),
                "required_projection_node_identity_ids": list(
                    item.required_projection_node_identity_ids
                ),
                "invocation_plan_artifact": (
                    dict(item.invocation_plan_artifact)
                    if item.invocation_plan_artifact is not None
                    else None
                ),
                "program_config_plan_artifact": (
                    dict(item.program_config_plan_artifact)
                    if item.program_config_plan_artifact is not None
                    else None
                ),
                "program_apply_calls_artifact": (
                    dict(item.program_apply_calls_artifact)
                    if item.program_apply_calls_artifact is not None
                    else None
                ),
            }
            for item in program_ownership
        ],
    }


def _encode_view_api_ownership_payload(
    *,
    view_api: ExperienceViewApiOwnership,
) -> dict[str, object]:
    return {
        "package_name": view_api.package_name,
        "fqn_prefix": view_api.fqn_prefix,
        "api_name": view_api.api_name,
        "source_path": view_api.source_path,
        "views": [_encode_view_api_view_payload(view=view) for view in view_api.views],
    }


def _encode_view_api_view_payload(
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
        "is_default": view.is_default,
        "source_path": view.source_path,
    }


def _encode_projection_experience_ownership_rows(
    *,
    ownerships: Sequence[ExperienceProjectionExperienceOwnership],
) -> list[dict[str, object]]:
    return [
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
        for item in ownerships
    ]


def _encode_connector_ownership_rows(
    *,
    ownerships: Sequence[ExperienceConnectorConfigOwnership],
) -> list[dict[str, object]]:
    return [
        {
            "connector_key": item.connector_key,
            "connector_kind": item.connector_kind,
            "source_path": item.source_path,
            "package_name": item.package_name,
            "fqn_prefix": item.fqn_prefix,
            "is_dependency": item.is_dependency,
            "label": item.label,
            "description": item.description,
            "providers": [
                {
                    "provider_key": provider.provider_key,
                    "provider_kind": provider.provider_kind,
                    "source_path": provider.source_path,
                    "provider_ref": provider.provider_ref,
                    "label": provider.label,
                    "description": provider.description,
                }
                for provider in item.providers
            ],
            "sensor_configs": [
                {
                    "sensor_key": sensor.sensor_key,
                    "sensor_kind": sensor.sensor_kind,
                    "source_path": sensor.source_path,
                    "source_ref": sensor.source_ref,
                    "observed_state_node_refs": list(sensor.observed_state_node_refs),
                    "label": sensor.label,
                    "description": sensor.description,
                    "invocation_action_configs": [
                        _encode_connector_invocation_action_config(
                            invocation=invocation
                        )
                        for invocation in sensor.invocation_action_configs
                    ],
                }
                for sensor in item.sensor_configs
            ],
            "actuator_configs": [
                {
                    "actuator_key": actuator.actuator_key,
                    "actuator_kind": actuator.actuator_kind,
                    "source_path": actuator.source_path,
                    "target_ref": actuator.target_ref,
                    "affected_state_node_refs": list(actuator.affected_state_node_refs),
                    "label": actuator.label,
                    "description": actuator.description,
                    "invocation_action_configs": [
                        _encode_connector_invocation_action_config(
                            invocation=invocation
                        )
                        for invocation in actuator.invocation_action_configs
                    ],
                }
                for actuator in item.actuator_configs
            ],
        }
        for item in ownerships
    ]


def _encode_connector_invocation_action_config(
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
        "request_fields": [
            {
                "attribute": field.attribute,
                "source_ref": field.source_ref,
                "required": field.required,
            }
            for field in invocation.request_fields
        ],
    }


def _encode_action_ownership_rows(
    *,
    ownerships: Sequence[ExperienceActionOwnership],
) -> list[dict[str, object]]:
    return [
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
        for item in ownerships
    ]


def _encode_environment_ownership_rows(
    *,
    ownerships: Sequence[ExperienceEnvironmentOwnership],
) -> list[dict[str, object]]:
    return [
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
                    "actions": [{"action": action.action} for action in event.actions],
                }
                for event in item.events
            ],
        }
        for item in ownerships
    ]


def _encode_environment_profile_ownership_rows(
    *,
    ownerships: Sequence[ExperienceEnvironmentProfileOwnership],
) -> list[dict[str, object]]:
    return [
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
                                    "projection_experience_name": (
                                        projection.projection_experience_name
                                    ),
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
                                            "projection_experience_name": (
                                                section.projection_experience_name
                                            ),
                                            "view_key": section.view_key,
                                            "source_path": section.source_path,
                                            "key": section.key,
                                            "section_graph_binding_key": (
                                                section.section_graph_binding_key
                                            ),
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
        for item in ownerships
    ]


def _dependency_projection_experience_prefixes(
    *,
    snapshot: Any,
) -> tuple[str, ...]:
    prefixes: set[str] = set()
    for dependency in (
        getattr(getattr(snapshot, "spec", None), "dependencies", ()) or ()
    ):
        package_name = (getattr(dependency, "package_name", None) or "").strip()
        if not package_name:
            continue
        prefixes.add(package_name)
        prefixes.add(package_name.replace("-", "_"))
        prefixes.add(package_name.replace("-", "."))
    return tuple(sorted(prefixes, key=str.casefold))


def _expect_list(value: object, *, field_name: str) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    raise RuntimeError(f"Invalid experience compile plan: {field_name} must be a list")


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise RuntimeError(
        f"Invalid experience compile plan: {field_name} must be an object"
    )


def _expect_nonempty_text(value: object, *, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise RuntimeError(
        f"Invalid experience compile plan: {field_name} must be a non-empty string"
    )


def _required_step_payload_token(value: object) -> str:
    if isinstance(value, str):
        token = value.strip()
        if token:
            return token
    raise ValueError("value is required")


def _optional_payload_token(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _validate_state_node_ref_tuple(*, value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError("state-node refs must be a list")
    value_items = cast(Sequence[object], value)
    refs: list[str] = []
    seen: set[str] = set()
    for item in value_items:
        ref = _required_step_payload_token(item)
        ref_key = ref.casefold()
        if ref_key in seen:
            raise ValueError(f"duplicate state-node ref {ref!r}")
        seen.add(ref_key)
        refs.append(ref)
    return tuple(refs)


def _state_node_refs_from_payload(
    value: object,
    *,
    field_name: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    try:
        return _validate_state_node_ref_tuple(value=value)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid experience compile plan: {field_name} {exc}"
        ) from exc


def _format_step_payload_validation_error(
    *, exc: ValidationError, prefix: str = "projection"
) -> str:
    first_error = exc.errors()[0] if exc.errors() else None
    if first_error is None:
        return f"Invalid experience compile plan: {prefix} materialization step payload is invalid"
    path = ".".join(str(item) for item in first_error.get("loc", ()))
    message = str(first_error.get("msg") or "invalid value")
    return f"Invalid experience compile plan: {prefix} materialization payload {path} {message}"


def _format_compile_payload_validation_error(*, exc: ValidationError, path: str) -> str:
    first_error = exc.errors()[0] if exc.errors() else None
    if first_error is None:
        return f"Invalid experience compile plan: {path} payload is invalid"
    row_path = ".".join(str(item) for item in first_error.get("loc", ()))
    message = str(first_error.get("msg") or "invalid value")
    return f"Invalid experience compile plan: {path}.{row_path} {message}"
