"""Network-owned app config defaults for raw comms clients."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from aware_comms.app.config import AppConfig, get_app_config, register_app_config


class _EnvironmentAppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AWARE_ENVIRONMENT_")

    NAME: str = "Aware Environment service"
    PORT: int = 8445
    BASE_URL: str = "http://aware-environment"


class _NetworkNodeAppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AWARE_NODE_")

    NAME: str = "Aware Network Node service"
    PORT: int = 8900
    BASE_URL: str = "http://aware-network-node"


def register_network_app_configs() -> None:
    environment = _EnvironmentAppSettings()
    network_node = _NetworkNodeAppSettings()
    register_app_config(
        "environment",
        AppConfig(
            name=environment.NAME,
            port=environment.PORT,
            base_url=environment.BASE_URL,
        ),
    )
    register_app_config(
        "network_node",
        AppConfig(
            name=network_node.NAME,
            port=network_node.PORT,
            base_url=network_node.BASE_URL,
        ),
    )


def get_network_app_config(app_type: str) -> AppConfig:
    register_network_app_configs()
    return get_app_config(app_type)


register_network_app_configs()


__all__ = ["get_network_app_config", "register_network_app_configs"]
