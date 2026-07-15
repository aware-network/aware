from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Experience Ontology
from aware_experience_ontology.actuator.actuator_config import ActuatorConfig
from aware_experience_ontology.connector.connector import Connector
from aware_experience_ontology.connector.connector_config import ConnectorConfig
from aware_experience_ontology.connector.connector_provider import ConnectorProvider
from aware_experience_ontology.sensor.sensor_config import SensorConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    ensure_existing_payload,
    optional_token,
    required_token,
    status_token,
)
from aware_experience.stable_ids import stable_connector_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(
    connector_key: str, connector_kind: str, label: str | None = None, description: str | None = None
) -> ConnectorConfig:
    """
    Create one canonical Connector config root.

    Contract:
    - `connector_key` is the stable service-facing config key.
    - `connector_kind` identifies the integration family.
    - The config is not scoped to a ProjectionExperience.
    """

    # --- AWARE: LOGIC START create
    normalized_connector_key = required_token(
        connector_key,
        field_name="ConnectorConfig.connector_key",
    )
    normalized_connector_kind = required_token(
        connector_kind,
        field_name="ConnectorConfig.connector_kind",
    )
    normalized_label = optional_token(label)
    normalized_description = optional_token(description)
    connector_config_id = stable_connector_config_id(
        connector_key=normalized_connector_key,
    )

    session = current_handler_session()
    existing = session.imap_get(ConnectorConfig, connector_config_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "connector_key": normalized_connector_key,
                "connector_kind": normalized_connector_kind,
                "label": normalized_label,
                "description": normalized_description,
            },
            label="ConnectorConfig",
            object_id=connector_config_id,
        )
        return existing

    return ConnectorConfig(
        id=connector_config_id,
        connector_key=normalized_connector_key,
        connector_kind=normalized_connector_kind,
        label=normalized_label,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END create


async def add_provider(
    connector_config: ConnectorConfig,
    provider_key: str,
    provider_kind: str,
    provider_ref: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> ConnectorProvider:
    """
    Add one provider config under this Connector config.

    Contract:
    - `ConnectorConfig` is the capability family, e.g. music.
    - `ConnectorProvider` is the concrete external provider, e.g.
      youtube_music or spotify.
    - Runtime session identity is owned by `ConnectorSession`, not the
      reusable provider config.
    """

    # --- AWARE: LOGIC START add_provider
    created = await ConnectorProvider.build_via_connector_config(
        connector_config_id=connector_config.id,
        provider_key=provider_key,
        provider_kind=provider_kind,
        provider_ref=provider_ref,
        label=label,
        description=description,
    )
    for existing in connector_config.providers:
        if existing.id == created.id:
            return existing
    connector_config.providers.append(created)
    return created
    # --- AWARE: LOGIC END add_provider


async def add_sensor_config(
    connector_config: ConnectorConfig,
    sensor_key: str,
    sensor_kind: str,
    source_ref: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> SensorConfig:
    """
    Add one Sensor config to this Connector config.

    Contract:
    - Sensors model inbound external information observed by this connector.
    - `source_ref` is a deferred adapter-facing instance hint.
    - Projection-node footprint is declared under SensorConfig state nodes.
    """

    # --- AWARE: LOGIC START add_sensor_config
    created = await SensorConfig.build_via_connector_config(
        connector_config_id=connector_config.id,
        sensor_key=sensor_key,
        sensor_kind=sensor_kind,
        source_ref=source_ref,
        label=label,
        description=description,
    )
    for existing in connector_config.sensor_configs:
        if existing.id == created.id:
            return existing
    connector_config.sensor_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_sensor_config


async def add_actuator_config(
    connector_config: ConnectorConfig,
    actuator_key: str,
    actuator_kind: str,
    target_ref: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> ActuatorConfig:
    """
    Add one Actuator config to this Connector config.

    Contract:
    - Actuators model outbound actions this connector can perform.
    - `target_ref` is a deferred adapter-facing instance hint.
    - Projection-node footprint is declared under ActuatorConfig state nodes.
    """

    # --- AWARE: LOGIC START add_actuator_config
    created = await ActuatorConfig.build_via_connector_config(
        connector_config_id=connector_config.id,
        actuator_key=actuator_key,
        actuator_kind=actuator_kind,
        target_ref=target_ref,
        label=label,
        description=description,
    )
    for existing in connector_config.actuator_configs:
        if existing.id == created.id:
            return existing
    connector_config.actuator_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_actuator_config


async def create_connector(
    connector_config: ConnectorConfig,
    connector_instance_key: str,
    runtime_ref: str | None = None,
    status: str = "active",
) -> Connector:
    """
    Create one deterministic Connector instance under this Connector config.

    Contract:
    - Config -> Instance is the canonical ownership rail.
    - Parent `ConnectorConfig` scope is propagated by constructor lowering.
    - `connector_instance_key` identifies this runtime fulfillment.
    """

    # --- AWARE: LOGIC START create_connector
    normalized_status = status_token(status, default="active")
    created = await Connector.build_via_connector_config(
        connector_config_id=connector_config.id,
        connector_instance_key=connector_instance_key,
        runtime_ref=runtime_ref,
        status=normalized_status,
    )
    for existing in connector_config.connectors:
        if existing.id == created.id:
            return existing
    connector_config.connectors.append(created)
    return created
    # --- AWARE: LOGIC END create_connector
