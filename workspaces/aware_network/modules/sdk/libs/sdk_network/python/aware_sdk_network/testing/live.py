from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, NoReturn
from uuid import UUID

import pytest

from aware_sdk_network.transport.provider_refs import (
    SdkServiceApiProviderRoute,
    build_api_client_for_api_package,
    endpoint_refs_for_api_package,
    routes_from_provider_refs_payload,
)


__all__ = [
    "LiveSdkEndpointProofRow",
    "build_live_api_client_for_package",
    "close_live_api_client",
    "endpoint_refs_for_api_package",
    "live_sdk_actor_id",
    "live_sdk_api_dependency_routes",
    "live_sdk_provider_refs_path",
]


_LIVE_CONSUMER_NODE_ID = UUID("019e9c01-01ad-7b61-a5ee-1ea536cbb642")
_LIVE_CONSUMER_SERVICE_PACKAGE_ID = UUID("f8a7cd53-f724-5d14-9b6e-6a55daefffe1")
_LIVE_CONSUMER_SERVICE_PACKAGE_NAME = "sdk-live-integration-proof"


@dataclass(frozen=True, slots=True)
class LiveSdkEndpointProofRow:
    endpoint_ref: str
    sdk_method_path: str
    tier: int
    status: str
    reason: str


@pytest.fixture(scope="session")
def live_sdk_provider_refs_path() -> Path:
    raw_path = os.environ.get("AWARE_SDK_LIVE_PROVIDER_REFS_PATH") or os.environ.get(
        "AWARE_SERVICES_PROVIDER_REFS_PATH"
    )
    if not raw_path:
        _fail_live_sdk_config(
            "live Service API provider refs not supplied; set "
            "AWARE_SDK_LIVE_PROVIDER_REFS_PATH"
        )
    path = Path(raw_path).expanduser()
    if not path.is_file():
        _fail_live_sdk_config(
            f"live Service API provider refs path does not exist: {path}"
        )
    return path


@pytest.fixture()
def live_sdk_api_dependency_routes(
    live_sdk_provider_refs_path: Path,
) -> tuple[SdkServiceApiProviderRoute, ...]:
    return routes_from_provider_refs_payload(
        load_json_payload(live_sdk_provider_refs_path),
        consumer_node_id=_LIVE_CONSUMER_NODE_ID,
        consumer_service_package_id=_LIVE_CONSUMER_SERVICE_PACKAGE_ID,
        consumer_service_package_name=_LIVE_CONSUMER_SERVICE_PACKAGE_NAME,
        request_timeout_s=_live_request_timeout_s(),
    )


@pytest.fixture(scope="session")
def live_sdk_actor_id() -> UUID | None:
    raw_actor_id = (os.environ.get("AWARE_SDK_LIVE_ACTOR_ID") or "").strip()
    return UUID(raw_actor_id) if raw_actor_id else None


def build_live_api_client_for_package(
    routes: Sequence[SdkServiceApiProviderRoute],
    *,
    api_package_name: str,
    actor_id: UUID | None = None,
) -> object:
    client = build_api_client_for_api_package(
        routes,
        api_package_name=api_package_name,
        actor_id=actor_id,
    )
    if client is None:
        raise RuntimeError(
            f"Live provider refs do not advertise API package {api_package_name!r}."
        )
    return client


async def close_live_api_client(api_invoker: object) -> None:
    transport = getattr(api_invoker, "transport", None)
    duplex = getattr(transport, "_duplex", None)
    config = getattr(api_invoker, "config", None)
    connection_id = getattr(config, "connection_id", None)
    if duplex is not None and connection_id is not None:
        await duplex.disconnect(connection_id)


def load_json_payload(path: Path) -> Any:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


def _live_request_timeout_s() -> float | None:
    override = (os.environ.get("AWARE_SDK_LIVE_TIMEOUT_S") or "").strip()
    if not override:
        return None
    timeout_s = float(override)
    if timeout_s <= 0:
        raise RuntimeError("Live SDK request timeout must be positive.")
    return timeout_s


def _fail_live_sdk_config(message: str) -> NoReturn:
    pytest.fail(message, pytrace=False)
    raise AssertionError(message)
