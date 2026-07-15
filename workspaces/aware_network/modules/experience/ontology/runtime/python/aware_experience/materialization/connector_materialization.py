from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast
from uuid import UUID

from pydantic import ValidationError

from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
)
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.environment_profile.runtime_support import ocg_support
from aware_experience.graph.materialization.service import (
    ProjectionExperienceNodeMaterializationSpec,
    build_projection_node_snapshots_for_materialization,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.compile_plan_payloads import (
    _ActuatorConfigMaterializationPayload,
    _ConnectorConfigMaterializationStepPayload,
    _ConnectorInvocationActionConfigPayload,
    _ConnectorInvocationRequestFieldPayload,
    _ConnectorProviderMaterializationPayload,
    _SensorConfigMaterializationPayload,
    _expect_list,
    _expect_mapping,
    _format_step_payload_validation_error,
    _optional_payload_token,
    _required_step_payload_token,
    _state_node_refs_from_payload,
    load_experience_compile_plan_payloads,
)
from aware_experience.program.registry_index import find_repo_root
from aware_experience_ontology.actuator.actuator_invocation_action_config import (
    ActuatorInvocationActionConfig,
)
from aware_experience_ontology.connector.connector_config import ConnectorConfig
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.sensor.sensor_invocation_action_config import (
    SensorInvocationActionConfig,
)
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_sdk_ontology.stable_ids import stable_sdk_config_id, stable_sdk_operation_id


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


class ResolveProjectionOpgiId(Protocol):
    def __call__(
        self,
        *,
        opgi_by_key_casefolded: Mapping[str, tuple[UUID, set[str] | frozenset[str]]],
        projection_key: str,
        experience_name: str,
        runtime_opgi_id: UUID | None = None,
    ) -> UUID: ...


class FindProjectionGraphByOpgiId(Protocol):
    def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        object_projection_graph_identity_id: UUID,
    ) -> ObjectProjectionGraph: ...


@dataclass(frozen=True, slots=True)
class ConnectorMaterializationDependencies:
    bind_meta_graph_runtime_lane: BindMetaGraphRuntimeLane
    resolve_projection_opgi_id: ResolveProjectionOpgiId
    find_projection_graph_by_opgi_id: FindProjectionGraphByOpgiId


@dataclass(frozen=True, slots=True)
class ConnectorInvocationRequestFieldMaterializationSpec:
    attribute: str
    source_ref: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class ConnectorInvocationActionConfigMaterializationSpec:
    action_key: str
    action_kind: str
    target_ref: str
    materialized_action_key: str
    source_path: str
    label: str | None = None
    receipt_policy: str | None = None
    confirmation_policy: str | None = None
    optimistic_policy: str | None = None
    request_fields: tuple[ConnectorInvocationRequestFieldMaterializationSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class ConnectorProviderMaterializationSpec:
    provider_key: str
    provider_kind: str
    source_path: str
    provider_ref: str | None = None
    label: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SensorConfigMaterializationSpec:
    sensor_key: str
    sensor_kind: str
    source_path: str
    source_ref: str | None = None
    observed_state_node_refs: tuple[str, ...] = ()
    label: str | None = None
    description: str | None = None
    invocation_action_configs: tuple[
        ConnectorInvocationActionConfigMaterializationSpec, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ActuatorConfigMaterializationSpec:
    actuator_key: str
    actuator_kind: str
    source_path: str
    target_ref: str | None = None
    affected_state_node_refs: tuple[str, ...] = ()
    label: str | None = None
    description: str | None = None
    invocation_action_configs: tuple[
        ConnectorInvocationActionConfigMaterializationSpec, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ConnectorConfigMaterializationSpec:
    connector_key: str
    connector_kind: str
    source_path: str
    projection_experience_name: str
    projection_key: str
    label: str | None = None
    description: str | None = None
    providers: tuple[ConnectorProviderMaterializationSpec, ...] = ()
    sensor_configs: tuple[SensorConfigMaterializationSpec, ...] = ()
    actuator_configs: tuple[ActuatorConfigMaterializationSpec, ...] = ()


def resolve_connector_config_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ConnectorConfigMaterializationSpec, ...]:
    return _resolve_connector_config_materialization_specs_from_payloads(
        compile_plan_payloads=compile_plan_payloads,
        payload_key="connector_ownership",
        require_projection=True,
        qualify_dependency_connector_key=False,
    )


def resolve_activation_target_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ConnectorConfigMaterializationSpec, ...]:
    return _resolve_connector_config_materialization_specs_from_payloads(
        compile_plan_payloads=compile_plan_payloads,
        payload_key="action_target_ownership",
        require_projection=False,
        qualify_dependency_connector_key=True,
    )


def _resolve_connector_config_materialization_specs_from_payloads(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    payload_key: str,
    require_projection: bool,
    qualify_dependency_connector_key: bool,
) -> tuple[ConnectorConfigMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    specs_by_key: dict[str, ConnectorConfigMaterializationSpec] = {}
    materialized_action_keys_seen: set[str] = set()
    for payload in compile_plan_payloads:
        if require_projection:
            canonical_projection_name, canonical_projection_key = (
                _canonical_projection_experience_for_connector_payload(payload=payload)
            )
        else:
            canonical_projection_name = ""
            canonical_projection_key = ""
        connectors_raw = _expect_list(
            payload.get(payload_key, []),
            field_name=payload_key,
        )
        for connector_obj in connectors_raw:
            connector_row = _expect_mapping(
                connector_obj, field_name=f"{payload_key}[]"
            )
            raw_connector_key = _required_step_payload_token(
                connector_row.get("connector_key")
            )
            connector_key = (
                _dependency_connector_materialized_key(
                    connector_row=connector_row,
                    connector_key=raw_connector_key,
                )
                if qualify_dependency_connector_key
                else raw_connector_key
            )
            connector_key_folded = connector_key.casefold()
            if connector_key_folded in specs_by_key:
                raise RuntimeError(
                    "Invalid experience compile plan: duplicate connector config "
                    + f"{connector_key!r}"
                )

            providers = _resolve_connector_provider_specs(connector_row=connector_row)
            sensor_specs = _resolve_sensor_config_specs(
                connector_key=connector_key,
                connector_row=connector_row,
                materialized_action_keys_seen=materialized_action_keys_seen,
            )
            actuator_specs = _resolve_actuator_config_specs(
                connector_key=connector_key,
                connector_row=connector_row,
                materialized_action_keys_seen=materialized_action_keys_seen,
            )
            specs_by_key[connector_key_folded] = ConnectorConfigMaterializationSpec(
                connector_key=connector_key,
                connector_kind=_required_step_payload_token(
                    connector_row.get("connector_kind")
                ),
                source_path=_required_step_payload_token(
                    connector_row.get("source_path")
                ),
                projection_experience_name=canonical_projection_name,
                projection_key=canonical_projection_key,
                label=_optional_payload_token(connector_row.get("label")),
                description=_optional_payload_token(connector_row.get("description")),
                providers=providers,
                sensor_configs=sensor_specs,
                actuator_configs=actuator_specs,
            )

    return tuple(
        spec for _, spec in sorted(specs_by_key.items(), key=lambda item: item[0])
    )


def _dependency_connector_materialized_key(
    *,
    connector_row: Mapping[str, object],
    connector_key: str,
) -> str:
    if not bool(connector_row.get("is_dependency", False)):
        return connector_key
    prefix = _connector_owner_prefix(
        _optional_payload_token(connector_row.get("fqn_prefix"))
        or _optional_payload_token(connector_row.get("package_name"))
    )
    if not prefix:
        return connector_key
    connector_key = connector_key.strip()
    if connector_key.casefold().startswith(f"{prefix.casefold()}."):
        return connector_key
    return f"{prefix}.{connector_key}"


def _connector_owner_prefix(raw: str | None) -> str:
    return (raw or "").strip().replace("-", "_")


def _canonical_projection_experience_for_connector_payload(
    *,
    payload: Mapping[str, object],
) -> tuple[str, str]:
    projection_rows_raw = _expect_list(
        payload.get("projection_experience_ownership", []),
        field_name="projection_experience_ownership",
    )
    projection_rows: list[tuple[str, str]] = []
    for row_obj in projection_rows_raw:
        row = _expect_mapping(row_obj, field_name="projection_experience_ownership[]")
        projection_rows.append(
            (
                _required_step_payload_token(row.get("name")),
                _required_step_payload_token(row.get("projection")),
            )
        )
    if not projection_rows:
        connectors_raw = _expect_list(
            payload.get("connector_ownership", []),
            field_name="connector_ownership",
        )
        if connectors_raw:
            raise RuntimeError(
                "Invalid experience compile plan: connector config materialization "
                "requires at least one projection_experience_ownership row for "
                "the shared ExperienceInvocationActionConfig parent"
            )
        return ("", "")
    return sorted(projection_rows, key=lambda item: (item[0].casefold(), item[1]))[0]


def _resolve_connector_provider_specs(
    *,
    connector_row: Mapping[str, object],
) -> tuple[ConnectorProviderMaterializationSpec, ...]:
    providers_raw = _expect_list(
        connector_row.get("providers", []),
        field_name="connector_ownership[].providers",
    )
    providers_by_key: dict[str, ConnectorProviderMaterializationSpec] = {}
    for provider_obj in providers_raw:
        provider_row = _expect_mapping(
            provider_obj, field_name="connector_ownership[].providers[]"
        )
        provider_key = _required_step_payload_token(provider_row.get("provider_key"))
        key = provider_key.casefold()
        if key in providers_by_key:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate connector provider "
                + f"{provider_key!r}"
            )
        providers_by_key[key] = ConnectorProviderMaterializationSpec(
            provider_key=provider_key,
            provider_kind=_required_step_payload_token(
                provider_row.get("provider_kind")
            ),
            source_path=_required_step_payload_token(provider_row.get("source_path")),
            provider_ref=_optional_payload_token(provider_row.get("provider_ref")),
            label=_optional_payload_token(provider_row.get("label")),
            description=_optional_payload_token(provider_row.get("description")),
        )
    return tuple(
        provider
        for _, provider in sorted(providers_by_key.items(), key=lambda item: item[0])
    )


def _resolve_sensor_config_specs(
    *,
    connector_key: str,
    connector_row: Mapping[str, object],
    materialized_action_keys_seen: set[str],
) -> tuple[SensorConfigMaterializationSpec, ...]:
    sensors_raw = _expect_list(
        connector_row.get("sensor_configs", []),
        field_name="connector_ownership[].sensor_configs",
    )
    sensors_by_key: dict[str, SensorConfigMaterializationSpec] = {}
    for sensor_obj in sensors_raw:
        sensor_row = _expect_mapping(
            sensor_obj, field_name="connector_ownership[].sensor_configs[]"
        )
        if "payload_schema_ref" in sensor_row:
            raise RuntimeError(
                "Invalid experience compile plan: "
                "connector_ownership[].sensor_configs[].payload_schema_ref is "
                "retired; declare observed_state_node_refs instead"
            )
        sensor_key = _required_step_payload_token(sensor_row.get("sensor_key"))
        key = sensor_key.casefold()
        if key in sensors_by_key:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate connector sensor "
                + f"{sensor_key!r}"
            )
        sensors_by_key[key] = SensorConfigMaterializationSpec(
            sensor_key=sensor_key,
            sensor_kind=_required_step_payload_token(sensor_row.get("sensor_kind")),
            source_path=_required_step_payload_token(sensor_row.get("source_path")),
            source_ref=_optional_payload_token(sensor_row.get("source_ref")),
            observed_state_node_refs=_state_node_refs_from_payload(
                sensor_row.get("observed_state_node_refs"),
                field_name=(
                    "connector_ownership[].sensor_configs[].observed_state_node_refs"
                ),
            ),
            label=_optional_payload_token(sensor_row.get("label")),
            description=_optional_payload_token(sensor_row.get("description")),
            invocation_action_configs=_resolve_connector_invocation_specs(
                connector_key=connector_key,
                surface_kind="sensor",
                surface_key=sensor_key,
                surface_row=sensor_row,
                materialized_action_keys_seen=materialized_action_keys_seen,
            ),
        )
    return tuple(
        sensor for _, sensor in sorted(sensors_by_key.items(), key=lambda item: item[0])
    )


def _resolve_actuator_config_specs(
    *,
    connector_key: str,
    connector_row: Mapping[str, object],
    materialized_action_keys_seen: set[str],
) -> tuple[ActuatorConfigMaterializationSpec, ...]:
    actuators_raw = _expect_list(
        connector_row.get("actuator_configs", []),
        field_name="connector_ownership[].actuator_configs",
    )
    actuators_by_key: dict[str, ActuatorConfigMaterializationSpec] = {}
    for actuator_obj in actuators_raw:
        actuator_row = _expect_mapping(
            actuator_obj, field_name="connector_ownership[].actuator_configs[]"
        )
        if "payload_schema_ref" in actuator_row:
            raise RuntimeError(
                "Invalid experience compile plan: "
                "connector_ownership[].actuator_configs[].payload_schema_ref is "
                "retired; declare affected_state_node_refs instead"
            )
        actuator_key = _required_step_payload_token(actuator_row.get("actuator_key"))
        key = actuator_key.casefold()
        if key in actuators_by_key:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate connector actuator "
                + f"{actuator_key!r}"
            )
        actuators_by_key[key] = ActuatorConfigMaterializationSpec(
            actuator_key=actuator_key,
            actuator_kind=_required_step_payload_token(
                actuator_row.get("actuator_kind")
            ),
            source_path=_required_step_payload_token(actuator_row.get("source_path")),
            target_ref=_optional_payload_token(actuator_row.get("target_ref")),
            affected_state_node_refs=_state_node_refs_from_payload(
                actuator_row.get("affected_state_node_refs"),
                field_name=(
                    "connector_ownership[].actuator_configs[].affected_state_node_refs"
                ),
            ),
            label=_optional_payload_token(actuator_row.get("label")),
            description=_optional_payload_token(actuator_row.get("description")),
            invocation_action_configs=_resolve_connector_invocation_specs(
                connector_key=connector_key,
                surface_kind="actuator",
                surface_key=actuator_key,
                surface_row=actuator_row,
                materialized_action_keys_seen=materialized_action_keys_seen,
            ),
        )
    return tuple(
        actuator
        for _, actuator in sorted(actuators_by_key.items(), key=lambda item: item[0])
    )


def _resolve_connector_invocation_specs(
    *,
    connector_key: str,
    surface_kind: str,
    surface_key: str,
    surface_row: Mapping[str, object],
    materialized_action_keys_seen: set[str],
) -> tuple[ConnectorInvocationActionConfigMaterializationSpec, ...]:
    invocations_raw = _expect_list(
        surface_row.get("invocation_action_configs", []),
        field_name=(
            "connector_ownership[]."
            + f"{surface_kind}_configs[].invocation_action_configs"
        ),
    )
    invocations_by_key: dict[
        str, ConnectorInvocationActionConfigMaterializationSpec
    ] = {}
    for invocation_obj in invocations_raw:
        invocation_row = _expect_mapping(
            invocation_obj,
            field_name=(
                "connector_ownership[]."
                + f"{surface_kind}_configs[].invocation_action_configs[]"
            ),
        )
        action_key = _required_step_payload_token(invocation_row.get("action_key"))
        action_key_folded = action_key.casefold()
        if action_key_folded in invocations_by_key:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate "
                + f"{surface_kind} invocation action {action_key!r}"
            )
        action_kind = _required_step_payload_token(invocation_row.get("action_kind"))
        if action_kind not in {"api", "sdk"}:
            raise RuntimeError(
                "Invalid experience compile plan: connector invocation action_kind "
                + f"must be api or sdk: {action_kind!r}"
            )
        materialized_action_key = _connector_materialized_action_key(
            connector_key=connector_key,
            surface_kind=surface_kind,
            surface_key=surface_key,
            action_key=action_key,
        )
        materialized_action_key_folded = materialized_action_key.casefold()
        if materialized_action_key_folded in materialized_action_keys_seen:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate materialized connector "
                + f"invocation action key {materialized_action_key!r}"
            )
        materialized_action_keys_seen.add(materialized_action_key_folded)
        invocations_by_key[action_key_folded] = (
            ConnectorInvocationActionConfigMaterializationSpec(
                action_key=action_key,
                action_kind=action_kind,
                target_ref=_required_step_payload_token(
                    invocation_row.get("target_ref")
                ),
                materialized_action_key=materialized_action_key,
                source_path=_required_step_payload_token(
                    invocation_row.get("source_path")
                ),
                label=_optional_payload_token(invocation_row.get("label")),
                receipt_policy=_optional_payload_token(
                    invocation_row.get("receipt_policy")
                ),
                confirmation_policy=_optional_payload_token(
                    invocation_row.get("confirmation_policy")
                ),
                optimistic_policy=_optional_payload_token(
                    invocation_row.get("optimistic_policy")
                ),
                request_fields=_resolve_connector_invocation_request_fields(
                    invocation_row=invocation_row,
                    field_name=(
                        "connector_ownership[]."
                        + f"{surface_kind}_configs[]."
                        + "invocation_action_configs[].request_fields"
                    ),
                ),
            )
        )
    return tuple(
        invocation
        for _, invocation in sorted(
            invocations_by_key.items(), key=lambda item: item[0]
        )
    )


def _resolve_connector_invocation_request_fields(
    *,
    invocation_row: Mapping[str, object],
    field_name: str,
) -> tuple[ConnectorInvocationRequestFieldMaterializationSpec, ...]:
    request_fields_raw = _expect_list(
        invocation_row.get("request_fields", []),
        field_name=field_name,
    )
    request_fields: list[ConnectorInvocationRequestFieldMaterializationSpec] = []
    seen_attributes: set[str] = set()
    for field_obj in request_fields_raw:
        field_row = _expect_mapping(field_obj, field_name=f"{field_name}[]")
        attribute = _required_step_payload_token(field_row.get("attribute"))
        attribute_key = attribute.casefold()
        if attribute_key in seen_attributes:
            raise RuntimeError(
                "Invalid experience compile plan: duplicate connector invocation "
                + f"request field attribute {attribute!r}"
            )
        seen_attributes.add(attribute_key)
        request_fields.append(
            ConnectorInvocationRequestFieldMaterializationSpec(
                attribute=attribute,
                source_ref=_required_step_payload_token(field_row.get("source_ref")),
                required=bool(field_row.get("required", True)),
            )
        )
    return tuple(request_fields)


def build_connector_config_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ConnectorConfigMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"connector_config:{spec.connector_key}",
            step_kind="experience.connector_config",
            payload=encode_connector_config_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.connector_config",
        lane=lane,
        steps=steps,
    )


def encode_connector_config_materialization_step_payload(
    *,
    spec: ConnectorConfigMaterializationSpec,
) -> dict[str, object]:
    payload = _ConnectorConfigMaterializationStepPayload(
        connector_key=spec.connector_key,
        connector_kind=spec.connector_kind,
        source_path=spec.source_path,
        projection_experience_name=spec.projection_experience_name,
        projection_key=spec.projection_key,
        label=spec.label,
        description=spec.description,
        providers=tuple(
            _ConnectorProviderMaterializationPayload(
                provider_key=provider.provider_key,
                provider_kind=provider.provider_kind,
                source_path=provider.source_path,
                provider_ref=provider.provider_ref,
                label=provider.label,
                description=provider.description,
            )
            for provider in spec.providers
        ),
        sensor_configs=tuple(
            _SensorConfigMaterializationPayload(
                sensor_key=sensor.sensor_key,
                sensor_kind=sensor.sensor_kind,
                source_path=sensor.source_path,
                source_ref=sensor.source_ref,
                observed_state_node_refs=sensor.observed_state_node_refs,
                label=sensor.label,
                description=sensor.description,
                invocation_action_configs=tuple(
                    _ConnectorInvocationActionConfigPayload(
                        action_key=invocation.action_key,
                        action_kind=invocation.action_kind,
                        target_ref=invocation.target_ref,
                        materialized_action_key=invocation.materialized_action_key,
                        source_path=invocation.source_path,
                        label=invocation.label,
                        receipt_policy=invocation.receipt_policy,
                        confirmation_policy=invocation.confirmation_policy,
                        optimistic_policy=invocation.optimistic_policy,
                        request_fields=tuple(
                            _ConnectorInvocationRequestFieldPayload(
                                attribute=field.attribute,
                                source_ref=field.source_ref,
                                required=field.required,
                            )
                            for field in invocation.request_fields
                        ),
                    )
                    for invocation in sensor.invocation_action_configs
                ),
            )
            for sensor in spec.sensor_configs
        ),
        actuator_configs=tuple(
            _ActuatorConfigMaterializationPayload(
                actuator_key=actuator.actuator_key,
                actuator_kind=actuator.actuator_kind,
                source_path=actuator.source_path,
                target_ref=actuator.target_ref,
                affected_state_node_refs=actuator.affected_state_node_refs,
                label=actuator.label,
                description=actuator.description,
                invocation_action_configs=tuple(
                    _ConnectorInvocationActionConfigPayload(
                        action_key=invocation.action_key,
                        action_kind=invocation.action_kind,
                        target_ref=invocation.target_ref,
                        materialized_action_key=invocation.materialized_action_key,
                        source_path=invocation.source_path,
                        label=invocation.label,
                        receipt_policy=invocation.receipt_policy,
                        confirmation_policy=invocation.confirmation_policy,
                        optimistic_policy=invocation.optimistic_policy,
                        request_fields=tuple(
                            _ConnectorInvocationRequestFieldPayload(
                                attribute=field.attribute,
                                source_ref=field.source_ref,
                                required=field.required,
                            )
                            for field in invocation.request_fields
                        ),
                    )
                    for invocation in actuator.invocation_action_configs
                ),
            )
            for actuator in spec.actuator_configs
        ),
    )
    return cast(dict[str, object], payload.model_dump(mode="json"))


def decode_connector_config_materialization_step_payload(
    payload: Mapping[str, object],
) -> ConnectorConfigMaterializationSpec:
    try:
        step_payload = _ConnectorConfigMaterializationStepPayload.model_validate(
            payload
        )
    except ValidationError as exc:
        raise RuntimeError(
            _format_step_payload_validation_error(exc=exc, prefix="connector_config")
        ) from exc

    return ConnectorConfigMaterializationSpec(
        connector_key=step_payload.connector_key,
        connector_kind=step_payload.connector_kind,
        source_path=step_payload.source_path,
        projection_experience_name=step_payload.projection_experience_name,
        projection_key=step_payload.projection_key,
        label=step_payload.label,
        description=step_payload.description,
        providers=tuple(
            ConnectorProviderMaterializationSpec(
                provider_key=provider.provider_key,
                provider_kind=provider.provider_kind,
                source_path=provider.source_path,
                provider_ref=provider.provider_ref,
                label=provider.label,
                description=provider.description,
            )
            for provider in step_payload.providers
        ),
        sensor_configs=tuple(
            SensorConfigMaterializationSpec(
                sensor_key=sensor.sensor_key,
                sensor_kind=sensor.sensor_kind,
                source_path=sensor.source_path,
                source_ref=sensor.source_ref,
                observed_state_node_refs=sensor.observed_state_node_refs,
                label=sensor.label,
                description=sensor.description,
                invocation_action_configs=tuple(
                    ConnectorInvocationActionConfigMaterializationSpec(
                        action_key=invocation.action_key,
                        action_kind=invocation.action_kind,
                        target_ref=invocation.target_ref,
                        materialized_action_key=(invocation.materialized_action_key),
                        source_path=invocation.source_path,
                        label=invocation.label,
                        receipt_policy=invocation.receipt_policy,
                        confirmation_policy=invocation.confirmation_policy,
                        optimistic_policy=invocation.optimistic_policy,
                        request_fields=tuple(
                            ConnectorInvocationRequestFieldMaterializationSpec(
                                attribute=field.attribute,
                                source_ref=field.source_ref,
                                required=field.required,
                            )
                            for field in invocation.request_fields
                        ),
                    )
                    for invocation in sensor.invocation_action_configs
                ),
            )
            for sensor in step_payload.sensor_configs
        ),
        actuator_configs=tuple(
            ActuatorConfigMaterializationSpec(
                actuator_key=actuator.actuator_key,
                actuator_kind=actuator.actuator_kind,
                source_path=actuator.source_path,
                target_ref=actuator.target_ref,
                affected_state_node_refs=actuator.affected_state_node_refs,
                label=actuator.label,
                description=actuator.description,
                invocation_action_configs=tuple(
                    ConnectorInvocationActionConfigMaterializationSpec(
                        action_key=invocation.action_key,
                        action_kind=invocation.action_kind,
                        target_ref=invocation.target_ref,
                        materialized_action_key=(invocation.materialized_action_key),
                        source_path=invocation.source_path,
                        label=invocation.label,
                        receipt_policy=invocation.receipt_policy,
                        confirmation_policy=invocation.confirmation_policy,
                        optimistic_policy=invocation.optimistic_policy,
                        request_fields=tuple(
                            ConnectorInvocationRequestFieldMaterializationSpec(
                                attribute=field.attribute,
                                source_ref=field.source_ref,
                                required=field.required,
                            )
                            for field in invocation.request_fields
                        ),
                    )
                    for invocation in actuator.invocation_action_configs
                ),
            )
            for actuator in step_payload.actuator_configs
        ),
    )


async def materialize_experience_connector_config_ontology(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    dependencies: ConnectorMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    specs = resolve_connector_config_materialization_specs(
        compile_plan_payloads=compile_plan_payloads
    )
    if not specs:
        return None

    connector_config_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ConnectorConfig",
    )
    projection_experience_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    sensor_invocation_action_config_projection_hash = (
        ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="SensorInvocationActionConfig",
        )
    )
    actuator_invocation_action_config_projection_hash = (
        ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="ActuatorInvocationActionConfig",
        )
    )
    connector_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=connector_config_projection_hash,
    )
    plan = build_connector_config_materialization_plan(
        lane=connector_lane,
        specs=specs,
    )
    opgi_by_key = ocg_support.build_opgi_index(index=index)
    opgi_by_key_casefolded = {
        (key or "").strip().casefold(): opgi_entry
        for key, opgi_entry in opgi_by_key.items()
        if (key or "").strip()
    }

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = decode_connector_config_materialization_step_payload(step.payload)
        experience_branch_id = derive_experience_reference_branch_id(
            base_branch_id=lane.branch_id,
            experience_name=spec.projection_experience_name,
        )
        projection_opgi_id = dependencies.resolve_projection_opgi_id(
            opgi_by_key_casefolded=opgi_by_key_casefolded,
            projection_key=spec.projection_key,
            experience_name=spec.projection_experience_name,
        )
        projection_experience_id = (
            experience_stable_ids.stable_projection_experience_id(
                object_projection_graph_identity_id=projection_opgi_id,
                name=spec.projection_experience_name,
            )
        )
        has_state_node_refs = any(
            sensor.observed_state_node_refs for sensor in spec.sensor_configs
        ) or any(
            actuator.affected_state_node_refs for actuator in spec.actuator_configs
        )
        projection_opg = (
            dependencies.find_projection_graph_by_opgi_id(
                index=index,
                object_projection_graph_identity_id=projection_opgi_id,
            )
            if has_state_node_refs
            else None
        )
        sensor_state_node_ids_by_key = {
            sensor.sensor_key.casefold(): (
                _resolve_connector_state_node_ids(
                    index=index,
                    opg=cast(ObjectProjectionGraph, projection_opg),
                    state_node_refs=sensor.observed_state_node_refs,
                    experience_name=spec.projection_experience_name,
                    connector_key=spec.connector_key,
                    surface_kind="sensor",
                    surface_key=sensor.sensor_key,
                )
                if sensor.observed_state_node_refs
                else ()
            )
            for sensor in spec.sensor_configs
        }
        actuator_state_node_ids_by_key = {
            actuator.actuator_key.casefold(): (
                _resolve_connector_state_node_ids(
                    index=index,
                    opg=cast(ObjectProjectionGraph, projection_opg),
                    state_node_refs=actuator.affected_state_node_refs,
                    experience_name=spec.projection_experience_name,
                    connector_key=spec.connector_key,
                    surface_kind="actuator",
                    surface_key=actuator.actuator_key,
                )
                if actuator.affected_state_node_refs
                else ()
            )
            for actuator in spec.actuator_configs
        }

        last_commit_id: UUID | None = None
        last_head_commit_id: UUID | None = None
        sensor_config_ids_by_key: dict[str, UUID] = {}
        actuator_config_ids_by_key: dict[str, UUID] = {}

        connector_runtime_lane = dependencies.bind_meta_graph_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=plan.lane.branch_id,
            projection=plan.lane.projection_hash,
            actor_id=actor_id,
        )
        with connector_runtime_lane.activate(
            commit=True,
            publish=False,
        ):
            connector_config = await ConnectorConfig.create(
                connector_key=spec.connector_key,
                connector_kind=spec.connector_kind,
                label=spec.label,
                description=spec.description,
            )
            for provider in spec.providers:
                _ = await connector_config.add_provider(
                    provider_key=provider.provider_key,
                    provider_kind=provider.provider_kind,
                    provider_ref=provider.provider_ref,
                    label=provider.label,
                    description=provider.description,
                )
            for sensor in spec.sensor_configs:
                sensor_config = await connector_config.add_sensor_config(
                    sensor_key=sensor.sensor_key,
                    sensor_kind=sensor.sensor_kind,
                    source_ref=sensor.source_ref,
                    label=sensor.label,
                    description=sensor.description,
                )
                for object_projection_graph_node_id in sensor_state_node_ids_by_key[
                    sensor.sensor_key.casefold()
                ]:
                    _ = await sensor_config.add_observed_state_node(
                        object_projection_graph_node_id=object_projection_graph_node_id,
                    )
                sensor_config_ids_by_key[sensor.sensor_key.casefold()] = (
                    sensor_config.id
                )
            for actuator in spec.actuator_configs:
                actuator_config = await connector_config.add_actuator_config(
                    actuator_key=actuator.actuator_key,
                    actuator_kind=actuator.actuator_kind,
                    target_ref=actuator.target_ref,
                    label=actuator.label,
                    description=actuator.description,
                )
                for object_projection_graph_node_id in actuator_state_node_ids_by_key[
                    actuator.actuator_key.casefold()
                ]:
                    _ = await actuator_config.add_affected_state_node(
                        object_projection_graph_node_id=object_projection_graph_node_id,
                    )
                actuator_config_ids_by_key[actuator.actuator_key.casefold()] = (
                    actuator_config.id
                )
        if connector_runtime_lane.last_commit_id is not None:
            last_commit_id = connector_runtime_lane.last_commit_id
        if connector_runtime_lane.last_head_commit_id is not None:
            last_head_commit_id = connector_runtime_lane.last_head_commit_id

        action_config_ids_by_materialized_key: dict[str, UUID] = {}
        projection_lane = MaterializationLaneContext(
            branch_id=experience_branch_id,
            projection_hash=projection_experience_projection_hash,
        )
        projection_runtime_lane = dependencies.bind_meta_graph_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=projection_lane.branch_id,
            projection=projection_lane.projection_hash,
            actor_id=actor_id,
        )
        with projection_runtime_lane.activate(
            commit=True,
            publish=False,
        ):
            projection_experience = ProjectionExperience.model_construct(
                id=projection_experience_id,
            )
            for sensor in spec.sensor_configs:
                for action in sensor.invocation_action_configs:
                    target_kind, api_endpoint_id, sdk_operation_id = (
                        _connector_invocation_action_target_ids(
                            action=action,
                            connector_key=spec.connector_key,
                            surface_kind="sensor",
                            surface_key=sensor.sensor_key,
                        )
                    )
                    action_config = (
                        await projection_experience.create_invocation_action_config(
                            target_kind=target_kind,
                            api_capability_endpoint_id=api_endpoint_id,
                            sdk_operation_id=sdk_operation_id,
                        )
                    )
                    action_config_ids_by_materialized_key[
                        action.materialized_action_key.casefold()
                    ] = action_config.id
            for actuator in spec.actuator_configs:
                for action in actuator.invocation_action_configs:
                    target_kind, api_endpoint_id, sdk_operation_id = (
                        _connector_invocation_action_target_ids(
                            action=action,
                            connector_key=spec.connector_key,
                            surface_kind="actuator",
                            surface_key=actuator.actuator_key,
                        )
                    )
                    action_config = (
                        await projection_experience.create_invocation_action_config(
                            target_kind=target_kind,
                            api_capability_endpoint_id=api_endpoint_id,
                            sdk_operation_id=sdk_operation_id,
                        )
                    )
                    action_config_ids_by_materialized_key[
                        action.materialized_action_key.casefold()
                    ] = action_config.id
        if projection_runtime_lane.last_commit_id is not None:
            last_commit_id = projection_runtime_lane.last_commit_id
        if projection_runtime_lane.last_head_commit_id is not None:
            last_head_commit_id = projection_runtime_lane.last_head_commit_id

        sensor_binding_count = 0
        sensor_binding_lane = MaterializationLaneContext(
            branch_id=plan.lane.branch_id,
            projection_hash=sensor_invocation_action_config_projection_hash,
        )
        sensor_runtime_lane = dependencies.bind_meta_graph_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=sensor_binding_lane.branch_id,
            projection=sensor_binding_lane.projection_hash,
            actor_id=actor_id,
        )
        with sensor_runtime_lane.activate(
            commit=True,
            publish=False,
        ):
            for sensor in spec.sensor_configs:
                sensor_config_id = sensor_config_ids_by_key[
                    sensor.sensor_key.casefold()
                ]
                for action in sensor.invocation_action_configs:
                    experience_action_config_id = action_config_ids_by_materialized_key[
                        action.materialized_action_key.casefold()
                    ]
                    _ = await SensorInvocationActionConfig.build_via_sensor_config(
                        sensor_config_id=sensor_config_id,
                        experience_invocation_action_config_id=(
                            experience_action_config_id
                        ),
                    )
                    sensor_binding_count += 1
        if sensor_runtime_lane.last_commit_id is not None:
            last_commit_id = sensor_runtime_lane.last_commit_id
        if sensor_runtime_lane.last_head_commit_id is not None:
            last_head_commit_id = sensor_runtime_lane.last_head_commit_id

        actuator_binding_count = 0
        actuator_binding_lane = MaterializationLaneContext(
            branch_id=plan.lane.branch_id,
            projection_hash=actuator_invocation_action_config_projection_hash,
        )
        actuator_runtime_lane = dependencies.bind_meta_graph_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=actuator_binding_lane.branch_id,
            projection=actuator_binding_lane.projection_hash,
            actor_id=actor_id,
        )
        with actuator_runtime_lane.activate(
            commit=True,
            publish=False,
        ):
            for actuator in spec.actuator_configs:
                actuator_config_id = actuator_config_ids_by_key[
                    actuator.actuator_key.casefold()
                ]
                for action in actuator.invocation_action_configs:
                    experience_action_config_id = action_config_ids_by_materialized_key[
                        action.materialized_action_key.casefold()
                    ]
                    _ = await ActuatorInvocationActionConfig.build_via_actuator_config(
                        actuator_config_id=actuator_config_id,
                        experience_invocation_action_config_id=(
                            experience_action_config_id
                        ),
                    )
                    actuator_binding_count += 1
        if actuator_runtime_lane.last_commit_id is not None:
            last_commit_id = actuator_runtime_lane.last_commit_id
        if actuator_runtime_lane.last_head_commit_id is not None:
            last_head_commit_id = actuator_runtime_lane.last_head_commit_id

        return MaterializationStepResult(
            details={
                "connector_key": spec.connector_key,
                "provider_count": len(spec.providers),
                "sensor_config_count": len(spec.sensor_configs),
                "actuator_config_count": len(spec.actuator_configs),
                "sensor_state_node_count": sum(
                    len(node_ids) for node_ids in sensor_state_node_ids_by_key.values()
                ),
                "actuator_state_node_count": sum(
                    len(node_ids)
                    for node_ids in actuator_state_node_ids_by_key.values()
                ),
                "invocation_action_config_count": (
                    len(action_config_ids_by_materialized_key)
                ),
                "sensor_invocation_action_config_count": sensor_binding_count,
                "actuator_invocation_action_config_count": actuator_binding_count,
            },
            commit_id=last_commit_id,
            head_commit_id=last_head_commit_id,
        )

    return await MaterializationExecutor().run(plan=plan, runner=_runner)


def _has_planned_threads(*, planned_processes: Sequence[Mapping[str, object]]) -> bool:
    for process_plan in planned_processes:
        threads = process_plan.get("threads")
        if isinstance(threads, list) and threads:
            return True
    return False


async def materialize_experience_compile_plan_connector_configs(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
    dependencies: ConnectorMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    if not _has_planned_threads(planned_processes=planned_processes):
        return None

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_connector_config_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        dependencies=dependencies,
    )


def _connector_materialized_action_key(
    *,
    connector_key: str,
    surface_kind: str,
    surface_key: str,
    action_key: str,
) -> str:
    return ".".join(
        token.strip().casefold()
        for token in (connector_key, surface_kind, surface_key, action_key)
        if token.strip()
    )


def _connector_invocation_action_target_ids(
    *,
    action: ConnectorInvocationActionConfigMaterializationSpec,
    connector_key: str,
    surface_kind: str,
    surface_key: str,
) -> tuple[ExperienceInvocationActionTargetKind, UUID | None, UUID | None]:
    action_kind = (action.action_kind or "").strip().casefold()
    target_ref = (action.target_ref or "").strip()
    if action_kind not in {"sdk", "api"}:
        raise RuntimeError(
            "Connector invocation action_kind must be sdk or api "
            + (
                f"(connector={connector_key!r}, surface={surface_kind!r}, "
                f"surface_key={surface_key!r}, action={action.action_key!r})"
            )
        )
    if not target_ref:
        raise RuntimeError(
            "Connector invocation action target_ref is required "
            + (
                f"(connector={connector_key!r}, surface={surface_kind!r}, "
                f"surface_key={surface_key!r}, action={action.action_key!r})"
            )
        )

    if action_kind == "sdk":
        parts = [part.strip() for part in target_ref.split(".") if part.strip()]
        if len(parts) < 2:
            raise RuntimeError(
                "SDK connector invocation target_ref must include `sdk.operation` "
                + (
                    f"(connector={connector_key!r}, surface={surface_kind!r}, "
                    f"surface_key={surface_key!r}, action={action.action_key!r}, "
                    f"target_ref={target_ref!r})"
                )
            )
        sdk_name = parts[0]
        operation_name = parts[-1]
        sdk_config_id = stable_sdk_config_id(name=sdk_name)
        return (
            ExperienceInvocationActionTargetKind.sdk,
            None,
            stable_sdk_operation_id(
                sdk_config_id=sdk_config_id,
                name=operation_name,
            ),
        )

    if action_kind == "api":
        parts = [part.strip() for part in target_ref.split(".") if part.strip()]
        if len(parts) != 3:
            raise RuntimeError(
                "API connector invocation target_ref must use "
                + "`api.capability.endpoint` "
                + (
                    f"(connector={connector_key!r}, surface={surface_kind!r}, "
                    f"surface_key={surface_key!r}, action={action.action_key!r}, "
                    f"target_ref={target_ref!r})"
                )
            )
        api_name, capability_name, endpoint_name = parts
        api_id = stable_api_id(name=api_name)
        api_capability_id = stable_api_capability_id(
            api_id=api_id,
            name=capability_name,
        )
        return (
            ExperienceInvocationActionTargetKind.api,
            stable_api_capability_endpoint_id(
                api_capability_id=api_capability_id,
                name=endpoint_name,
            ),
            None,
        )
    raise AssertionError(f"unreachable connector action kind: {action_kind}")


def _resolve_connector_state_node_ids(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    state_node_refs: Sequence[str],
    experience_name: str,
    connector_key: str,
    surface_kind: str,
    surface_key: str,
) -> tuple[UUID, ...]:
    if not state_node_refs:
        return ()

    node_specs: list[ProjectionExperienceNodeMaterializationSpec] = []
    seen_refs: set[str] = set()
    for position, node_ref in enumerate(state_node_refs):
        normalized_ref = (node_ref or "").strip()
        if not normalized_ref:
            raise RuntimeError(
                "Connector state-node footprint requires non-empty node refs "
                + (
                    f"(experience={experience_name!r}, connector={connector_key!r}, "
                    f"{surface_kind}={surface_key!r})"
                )
            )
        ref_key = normalized_ref.casefold()
        if ref_key in seen_refs:
            raise RuntimeError(
                "Connector state-node footprint contains duplicate node_ref "
                + (
                    f"(experience={experience_name!r}, connector={connector_key!r}, "
                    f"{surface_kind}={surface_key!r}, node_ref={normalized_ref!r})"
                )
            )
        seen_refs.add(ref_key)
        node_specs.append(
            ProjectionExperienceNodeMaterializationSpec(
                name=f"{surface_kind}.{surface_key}.state_node.{position}",
                node_ref=normalized_ref,
                identity_keys=("state",),
            )
        )

    snapshots = build_projection_node_snapshots_for_materialization(
        index=index,
        opg=opg,
        nodes=node_specs,
        experience_name=experience_name,
    )
    node_ids = tuple(snapshot.object_projection_graph_node_id for snapshot in snapshots)
    unique_node_ids = frozenset(node_ids)
    if len(unique_node_ids) != len(node_ids):
        raise RuntimeError(
            "Connector state-node footprint refs resolved to duplicate "
            "ObjectProjectionGraphNode ids "
            + (
                f"(experience={experience_name!r}, connector={connector_key!r}, "
                f"{surface_kind}={surface_key!r})"
            )
        )
    return node_ids
