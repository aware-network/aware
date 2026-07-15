from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import BaseModel

from aware_experience.compiler.models import (
    ExperienceActuatorConfigOwnership,
    ExperienceConnectorConfigOwnership,
    ExperienceConnectorInvocationActionConfigOwnership,
    ExperienceConnectorProviderOwnership,
    ExperienceSensorConfigOwnership,
)
from aware_experience.connector.compiler import load_connector_ownership_from_sources
from aware_experience.connector.protocol_renderer import (
    build_connector_protocol_plan,
    render_python_connector_protocol_module,
)
from aware_experience.materialization.service import (
    resolve_connector_config_materialization_specs,
)


@dataclass(frozen=True, slots=True)
class _GraphCommit:
    commit_id: str
    source_invocation_action_key: str
    object_ref: str
    patch: dict[str, object]
    event_types: tuple[str, ...]
    parent_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class _ReactivityEvent:
    event_type: str
    commit_id: str
    source_invocation_action_key: str
    payload: dict[str, object]


@dataclass(slots=True)
class _LocalGraph:
    commits: list[_GraphCommit] = field(default_factory=list)
    events: list[_ReactivityEvent] = field(default_factory=list)

    def commit(
        self,
        *,
        source_invocation_action_key: str,
        object_ref: str,
        patch: dict[str, object],
        event_types: tuple[str, ...],
        parent_commit_id: str | None = None,
    ) -> _GraphCommit:
        commit = _GraphCommit(
            commit_id=f"commit-{len(self.commits) + 1}-{uuid4()}",
            source_invocation_action_key=source_invocation_action_key,
            object_ref=object_ref,
            patch=patch,
            event_types=event_types,
            parent_commit_id=parent_commit_id,
        )
        self.commits.append(commit)
        for event_type in event_types:
            self.events.append(
                _ReactivityEvent(
                    event_type=event_type,
                    commit_id=commit.commit_id,
                    source_invocation_action_key=source_invocation_action_key,
                    payload=dict(patch),
                )
            )
        return commit


@dataclass(frozen=True, slots=True)
class _ActuatorRoute:
    materialized_action_key: str
    request: BaseModel
    trigger_commit_id: str


class _DoorByLabel(BaseModel):
    label: str


class _LockDoor(BaseModel):
    label: str


@dataclass(frozen=True, slots=True)
class _WorldEffect:
    materialized_action_key: str
    label: str
    command: str
    trigger_commit_id: str


class _DoorLockReactor:
    def route(self, *, event: _ReactivityEvent) -> _ActuatorRoute | None:
        if event.event_type != "home.door.state.changed":
            return None
        if bool(event.payload.get("is_locked")):
            return None
        if not bool(event.payload.get("desired_is_locked")):
            return None
        return _ActuatorRoute(
            materialized_action_key="home_devices.actuator.lock_door.lock",
            request=_LockDoor(label=str(event.payload["label"])),
            trigger_commit_id=event.commit_id,
        )


@pytest.mark.asyncio
async def test_home_sensor_graph_event_actuator_receipt_local_e2e() -> None:
    namespace = _home_story_connector_protocol_namespace()
    assert "ConnectorInvocationReceipt" not in namespace
    assert "SensorInvocationContext" not in namespace
    assert "ActuatorInvocationContext" not in namespace
    bindings = namespace["WORLD_SERVICE_ENDPOINT_BINDINGS"]
    graph = _LocalGraph()
    world_effects: list[_WorldEffect] = []

    class _DoorStateSensor:
        async def observe(self, request: _DoorByLabel) -> None:
            graph.commit(
                source_invocation_action_key=(
                    "home_devices.sensor.door_state.observe"
                ),
                object_ref=f"aware_home.home.Door:{request.label}",
                patch={
                    "label": request.label,
                    "is_locked": False,
                    "desired_is_locked": True,
                },
                event_types=("home.door.state.changed",),
            )
            return None

    class _LockDoorActuator:
        async def lock(self, request: _LockDoor) -> None:
            world_effects.append(
                _WorldEffect(
                    materialized_action_key="home_devices.actuator.lock_door.lock",
                    label=request.label,
                    command="lock",
                    trigger_commit_id=graph.events[0].commit_id,
                )
            )
            return None

    class _HomeDevicesConnector:
        @property
        def sensor_door_state(self) -> _DoorStateSensor:
            return _DoorStateSensor()

        @property
        def actuator_lock_door(self) -> _LockDoorActuator:
            return _LockDoorActuator()

    sensor_binding = bindings["home_devices.sensor.door_state.observe"]
    actuator_binding = bindings["home_devices.actuator.lock_door.lock"]
    assert sensor_binding.role == "client"
    assert sensor_binding.endpoint_ref == (
        "home_devices.observe_door_state.observe_door_state"
    )
    assert sensor_binding.request_type_ref == "aware_home_api.door.DoorByLabel"
    assert sensor_binding.receipt_policy == "event"
    assert actuator_binding.role == "handler"
    assert actuator_binding.endpoint_ref == "home_devices.lock_door.lock_door"
    assert actuator_binding.request_type_ref == "aware_home_api.door.LockDoor"

    handler = _HomeDevicesConnector()
    sensor_response = await sensor_binding.invoke(
        handler,
        _DoorByLabel(
            label="front_door",
        ),
    )

    assert sensor_response is None
    assert len(graph.commits) == 1
    assert graph.commits[0].event_types == ("home.door.state.changed",)
    assert len(graph.events) == 1

    route = _DoorLockReactor().route(event=graph.events[0])
    assert route is not None
    actuator_response = await actuator_binding.invoke(
        handler,
        route.request,
    )

    assert actuator_response is None
    assert len(graph.commits) == 1
    assert world_effects == [
        _WorldEffect(
            materialized_action_key="home_devices.actuator.lock_door.lock",
            label="front_door",
            command="lock",
            trigger_commit_id=graph.commits[0].commit_id,
        )
    ]
    assert [event.event_type for event in graph.events] == ["home.door.state.changed"]
    assert [commit.source_invocation_action_key for commit in graph.commits] == [
        "home_devices.sensor.door_state.observe",
    ]


def _home_story_connector_protocol_namespace() -> dict[str, object]:
    package_root = (
        _repo_root()
        / "workspaces"
        / "aware_home"
        / "modules"
        / "home"
        / "experiences"
        / "home_story"
    )
    connector_ownership = load_connector_ownership_from_sources(
        package_root=package_root,
        source_files=(Path("connectors/home_devices.aware"),),
    )
    specs = resolve_connector_config_materialization_specs(
        compile_plan_payloads=[
            {
                "package_name": "home-story-experience",
                "fqn_prefix": "aware_home_story",
                "projection_experience_ownership": [
                    {
                        "name": "home_story",
                        "projection": "aware_home.home.Home",
                        "source_path": "experiences.aware",
                    }
                ],
                "connector_ownership": [
                    _connector_ownership_payload(connector=connector)
                    for connector in connector_ownership
                ],
            }
        ]
    )
    plan = build_connector_protocol_plan(
        package_name="home-story-experience",
        fqn_prefix="aware_home_story",
        specs=specs,
        endpoint_bindings=_home_devices_endpoint_bindings(),
    )
    module_text = render_python_connector_protocol_module(plan=plan)
    namespace: dict[str, object] = {}
    exec(compile(module_text, "protocols.py", "exec"), namespace)
    return namespace


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "aware.environment.toml").exists():
            return parent
    raise AssertionError("Could not resolve repository root")


def _home_devices_endpoint_bindings() -> dict[str, object]:
    return {
        "home_devices.observe_door_state.observe_door_state": _endpoint_binding(
            endpoint_ref="home_devices.observe_door_state.observe_door_state",
            request_type_ref="aware_home_api.door.DoorByLabel",
        ),
        "home_devices.close_door.close_door": _endpoint_binding(
            endpoint_ref="home_devices.close_door.close_door",
            request_type_ref="aware_home_api.door.CloseDoor",
        ),
        "home_devices.lock_door.lock_door": _endpoint_binding(
            endpoint_ref="home_devices.lock_door.lock_door",
            request_type_ref="aware_home_api.door.LockDoor",
        ),
        "home_devices.open_door.open_door": _endpoint_binding(
            endpoint_ref="home_devices.open_door.open_door",
            request_type_ref="aware_home_api.door.DoorByLabel",
        ),
        "home_devices.unlock_door.unlock_door": _endpoint_binding(
            endpoint_ref="home_devices.unlock_door.unlock_door",
            request_type_ref="aware_home_api.door.UnlockDoor",
        ),
    }


def _endpoint_binding(
    *,
    endpoint_ref: str,
    request_type_ref: str,
    response_type_ref: str | None = None,
    stream_event_type_refs: tuple[str, ...] = (),
) -> object:
    api_name, capability_name, endpoint_name = endpoint_ref.split(".", 2)
    return SimpleNamespace(
        endpoint_ref=endpoint_ref,
        api_name=api_name,
        capability_name=capability_name,
        endpoint_name=endpoint_name,
        request_type_ref=request_type_ref,
        response_type_ref=response_type_ref,
        stream_event_type_refs=stream_event_type_refs,
        fulfillment_bindings=(),
    )


def _connector_ownership_payload(
    *,
    connector: ExperienceConnectorConfigOwnership,
) -> dict[str, object]:
    return {
        "connector_key": connector.connector_key,
        "connector_kind": connector.connector_kind,
        "source_path": connector.source_path,
        "label": connector.label,
        "description": connector.description,
        "providers": [
            _provider_ownership_payload(provider=provider)
            for provider in connector.providers
        ],
        "sensor_configs": [
            _sensor_ownership_payload(sensor=sensor)
            for sensor in connector.sensor_configs
        ],
        "actuator_configs": [
            _actuator_ownership_payload(actuator=actuator)
            for actuator in connector.actuator_configs
        ],
    }


def _provider_ownership_payload(
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


def _sensor_ownership_payload(
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
            _invocation_ownership_payload(invocation=invocation)
            for invocation in sensor.invocation_action_configs
        ],
    }


def _actuator_ownership_payload(
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
            _invocation_ownership_payload(invocation=invocation)
            for invocation in actuator.invocation_action_configs
        ],
    }


def _invocation_ownership_payload(
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
