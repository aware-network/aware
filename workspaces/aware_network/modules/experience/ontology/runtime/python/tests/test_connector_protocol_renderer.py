from __future__ import annotations

import importlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from collections.abc import Iterator

import pytest

from aware_experience.compiler.models import (
    ExperienceActuatorConfigOwnership,
    ExperienceConnectorConfigOwnership,
    ExperienceConnectorInvocationActionConfigOwnership,
    ExperienceConnectorProviderOwnership,
    ExperienceSensorConfigOwnership,
)
from aware_experience.connector.compiler import load_connector_ownership_from_sources
from aware_experience.connector.protocol_renderer import (
    CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME,
    build_connector_protocol_plan,
    encode_connector_protocol_plan,
    endpoint_contract_from_service_protocol_binding,
    render_python_connector_protocol_module,
    render_python_connector_protocol_sections,
)
from aware_experience.materialization.service import (
    ActuatorConfigMaterializationSpec,
    ConnectorConfigMaterializationSpec,
    ConnectorInvocationActionConfigMaterializationSpec,
    ConnectorProviderMaterializationSpec,
    SensorConfigMaterializationSpec,
    resolve_connector_config_materialization_specs,
)


def test_connector_protocol_plan_preserves_many_invocations_per_surface() -> None:
    plan = build_connector_protocol_plan(
        package_name="futurehill-ambient-experience",
        fqn_prefix="futurehill_ambient",
        specs=(_music_connector_spec(),),
    )

    payload = encode_connector_protocol_plan(plan=plan)

    assert payload["invocation_count"] == 3
    connector = plan.connectors[0]
    assert connector.connector_key == "music"
    assert connector.providers[0].provider_key == "youtube_music"
    now_playing = connector.sensor_surfaces[0]
    assert now_playing.surface_key == "now_playing"
    assert [item.action_key for item in now_playing.invocation_actions] == [
        "poll",
        "subscribe",
    ]
    assert [
        item.materialized_action_key for item in now_playing.invocation_actions
    ] == [
        "music.sensor.now_playing.poll",
        "music.sensor.now_playing.subscribe",
    ]


def test_python_connector_protocol_renderer_emits_invokers_and_manifest() -> None:
    plan = build_connector_protocol_plan(
        package_name="futurehill-ambient-experience",
        fqn_prefix="futurehill_ambient",
        specs=(_music_connector_spec(),),
        endpoint_bindings=_music_endpoint_bindings(),
    )

    module_text = render_python_connector_protocol_module(plan=plan)
    namespace = _exec_protocol_module(module_text)

    assert "class MusicNowPlayingSensorProtocol(Protocol):" in module_text
    assert "async def poll(" in module_text
    assert "async def subscribe(" in module_text
    assert "class MusicPlayTrackActuatorProtocol(Protocol):" in module_text
    assert "async def activate(" in module_text
    assert "def sensor_now_playing(self)" in module_text
    assert "MUSIC__SENSOR__NOW_PLAYING__POLL__BINDING" in namespace
    assert "ConnectorPayload" not in module_text
    assert "ConnectorInvocationReceipt" not in module_text
    assert "CONNECTOR_INVOCATION_BINDINGS" not in module_text

    bindings = namespace["WORLD_SERVICE_ENDPOINT_BINDINGS"]
    assert sorted(bindings) == [
        "music.actuator.play_track.activate",
        "music.sensor.now_playing.poll",
        "music.sensor.now_playing.subscribe",
    ]
    assert bindings["music.sensor.now_playing.poll"].role == "client"
    assert bindings["music.sensor.now_playing.poll"].endpoint_ref == (
        "MusicApi.Playback.now_playing"
    )
    assert bindings["music.sensor.now_playing.poll"].request_type_ref == (
        "futurehill.music.NowPlayingRequest"
    )
    assert bindings["music.sensor.now_playing.poll"].state_node_refs == (
        "clinic.Room::devices",
    )
    assert bindings["music.sensor.now_playing.subscribe"].stream_event_type_refs == (
        "futurehill.music.NowPlayingEvent",
    )
    assert bindings["music.actuator.play_track.activate"].role == "handler"
    assert bindings["music.actuator.play_track.activate"].endpoint_ref == (
        "MusicApi.Player.play"
    )
    assert bindings["music.actuator.play_track.activate"].state_node_refs == (
        "clinic.Room::devices",
    )
    assert "payload_schema_ref" not in module_text

    manifest = json.loads(namespace[CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME])
    sections = render_python_connector_protocol_sections(plan=plan)
    assert manifest["manifest_kind"] == "connector_protocol_section_text_manifest"
    assert manifest["section_count"] == len(sections) - 1
    assert manifest["target_relpath"] == "protocols.py"


def test_python_connector_protocol_renderer_rejects_graph_fulfillment() -> None:
    with pytest.raises(ValueError, match="graph fulfillment"):
        build_connector_protocol_plan(
            package_name="futurehill-ambient-experience",
            fqn_prefix="futurehill_ambient",
            specs=(_music_connector_spec(),),
            endpoint_bindings={
                "MusicApi.Playback.now_playing": _endpoint_binding(
                    endpoint_ref="MusicApi.Playback.now_playing",
                    request_type_ref="futurehill.music.NowPlayingRequest",
                    response_type_ref="futurehill.music.NowPlayingSnapshot",
                    fulfillment_bindings=(object(),),
                )
            },
        )


def test_home_story_connector_protocol_renderer_covers_source_fixture() -> None:
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
    payloads = [
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
    specs = resolve_connector_config_materialization_specs(
        compile_plan_payloads=payloads
    )
    plan = build_connector_protocol_plan(
        package_name="home-story-experience",
        fqn_prefix="aware_home_story",
        specs=specs,
        endpoint_bindings=_home_devices_endpoint_bindings(),
    )

    module_text = render_python_connector_protocol_module(plan=plan)
    namespace = _exec_protocol_module(module_text)
    bindings = namespace["WORLD_SERVICE_ENDPOINT_BINDINGS"]

    assert plan.invocation_count == 5
    assert sorted(bindings) == [
        "home_devices.actuator.close_door.close",
        "home_devices.actuator.lock_door.lock",
        "home_devices.actuator.open_door.open",
        "home_devices.actuator.unlock_door.unlock",
        "home_devices.sensor.door_state.observe",
    ]
    assert "class HomeDevicesDoorStateSensorProtocol(Protocol):" in module_text
    assert "class HomeDevicesLockDoorActuatorProtocol(Protocol):" in module_text
    assert "HOME_DEVICES__SENSOR__DOOR_STATE__OBSERVE__BINDING" in namespace
    assert "aware_home_ontology" not in module_text
    assert "ConnectorPayload" not in module_text
    assert "ConnectorInvocationReceipt" not in module_text
    assert "CONNECTOR_INVOCATION_BINDINGS" not in module_text
    assert bindings["home_devices.sensor.door_state.observe"].role == "client"
    assert bindings["home_devices.sensor.door_state.observe"].endpoint_ref == (
        "home_devices.observe_door_state.observe_door_state"
    )
    assert bindings["home_devices.sensor.door_state.observe"].request_type_ref == (
        "aware_home_api.door.DoorByLabel"
    )
    assert bindings["home_devices.sensor.door_state.observe"].state_node_refs == (
        "home.Home::doors",
    )
    assert bindings["home_devices.actuator.lock_door.lock"].role == "handler"
    assert bindings["home_devices.actuator.lock_door.lock"].endpoint_ref == (
        "home_devices.lock_door.lock_door"
    )
    assert bindings["home_devices.actuator.lock_door.lock"].request_type_ref == (
        "aware_home_api.door.LockDoor"
    )
    assert bindings["home_devices.actuator.lock_door.lock"].state_node_refs == (
        "home.Home::doors",
    )


def test_agent_fulfill_action_intent_renders_as_world_profile_handler() -> None:
    with _agent_api_python_path():
        protocol_module = importlib.import_module(
            "aware_agent_service_protocol.protocols"
        )
    source_binding = getattr(
        protocol_module,
        "AGENT__FULFILL_ACTION_INTENT__FULFILL_ACTION_INTENT_PROTOCOL_BINDING",
    )
    endpoint_contract = endpoint_contract_from_service_protocol_binding(
        source_binding
    )

    plan = build_connector_protocol_plan(
        package_name="agent-world-profile",
        fqn_prefix="aware_agent_world",
        specs=(_agent_action_connector_spec(),),
        endpoint_bindings={
            endpoint_contract.endpoint_ref: source_binding,
        },
    )
    module_text = render_python_connector_protocol_module(plan=plan)
    namespace = _exec_protocol_module(module_text)
    binding = namespace["WORLD_SERVICE_ENDPOINT_BINDINGS"][
        "agent_actions.actuator.agent_fulfillment.fulfill"
    ]

    assert binding.role == "handler"
    assert binding.endpoint_ref == "agent.fulfill_action_intent.fulfill_action_intent"
    assert binding.request_type_ref == (
        "aware_agent_service_dto.agent.reactivity.AgentActorAptExecutionRequest"
    )
    assert binding.response_type_ref == (
        "aware_agent_service_dto.agent.reactivity.AgentActorAptExecutionResult"
    )
    assert "ConnectorPayload" not in module_text
    assert "aware_reactivity_ontology" not in module_text


def _music_connector_spec() -> ConnectorConfigMaterializationSpec:
    return ConnectorConfigMaterializationSpec(
        connector_key="music",
        connector_kind="media",
        source_path="connectors/music.aware",
        projection_experience_name="futurehill_clinic",
        projection_key="ClinicAmbient",
        label="Music",
        providers=(
            ConnectorProviderMaterializationSpec(
                provider_key="youtube_music",
                provider_kind="music_streaming",
                source_path="connectors/music.aware",
                provider_ref="youtube.music",
                label="YouTube Music",
            ),
        ),
        sensor_configs=(
            SensorConfigMaterializationSpec(
                sensor_key="now_playing",
                sensor_kind="media_state",
                source_path="connectors/music.aware",
                source_ref="youtube.now_playing",
                observed_state_node_refs=("clinic.Room::devices",),
                invocation_action_configs=(
                    ConnectorInvocationActionConfigMaterializationSpec(
                        action_key="poll",
                        action_kind="api",
                        target_ref="MusicApi.Playback.now_playing",
                        materialized_action_key="music.sensor.now_playing.poll",
                        source_path="connectors/music.aware",
                        receipt_policy="event",
                    ),
                    ConnectorInvocationActionConfigMaterializationSpec(
                        action_key="subscribe",
                        action_kind="api",
                        target_ref="MusicApi.Playback.subscribe_now_playing",
                        materialized_action_key=("music.sensor.now_playing.subscribe"),
                        source_path="connectors/music.aware",
                        confirmation_policy="none",
                    ),
                ),
            ),
        ),
        actuator_configs=(
            ActuatorConfigMaterializationSpec(
                actuator_key="play_track",
                actuator_kind="media_control",
                source_path="connectors/music.aware",
                target_ref="youtube.play",
                affected_state_node_refs=("clinic.Room::devices",),
                invocation_action_configs=(
                    ConnectorInvocationActionConfigMaterializationSpec(
                        action_key="activate",
                        action_kind="api",
                        target_ref="MusicApi.Player.play",
                        materialized_action_key=("music.actuator.play_track.activate"),
                        source_path="connectors/music.aware",
                        optimistic_policy="immediate",
                    ),
                ),
            ),
        ),
    )


def _agent_action_connector_spec() -> ConnectorConfigMaterializationSpec:
    return ConnectorConfigMaterializationSpec(
        connector_key="agent_actions",
        connector_kind="agent_action_fulfillment",
        source_path="connectors/agent_actions.aware",
        projection_experience_name="futurehill_clinic",
        projection_key="ClinicAmbient",
        label="Agent actions",
        providers=(
            ConnectorProviderMaterializationSpec(
                provider_key="aware_agent",
                provider_kind="agent_service",
                source_path="connectors/agent_actions.aware",
                provider_ref="aware.agent",
                label="Aware Agent",
            ),
        ),
        sensor_configs=(),
        actuator_configs=(
            ActuatorConfigMaterializationSpec(
                actuator_key="agent_fulfillment",
                actuator_kind="agent_action",
                source_path="connectors/agent_actions.aware",
                target_ref="aware.agent",
                affected_state_node_refs=(),
                invocation_action_configs=(
                    ConnectorInvocationActionConfigMaterializationSpec(
                        action_key="fulfill",
                        action_kind="api",
                        target_ref=(
                            "agent.fulfill_action_intent.fulfill_action_intent"
                        ),
                        materialized_action_key=(
                            "agent_actions.actuator.agent_fulfillment.fulfill"
                        ),
                        source_path="connectors/agent_actions.aware",
                    ),
                ),
            ),
        ),
    )


def _music_endpoint_bindings() -> dict[str, object]:
    return {
        "MusicApi.Playback.now_playing": _endpoint_binding(
            endpoint_ref="MusicApi.Playback.now_playing",
            request_type_ref="futurehill.music.NowPlayingRequest",
            response_type_ref="futurehill.music.NowPlayingSnapshot",
        ),
        "MusicApi.Playback.subscribe_now_playing": _endpoint_binding(
            endpoint_ref="MusicApi.Playback.subscribe_now_playing",
            request_type_ref="futurehill.music.NowPlayingSubscribeRequest",
            response_type_ref="futurehill.music.NowPlayingSubscribeResponse",
            stream_event_type_refs=("futurehill.music.NowPlayingEvent",),
        ),
        "MusicApi.Player.play": _endpoint_binding(
            endpoint_ref="MusicApi.Player.play",
            request_type_ref="futurehill.music.PlayTrackRequest",
            response_type_ref="futurehill.music.PlayTrackResult",
        ),
    }


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
    fulfillment_bindings: tuple[object, ...] = (),
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
        fulfillment_bindings=fulfillment_bindings,
    )


def _exec_protocol_module(module_text: str) -> dict[str, object]:
    compiled = compile(module_text, "protocols.py", "exec")
    namespace: dict[str, object] = {}
    exec(compiled, namespace)
    return namespace


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "aware.environment.toml").exists():
            return parent
    raise AssertionError("Could not resolve repository root")


@contextmanager
def _agent_api_python_path() -> Iterator[None]:
    repo_root = _repo_root()
    paths = [
        str(
            repo_root
            / "workspaces"
            / "aware_agent"
            / "modules"
            / "agent"
            / "apis"
            / "agent"
            / "python"
            / "aware_agent_service_protocol"
        ),
        str(
            repo_root
            / "workspaces"
            / "aware_agent"
            / "modules"
            / "agent"
            / "apis"
            / "agent"
            / "python"
            / "aware_agent_service_dto"
        ),
    ]
    old_path = list(sys.path)
    sys.path[:0] = paths
    try:
        yield
    finally:
        sys.path[:] = old_path


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
