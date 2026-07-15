from __future__ import annotations

from pathlib import Path
import sys
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_experience.handlers.impl.actuator import actuator as actuator_handler
from aware_experience.handlers.impl.actuator import (
    actuator_config as actuator_config_handler,
)
from aware_experience.handlers.impl.actuator import (
    actuator_config_state_node as actuator_config_state_node_handler,
)
from aware_experience.handlers.impl.actuator import (
    actuator_invocation_action as actuator_invocation_action_handler,
)
from aware_experience.handlers.impl.actuator import (
    actuator_invocation_action_config as actuator_invocation_action_config_handler,
)
from aware_experience.handlers.impl.connector import connector as connector_handler
from aware_experience.handlers.impl.connector import (
    connector_config as connector_config_handler,
)
from aware_experience.handlers.impl.connector import (
    connector_provider as connector_provider_handler,
)
from aware_experience.handlers.impl.connector import (
    connector_session as connector_session_handler,
)
from aware_experience.handlers.impl.sensor import sensor as sensor_handler
from aware_experience.handlers.impl.sensor import sensor_config as sensor_config_handler
from aware_experience.handlers.impl.sensor import (
    sensor_config_state_node as sensor_config_state_node_handler,
)
from aware_experience.handlers.impl.sensor import (
    sensor_invocation_action as sensor_invocation_action_handler,
)
from aware_experience.handlers.impl.sensor import (
    sensor_invocation_action_config as sensor_invocation_action_config_handler,
)
from aware_experience.stable_ids import (
    stable_actuator_config_state_node_id,
    stable_actuator_invocation_action_id,
    stable_connector_config_id,
    stable_sensor_config_state_node_id,
    stable_sensor_invocation_action_config_id,
    stable_sensor_invocation_action_id,
)
from aware_experience_ontology.invocation.experience_invocation_action import (
    ExperienceInvocationAction,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.testing import (
    MetaOIGAssertions,
    materialize_meta_runtime_lane_head,
)
from ._experience_runtime_test_paths import REPO_ROOT

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.append(str(_TESTS_DIR))

from .test_experience_projection_view_invocation_action_meta_runtime import (  # noqa: E402
    IsolatedMetaAwareRoot,
    _build_experience_meta_runtime,
    _expect_uuid_primitive,
)


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, UUID(str(value_id))))


def _install_sessions(monkeypatch: pytest.MonkeyPatch, session: _Session) -> None:
    for module in (
        connector_config_handler,
        connector_handler,
        connector_provider_handler,
        connector_session_handler,
        sensor_config_handler,
        sensor_config_state_node_handler,
        sensor_handler,
        sensor_invocation_action_config_handler,
        sensor_invocation_action_handler,
        actuator_config_handler,
        actuator_config_state_node_handler,
        actuator_handler,
        actuator_invocation_action_config_handler,
        actuator_invocation_action_handler,
    ):
        monkeypatch.setattr(module, "current_handler_session", lambda: session)


def _install_direct_constructors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        connector_config_handler.ConnectorProvider,
        "build_via_connector_config",
        connector_provider_handler.build_via_connector_config,
    )
    monkeypatch.setattr(
        connector_config_handler.SensorConfig,
        "build_via_connector_config",
        sensor_config_handler.build_via_connector_config,
    )
    monkeypatch.setattr(
        connector_config_handler.ActuatorConfig,
        "build_via_connector_config",
        actuator_config_handler.build_via_connector_config,
    )
    monkeypatch.setattr(
        connector_config_handler.Connector,
        "build_via_connector_config",
        connector_handler.build_via_connector_config,
    )
    monkeypatch.setattr(
        connector_provider_handler.ConnectorSession,
        "build_via_connector_provider",
        connector_session_handler.build_via_connector_provider,
    )
    monkeypatch.setattr(
        sensor_config_handler.Sensor,
        "build_via_sensor_config",
        sensor_handler.build_via_sensor_config,
    )
    monkeypatch.setattr(
        sensor_config_handler.SensorInvocationActionConfig,
        "build_via_sensor_config",
        sensor_invocation_action_config_handler.build_via_sensor_config,
    )
    monkeypatch.setattr(
        sensor_config_handler.SensorConfigStateNode,
        "build_via_sensor_config",
        sensor_config_state_node_handler.build_via_sensor_config,
    )
    monkeypatch.setattr(
        actuator_config_handler.Actuator,
        "build_via_actuator_config",
        actuator_handler.build_via_actuator_config,
    )
    monkeypatch.setattr(
        actuator_config_handler.ActuatorInvocationActionConfig,
        "build_via_actuator_config",
        actuator_invocation_action_config_handler.build_via_actuator_config,
    )
    monkeypatch.setattr(
        actuator_config_handler.ActuatorConfigStateNode,
        "build_via_actuator_config",
        actuator_config_state_node_handler.build_via_actuator_config,
    )


def _projection_state_nodes(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> tuple[ObjectProjectionGraphNode, ObjectProjectionGraphNode]:
    opg = next(
        opg
        for opg in index.opg_by_hash.values()
        if (opg.name or "").strip() == projection_name
    )
    nodes = [
        node
        for node in opg.object_projection_graph_nodes
        if node.class_config_id in index.class_configs_by_id
    ]
    if len(nodes) < 2:
        raise AssertionError(
            f"Expected at least two projection nodes for {projection_name!r}"
        )
    return cast(ObjectProjectionGraphNode, nodes[0]), cast(
        ObjectProjectionGraphNode,
        nodes[1],
    )


def _node_class_name(
    *,
    index: MetaGraphRuntimeIndex,
    node: ObjectProjectionGraphNode,
) -> str:
    class_config = index.class_configs_by_id.get(node.class_config_id)
    if class_config is None or not class_config.name:
        raise AssertionError(f"Projection node {node.id} has no ClassConfig")
    return class_config.name


@pytest.mark.asyncio
async def test_connector_config_handlers_create_deterministic_config_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    _install_sessions(monkeypatch, session)
    _install_direct_constructors(monkeypatch)

    connector_config = await connector_config_handler.create(
        connector_key=" music ",
        connector_kind=" media ",
        label=" Music ",
    )
    session.put(connector_config)

    assert connector_config.id == stable_connector_config_id(connector_key="music")
    assert connector_config.connector_key == "music"
    assert connector_config.connector_kind == "media"
    assert connector_config.label == "Music"

    provider = await connector_config_handler.add_provider(
        connector_config,
        provider_key=" youtube_music ",
        provider_kind=" streaming ",
        provider_ref=" youtube.music ",
    )
    session.put(provider)
    provider_again = await connector_config_handler.add_provider(
        connector_config,
        provider_key="youtube_music",
        provider_kind="streaming",
        provider_ref="youtube.music",
    )

    assert provider_again is provider
    assert len(connector_config.providers) == 1
    assert provider.connector_config_id == connector_config.id

    sensor_config = await connector_config_handler.add_sensor_config(
        connector_config,
        sensor_key=" now_playing ",
        sensor_kind=" media_state ",
        source_ref=" youtube.now_playing ",
    )
    actuator_config = await connector_config_handler.add_actuator_config(
        connector_config,
        actuator_key=" play_track ",
        actuator_kind=" media_control ",
        target_ref=" youtube.play ",
    )
    state_node_a = ObjectProjectionGraphNode.model_construct(id=uuid4())
    state_node_b = ObjectProjectionGraphNode.model_construct(id=uuid4())
    session.put(state_node_a)
    session.put(state_node_b)
    observed_a = await sensor_config_handler.add_observed_state_node(
        sensor_config,
        object_projection_graph_node_id=state_node_a.id,
    )
    observed_b = await sensor_config_handler.add_observed_state_node(
        sensor_config,
        object_projection_graph_node_id=state_node_b.id,
    )
    affected_a = await actuator_config_handler.add_affected_state_node(
        actuator_config,
        object_projection_graph_node_id=state_node_a.id,
    )
    affected_b = await actuator_config_handler.add_affected_state_node(
        actuator_config,
        object_projection_graph_node_id=state_node_b.id,
    )
    connector = await connector_config_handler.create_connector(
        connector_config,
        connector_instance_key=" clinic-main ",
        runtime_ref=" host:clinic ",
    )

    assert sensor_config.connector_config_id == connector_config.id
    assert actuator_config.connector_config_id == connector_config.id
    assert connector.connector_config_id == connector_config.id
    assert connector_config.sensor_configs == [sensor_config]
    assert connector_config.actuator_configs == [actuator_config]
    assert sensor_config.observed_state_nodes == [observed_a, observed_b]
    assert actuator_config.affected_state_nodes == [affected_a, affected_b]
    assert observed_a.id == stable_sensor_config_state_node_id(
        sensor_config_id=sensor_config.id,
        object_projection_graph_node_id=state_node_a.id,
    )
    assert observed_a.object_projection_graph_node is state_node_a
    assert observed_b.id == stable_sensor_config_state_node_id(
        sensor_config_id=sensor_config.id,
        object_projection_graph_node_id=state_node_b.id,
    )
    assert affected_a.id == stable_actuator_config_state_node_id(
        actuator_config_id=actuator_config.id,
        object_projection_graph_node_id=state_node_a.id,
    )
    assert affected_a.object_projection_graph_node is state_node_a
    assert affected_b.id == stable_actuator_config_state_node_id(
        actuator_config_id=actuator_config.id,
        object_projection_graph_node_id=state_node_b.id,
    )
    assert connector_config.connectors == [connector]


@pytest.mark.asyncio
async def test_sensor_actuator_state_node_footprint_commits_projection_node_refs(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_experience_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.actuator.actuator_config import ActuatorConfig
    from aware_experience_ontology.sensor.sensor_config import SensorConfig

    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/sensor-actuator-state-node-footprint/v1",
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = cast(MetaGraphRuntimeIndex, context.index)
        state_node_a, state_node_b = _projection_state_nodes(
            index=index,
            projection_name="ProjectionExperience",
        )
        state_node_a_class_name = _node_class_name(index=index, node=state_node_a)
        state_node_b_class_name = _node_class_name(index=index, node=state_node_b)

        connector_config_id = uuid5(ns, "connector_config")
        sensor_lane = runtime.bind(
            projection="SensorConfig",
            branch_id=uuid5(ns, "sensor_branch"),
        )
        with sensor_lane.activate(commit=True, publish=False):
            sensor_config = await SensorConfig.build_via_connector_config(
                connector_config_id=connector_config_id,
                sensor_key="now_playing",
                sensor_kind="media_state",
            )
        with sensor_lane.activate(commit=True, publish=False):
            observed_a = await sensor_config.add_observed_state_node(
                object_projection_graph_node_id=state_node_a.id,
            )
            observed_b = await sensor_config.add_observed_state_node(
                object_projection_graph_node_id=state_node_b.id,
            )
        assert sensor_lane.last_response is not None
        assert sensor_lane.last_response.commit_id is not None
        sensor_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=sensor_lane,
        )

        actuator_lane = runtime.bind(
            projection="ActuatorConfig",
            branch_id=uuid5(ns, "actuator_branch"),
        )
        with actuator_lane.activate(commit=True, publish=False):
            actuator_config = await ActuatorConfig.build_via_connector_config(
                connector_config_id=connector_config_id,
                actuator_key="play_track",
                actuator_kind="media_control",
            )
        with actuator_lane.activate(commit=True, publish=False):
            affected_a = await actuator_config.add_affected_state_node(
                object_projection_graph_node_id=state_node_a.id,
            )
            affected_b = await actuator_config.add_affected_state_node(
                object_projection_graph_node_id=state_node_b.id,
            )
        assert actuator_lane.last_response is not None
        assert actuator_lane.last_response.commit_id is not None
        actuator_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=actuator_lane,
        )

    sensor_assertions = MetaOIGAssertions(oig=sensor_oig, index=index)
    sensor_assertions.expect_root(sensor_config.id)
    for instance_id in (
        sensor_config.id,
        observed_a.id,
        observed_b.id,
    ):
        sensor_assertions.expect_instance(instance_id)
    sensor_assertions.expect_edge(
        source_id=sensor_config.id,
        target_id=observed_a.id,
        relationship_name="observed_state_nodes",
    )
    sensor_assertions.expect_edge(
        source_id=sensor_config.id,
        target_id=observed_b.id,
        relationship_name="observed_state_nodes",
    )
    _expect_uuid_primitive(
        sensor_assertions,
        instance_id=observed_a.id,
        field_name="sensor_config_id",
        expected=sensor_config.id,
    )
    _expect_uuid_primitive(
        sensor_assertions,
        instance_id=observed_a.id,
        field_name="object_projection_graph_node_id",
        expected=state_node_a.id,
    )
    _expect_uuid_primitive(
        sensor_assertions,
        instance_id=observed_b.id,
        field_name="object_projection_graph_node_id",
        expected=state_node_b.id,
    )

    actuator_assertions = MetaOIGAssertions(oig=actuator_oig, index=index)
    actuator_assertions.expect_root(actuator_config.id)
    for instance_id in (
        actuator_config.id,
        affected_a.id,
        affected_b.id,
    ):
        actuator_assertions.expect_instance(instance_id)
    actuator_assertions.expect_edge(
        source_id=actuator_config.id,
        target_id=affected_a.id,
        relationship_name="affected_state_nodes",
    )
    actuator_assertions.expect_edge(
        source_id=actuator_config.id,
        target_id=affected_b.id,
        relationship_name="affected_state_nodes",
    )
    _expect_uuid_primitive(
        actuator_assertions,
        instance_id=affected_a.id,
        field_name="actuator_config_id",
        expected=actuator_config.id,
    )
    _expect_uuid_primitive(
        actuator_assertions,
        instance_id=affected_a.id,
        field_name="object_projection_graph_node_id",
        expected=state_node_a.id,
    )
    _expect_uuid_primitive(
        actuator_assertions,
        instance_id=affected_b.id,
        field_name="object_projection_graph_node_id",
        expected=state_node_b.id,
    )
    assert observed_a.id == stable_sensor_config_state_node_id(
        sensor_config_id=sensor_config.id,
        object_projection_graph_node_id=state_node_a.id,
    )
    assert affected_a.id == stable_actuator_config_state_node_id(
        actuator_config_id=actuator_config.id,
        object_projection_graph_node_id=state_node_a.id,
    )
    assert state_node_a_class_name
    assert state_node_b_class_name
    assert "payload_schema_ref" not in {
        attribute_name
        for class_config in index.class_configs_by_id.values()
        for link in class_config.class_config_attribute_configs
        for attribute_name in [link.attribute_config.name]
    }


@pytest.mark.asyncio
async def test_sensor_actuator_invocation_bridges_bind_existing_action_receipts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    _install_sessions(monkeypatch, session)
    _install_direct_constructors(monkeypatch)

    connector_config = await connector_config_handler.create(
        connector_key="music",
        connector_kind="media",
    )
    sensor_config = await connector_config_handler.add_sensor_config(
        connector_config,
        sensor_key="now_playing",
        sensor_kind="media_state",
    )
    actuator_config = await connector_config_handler.add_actuator_config(
        connector_config,
        actuator_key="play_track",
        actuator_kind="media_control",
    )
    sensor = await sensor_config_handler.create_sensor(
        sensor_config,
        sensor_instance_key="clinic-main",
    )
    actuator = await actuator_config_handler.create_actuator(
        actuator_config,
        actuator_instance_key="clinic-main",
    )

    experience_action_config = ExperienceInvocationActionConfig.model_construct(
        id=uuid4(),
    )
    experience_action = ExperienceInvocationAction.model_construct(id=uuid4())
    session.put(experience_action_config)
    session.put(experience_action)

    sensor_binding = await sensor_config_handler.bind_invocation_action_config(
        sensor_config,
        experience_invocation_action_config_id=experience_action_config.id,
    )
    actuator_binding = await actuator_config_handler.bind_invocation_action_config(
        actuator_config,
        experience_invocation_action_config_id=experience_action_config.id,
    )

    assert sensor_binding.id == stable_sensor_invocation_action_config_id(
        sensor_config_id=sensor_config.id,
        experience_invocation_action_config_id=experience_action_config.id,
    )
    assert sensor_binding.experience_invocation_action_config is (
        experience_action_config
    )
    assert actuator_binding.experience_invocation_action_config is (
        experience_action_config
    )

    sensor_action = await sensor_invocation_action_handler.build(
        sensor_id=sensor.id,
        sensor_invocation_action_config_id=sensor_binding.id,
        experience_invocation_action_id=experience_action.id,
    )
    actuator_action = await actuator_invocation_action_handler.build(
        actuator_id=actuator.id,
        actuator_invocation_action_config_id=actuator_binding.id,
        experience_invocation_action_id=experience_action.id,
    )

    assert sensor_action.id == stable_sensor_invocation_action_id(
        sensor_invocation_action_config_id=sensor_binding.id,
        experience_invocation_action_id=experience_action.id,
    )
    assert sensor_action.experience_invocation_action is experience_action
    assert actuator_action.id == stable_actuator_invocation_action_id(
        actuator_invocation_action_config_id=actuator_binding.id,
        experience_invocation_action_id=experience_action.id,
    )
    assert actuator_action.experience_invocation_action is experience_action

    with pytest.raises(
        RuntimeError, match="cannot construct ExperienceInvocationAction"
    ):
        await sensor_invocation_action_config_handler.record_invocation(
            sensor_binding,
            invocation_key=uuid4(),
        )
    with pytest.raises(
        RuntimeError, match="cannot construct ExperienceInvocationAction"
    ):
        await actuator_invocation_action_config_handler.record_invocation(
            actuator_binding,
            invocation_key=uuid4(),
        )
