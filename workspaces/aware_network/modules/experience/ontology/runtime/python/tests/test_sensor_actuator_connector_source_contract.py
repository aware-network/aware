from __future__ import annotations

from pathlib import Path

from ._experience_runtime_test_paths import REPO_ROOT


def _source_root() -> Path:
    return (
        REPO_ROOT
        / "workspaces"
        / "aware_network"
        / "modules"
        / "experience"
        / "ontology"
        / "structure"
        / "aware"
    )


def test_sensor_actuator_connector_raw_source_contract() -> None:
    root = _source_root()

    expected_files = (
        root / "connector" / "connector_config.aware",
        root / "connector" / "connector_provider.aware",
        root / "connector" / "connector_session.aware",
        root / "connector" / "connector.aware",
        root / "sensor" / "sensor_config.aware",
        root / "sensor" / "sensor_config_state_node.aware",
        root / "sensor" / "sensor.aware",
        root / "sensor" / "sensor_invocation_action_config.aware",
        root / "sensor" / "sensor_invocation_action.aware",
        root / "actuator" / "actuator_config.aware",
        root / "actuator" / "actuator_config_state_node.aware",
        root / "actuator" / "actuator.aware",
        root / "actuator" / "actuator_invocation_action_config.aware",
        root / "actuator" / "actuator_invocation_action.aware",
        root / "connector_config_projection.aware",
        root / "connector_provider_projection.aware",
        root / "connector_session_projection.aware",
        root / "connector_projection.aware",
        root / "sensor_config_projection.aware",
        root / "sensor_projection.aware",
        root / "sensor_invocation_action_config_projection.aware",
        root / "sensor_invocation_action_projection.aware",
        root / "actuator_config_projection.aware",
        root / "actuator_projection.aware",
        root / "actuator_invocation_action_config_projection.aware",
        root / "actuator_invocation_action_projection.aware",
    )
    for path in expected_files:
        assert path.exists(), path

    removed_files = (
        root / "connector" / "experience_connector_config.aware",
        root / "connector" / "experience_connector.aware",
        root / "sensor" / "experience_sensor_config.aware",
        root / "sensor" / "experience_sensor.aware",
        root / "actuator" / "experience_actuator_config.aware",
        root / "actuator" / "experience_actuator.aware",
        root / "experience_connector_config_projection.aware",
        root / "experience_connector_projection.aware",
        root / "experience_sensor_config_projection.aware",
        root / "experience_sensor_projection.aware",
        root / "experience_actuator_config_projection.aware",
        root / "experience_actuator_projection.aware",
    )
    for path in removed_files:
        assert not path.exists(), path

    authored = "\n".join(
        path.read_text(encoding="utf-8")
        for path in root.rglob("*.aware")
        if path.is_file() and "/.aware/" not in str(path)
    )
    assert "ExperienceConnector" not in authored
    assert "ExperienceSensor" not in authored
    assert "ExperienceActuator" not in authored
    assert "experience_connector" not in authored
    assert "experience_sensor" not in authored
    assert "experience_actuator" not in authored
    assert "payload_schema_ref" not in authored

    projection_experience = (
        root / "projection" / "projection_experience.aware"
    ).read_text(encoding="utf-8")
    assert "connector_configs" not in projection_experience
    assert "create_connector_config" not in projection_experience

    connector_config = (root / "connector" / "connector_config.aware").read_text(
        encoding="utf-8",
    )
    assert "class ConnectorConfig" in connector_config
    assert "providers ConnectorProvider[]" in connector_config
    assert "sensor_configs sensor.SensorConfig[]" in connector_config
    assert "actuator_configs actuator.ActuatorConfig[]" in connector_config
    assert "connectors Connector[]" in connector_config
    assert "fn create construct" in connector_config
    assert "fn add_provider" in connector_config
    assert "fn create_connector" in connector_config

    connector_provider = (root / "connector" / "connector_provider.aware").read_text(
        encoding="utf-8"
    )
    assert "class ConnectorProvider" in connector_provider
    assert "sessions ConnectorSession[]" in connector_provider
    assert "provider_key String key" in connector_provider
    assert "provider_kind String" in connector_provider
    assert "fn create_session" in connector_provider

    connector_session = (root / "connector" / "connector_session.aware").read_text(
        encoding="utf-8"
    )
    assert "class ConnectorSession" in connector_session
    assert "connector Connector key" in connector_session
    assert "session_key String key" in connector_session
    assert "host_ref String?" in connector_session
    assert "principal_ref String?" in connector_session

    connector = (root / "connector" / "connector.aware").read_text(
        encoding="utf-8",
    )
    assert "class Connector" in connector
    assert "sensors sensor.Sensor[] many" in connector
    assert "actuators actuator.Actuator[] many" in connector

    sensor_config = (root / "sensor" / "sensor_config.aware").read_text(
        encoding="utf-8",
    )
    assert "invocation_action_configs SensorInvocationActionConfig[]" in sensor_config
    assert "observed_state_nodes SensorConfigStateNode[]" in sensor_config
    assert "fn add_observed_state_node" in sensor_config
    assert "fn bind_invocation_action_config" in sensor_config

    sensor_config_state_node = (
        root / "sensor" / "sensor_config_state_node.aware"
    ).read_text(encoding="utf-8")
    assert "class SensorConfigStateNode" in sensor_config_state_node
    assert (
        "object_projection_graph_node "
        "aware_meta.graph.projection.ObjectProjectionGraphNode key"
    ) in sensor_config_state_node

    sensor_invocation_action_config = (
        root / "sensor" / "sensor_invocation_action_config.aware"
    ).read_text(encoding="utf-8")
    assert (
        "experience_invocation_action_config "
        "invocation.ExperienceInvocationActionConfig key"
    ) in sensor_invocation_action_config
    assert (
        "invocation_actions invocation.ExperienceInvocationAction[]"
        not in sensor_invocation_action_config
    )

    sensor = (root / "sensor" / "sensor.aware").read_text(encoding="utf-8")
    assert "invocation_actions SensorInvocationAction[]" in sensor

    sensor_invocation_action = (
        root / "sensor" / "sensor_invocation_action.aware"
    ).read_text(encoding="utf-8")
    assert (
        "experience_invocation_action invocation.ExperienceInvocationAction key"
        in sensor_invocation_action
    )

    actuator_config = (root / "actuator" / "actuator_config.aware").read_text(
        encoding="utf-8",
    )
    assert (
        "invocation_action_configs ActuatorInvocationActionConfig[]" in actuator_config
    )
    assert "affected_state_nodes ActuatorConfigStateNode[]" in actuator_config
    assert "fn add_affected_state_node" in actuator_config
    assert "fn bind_invocation_action_config" in actuator_config

    actuator_config_state_node = (
        root / "actuator" / "actuator_config_state_node.aware"
    ).read_text(encoding="utf-8")
    assert "class ActuatorConfigStateNode" in actuator_config_state_node
    assert (
        "object_projection_graph_node "
        "aware_meta.graph.projection.ObjectProjectionGraphNode key"
    ) in actuator_config_state_node

    actuator_invocation_action_config = (
        root / "actuator" / "actuator_invocation_action_config.aware"
    ).read_text(encoding="utf-8")
    assert (
        "experience_invocation_action_config "
        "invocation.ExperienceInvocationActionConfig key"
    ) in actuator_invocation_action_config
    assert (
        "invocation_actions invocation.ExperienceInvocationAction[]"
        not in actuator_invocation_action_config
    )

    actuator = (root / "actuator" / "actuator.aware").read_text(
        encoding="utf-8",
    )
    assert "invocation_actions ActuatorInvocationAction[]" in actuator

    actuator_invocation_action = (
        root / "actuator" / "actuator_invocation_action.aware"
    ).read_text(encoding="utf-8")
    assert (
        "experience_invocation_action invocation.ExperienceInvocationAction key"
        in actuator_invocation_action
    )

    connector_projection = (root / "connector_projection.aware").read_text(
        encoding="utf-8",
    )
    assert "projection Connector" in connector_projection
    assert "connector.Connector::sensors Sensor" in connector_projection
    assert "connector.Connector::actuators Actuator" in connector_projection

    connector_config_projection = (
        root / "connector_config_projection.aware"
    ).read_text(encoding="utf-8")
    assert (
        "connector.ConnectorConfig::providers ConnectorProvider"
        in connector_config_projection
    )

    connector_provider_projection = (
        root / "connector_provider_projection.aware"
    ).read_text(encoding="utf-8")
    assert "projection ConnectorProvider" in connector_provider_projection
    assert (
        "connector.ConnectorProvider::sessions ConnectorSession"
        in connector_provider_projection
    )

    connector_session_projection = (
        root / "connector_session_projection.aware"
    ).read_text(encoding="utf-8")
    assert "projection ConnectorSession" in connector_session_projection
    assert (
        "connector.ConnectorSession::connector Connector"
        in connector_session_projection
    )

    sensor_invocation_action_config_projection = (
        root / "sensor_invocation_action_config_projection.aware"
    ).read_text(encoding="utf-8")
    assert (
        "projection SensorInvocationActionConfig"
        in sensor_invocation_action_config_projection
    )
    assert (
        "sensor.SensorInvocationActionConfig::experience_invocation_action_config "
        "ExperienceInvocationActionConfig"
    ) in sensor_invocation_action_config_projection
    assert (
        "sensor.SensorInvocationActionConfig::invocation_actions "
        "ExperienceInvocationAction"
    ) not in sensor_invocation_action_config_projection

    sensor_config_projection = (root / "sensor_config_projection.aware").read_text(
        encoding="utf-8"
    )
    assert "sensor.SensorConfig::observed_state_nodes" in sensor_config_projection
    assert (
        "sensor.SensorConfigStateNode::object_projection_graph_node "
        "aware_meta.ObjectProjectionGraph"
    ) in sensor_config_projection

    sensor_invocation_action_projection = (
        root / "sensor_invocation_action_projection.aware"
    ).read_text(
        encoding="utf-8",
    )
    assert "projection SensorInvocationAction" in sensor_invocation_action_projection
    assert (
        "sensor.SensorInvocationAction::sensor_invocation_action_config "
        "SensorInvocationActionConfig"
    ) in sensor_invocation_action_projection
    assert (
        "sensor.SensorInvocationAction::experience_invocation_action "
        "ExperienceInvocationAction"
    ) in sensor_invocation_action_projection

    actuator_invocation_action_config_projection = (
        root / "actuator_invocation_action_config_projection.aware"
    ).read_text(encoding="utf-8")
    assert (
        "projection ActuatorInvocationActionConfig"
        in actuator_invocation_action_config_projection
    )
    assert (
        "actuator.ActuatorInvocationActionConfig::experience_invocation_action_config "
        "ExperienceInvocationActionConfig"
    ) in actuator_invocation_action_config_projection
    assert (
        "actuator.ActuatorInvocationActionConfig::invocation_actions "
        "ExperienceInvocationAction"
    ) not in actuator_invocation_action_config_projection

    actuator_config_projection = (root / "actuator_config_projection.aware").read_text(
        encoding="utf-8"
    )
    assert "actuator.ActuatorConfig::affected_state_nodes" in actuator_config_projection
    assert (
        "actuator.ActuatorConfigStateNode::object_projection_graph_node "
        "aware_meta.ObjectProjectionGraph"
    ) in actuator_config_projection

    actuator_invocation_action_projection = (
        root / "actuator_invocation_action_projection.aware"
    ).read_text(encoding="utf-8")
    assert (
        "projection ActuatorInvocationAction" in actuator_invocation_action_projection
    )
    assert (
        "actuator.ActuatorInvocationAction::actuator_invocation_action_config "
        "ActuatorInvocationActionConfig"
    ) in actuator_invocation_action_projection
    assert (
        "actuator.ActuatorInvocationAction::experience_invocation_action "
        "ExperienceInvocationAction"
    ) in actuator_invocation_action_projection
