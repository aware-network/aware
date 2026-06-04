# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical event render catalog (phase-1 registry rail).
from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict


class EventRenderCatalogEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_config_id: str
    event_name: str
    renderer_key: str
    title: str
    description: str
    projection_name: str | None
    class_name: str | None
    operation: str | None
    attribute_name: str | None


EVENT_RENDER_CATALOG: Final[tuple[EventRenderCatalogEntry, ...]] = ()

EVENT_RENDER_CATALOG_BY_EVENT_CONFIG_ID: Final[dict[str, EventRenderCatalogEntry]] = {
    entry.event_config_id: entry for entry in EVENT_RENDER_CATALOG
}

EVENT_RENDER_CATALOG_BY_EVENT_NAME: Final[dict[str, EventRenderCatalogEntry]] = {
    entry.event_name: entry for entry in EVENT_RENDER_CATALOG
}


def event_render_catalog_payload() -> list[dict[str, str | None]]:
    return [entry.model_dump(mode="json") for entry in EVENT_RENDER_CATALOG]


__all__ = [
    "EventRenderCatalogEntry",
    "EVENT_RENDER_CATALOG",
    "EVENT_RENDER_CATALOG_BY_EVENT_CONFIG_ID",
    "EVENT_RENDER_CATALOG_BY_EVENT_NAME",
    "event_render_catalog_payload",
]
