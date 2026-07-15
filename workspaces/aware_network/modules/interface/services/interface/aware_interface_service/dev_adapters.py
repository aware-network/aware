from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)

from aware_interface_service.mock_service_adapters import (
    MockIdentityAdmissionServiceAdapter,
    is_mock_service_endpoint,
)

_SUPPORTED_DEV_ADAPTERS = {
    ("identity", "mock"),
    ("network", "mock"),
}


@dataclass(frozen=True, slots=True)
class InterfaceHostDevAdapterSelection:
    service_key: str
    adapter_key: str
    source_kind: str
    adapter: Any
    disables_lane_sync: bool = True
    authenticated: bool = True

    @property
    def interface_id(self) -> UUID | None:
        raw_id = getattr(self.adapter, "interface_id", None)
        return raw_id if isinstance(raw_id, UUID) else None


def interface_host_dev_adapter_selected(
    *,
    endpoint: str | None,
    dev_adapter_specs: Iterable[object] = (),
) -> bool:
    if is_mock_service_endpoint(endpoint):
        return True
    return any(_adapter_key(spec) != "local" for spec in dev_adapter_specs)


def build_interface_host_dev_adapter_selection(
    *,
    endpoint: str,
    dev_adapter_specs: Iterable[object] = (),
    namespace: str,
    host_label: str,
    repository_root: Path,
    state_home: Path,
    interface_config_bundle: InterfaceConfigBundle | None,
) -> InterfaceHostDevAdapterSelection | None:
    if is_mock_service_endpoint(endpoint):
        return _build_identity_mock_selection(
            endpoint=endpoint,
            namespace=namespace,
            host_label=host_label,
            repository_root=repository_root,
            state_home=state_home,
            interface_config_bundle=interface_config_bundle,
            source_kind="endpoint_compat",
        )

    active_specs = tuple(
        spec
        for spec in dev_adapter_specs
        if _adapter_key(spec) != "local"
    )
    if not active_specs:
        return None

    unsupported = tuple(
        spec
        for spec in active_specs
        if (_service_key(spec), _adapter_key(spec)) not in _SUPPORTED_DEV_ADAPTERS
    )
    if unsupported:
        formatted = ", ".join(
            f"{_service_key(spec)}={_adapter_key(spec)}"
            for spec in unsupported
        )
        raise RuntimeError(
            "Unsupported Interface Host dev adapter selection: "
            f"{formatted}. Supported in v0: identity=mock, network=mock."
        )

    return _build_identity_mock_selection(
        endpoint=endpoint,
        namespace=namespace,
        host_label=host_label,
        repository_root=repository_root,
        state_home=state_home,
        interface_config_bundle=interface_config_bundle,
        source_kind="dev_adapter_registry",
        identity_admission_enabled=_has_adapter(
            active_specs,
            service_key="identity",
            adapter_key="mock",
        ),
        network_territory_enabled=_has_adapter(
            active_specs,
            service_key="network",
            adapter_key="mock",
        ),
    )


def _build_identity_mock_selection(
    *,
    endpoint: str,
    namespace: str,
    host_label: str,
    repository_root: Path,
    state_home: Path,
    interface_config_bundle: InterfaceConfigBundle | None,
    source_kind: str,
    identity_admission_enabled: bool = True,
    network_territory_enabled: bool = False,
) -> InterfaceHostDevAdapterSelection:
    return InterfaceHostDevAdapterSelection(
        service_key=("identity" if identity_admission_enabled else "network"),
        adapter_key="mock",
        source_kind=source_kind,
        adapter=MockIdentityAdmissionServiceAdapter(
            namespace=namespace,
            host_label=host_label,
            endpoint=endpoint,
            repository_root=repository_root,
            state_home=state_home,
            interface_config_bundle=interface_config_bundle,
            identity_admission_enabled=identity_admission_enabled,
            network_territory_enabled=network_territory_enabled,
        ),
    )


def _has_adapter(
    specs: Iterable[object],
    *,
    service_key: str,
    adapter_key: str,
) -> bool:
    return any(
        (_service_key(spec), _adapter_key(spec)) == (service_key, adapter_key)
        for spec in specs
    )


def _service_key(spec: object) -> str:
    return _normalized_attr(spec, "service_key")


def _adapter_key(spec: object) -> str:
    return _normalized_attr(spec, "adapter_key")


def _normalized_attr(spec: object, attr: str) -> str:
    value = getattr(spec, attr, None)
    if value is None and isinstance(spec, dict):
        value = spec.get(attr)
    return str(value or "").strip().casefold()


__all__ = [
    "InterfaceHostDevAdapterSelection",
    "build_interface_host_dev_adapter_selection",
    "interface_host_dev_adapter_selected",
]
