"""Generic app config registry for raw communications clients."""

from __future__ import annotations

from pydantic import BaseModel


class AppConfig(BaseModel):
    """Connection settings for a routable app endpoint."""

    name: str
    port: int
    base_url: str

    @property
    def full_url(self) -> str:
        return f"{self.base_url}:{self.port}"


_APP_CONFIG: dict[str, AppConfig] = {}


def register_app_config(app_type: str, config: AppConfig) -> None:
    """Register a product-owned app config by route key."""
    _APP_CONFIG[app_type] = config


def get_app_config(app_type: str) -> AppConfig:
    try:
        return _APP_CONFIG[app_type]
    except KeyError as exc:
        raise KeyError(
            f"No aware_comms app config registered for {app_type!r}"
        ) from exc


__all__ = [
    "AppConfig",
    "get_app_config",
    "register_app_config",
]
