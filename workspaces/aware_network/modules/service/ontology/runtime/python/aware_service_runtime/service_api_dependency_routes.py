from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import UUID


class ServiceApiDependencyRouteKind(str, Enum):
    """Transport kinds for resolved service-to-service API dependencies."""

    LOCAL_SERVICE_HOST_IPC = "local_service_host_ipc"
    REMOTE_NODE_API_ENDPOINT = "remote_node_api_endpoint"


ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY = "ontology_authority_catalog"
ONTOLOGY_AUTHORITY_CATALOG_SCHEMA = "aware.ontology_authority_catalog.v1"


@dataclass(frozen=True, slots=True)
class ServiceApiRouteAuthority:
    """Shared authority metadata for a resolved Service API route."""

    provider_set_id: str | None = None
    workspace_revision_id: UUID | None = None
    workspace_deployment_revision_id: str | None = None
    workspace_deployment_channel: str | None = None
    workspace_deployment_artifact_key: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not any(
            (
                _clean_optional_str(self.provider_set_id),
                self.workspace_revision_id,
                _clean_optional_str(self.workspace_deployment_revision_id),
                _clean_optional_str(self.workspace_deployment_channel),
                _clean_optional_str(self.workspace_deployment_artifact_key),
                self.metadata,
            )
        )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        provider_set_id = _clean_optional_str(self.provider_set_id)
        if provider_set_id is not None:
            payload["provider_set_id"] = provider_set_id
        if self.workspace_revision_id is not None:
            payload["workspace_revision_id"] = str(self.workspace_revision_id)
        deployment_revision_id = _clean_optional_str(
            self.workspace_deployment_revision_id
        )
        if deployment_revision_id is not None:
            payload["workspace_deployment_revision_id"] = deployment_revision_id
        deployment_channel = _clean_optional_str(self.workspace_deployment_channel)
        if deployment_channel is not None:
            payload["workspace_deployment_channel"] = deployment_channel
        deployment_artifact_key = _clean_optional_str(
            self.workspace_deployment_artifact_key
        )
        if deployment_artifact_key is not None:
            payload["workspace_deployment_artifact_key"] = deployment_artifact_key
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "ServiceApiRouteAuthority":
        if not isinstance(payload, Mapping):
            raise RuntimeError("Service API route authority payload must be an object.")
        metadata = payload.get("metadata")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise RuntimeError(
                "Service API route authority metadata must be an object."
            )
        return cls(
            provider_set_id=_optional_str(payload, "provider_set_id"),
            workspace_revision_id=_optional_uuid(payload, "workspace_revision_id"),
            workspace_deployment_revision_id=_optional_str(
                payload,
                "workspace_deployment_revision_id",
            ),
            workspace_deployment_channel=_optional_str(
                payload,
                "workspace_deployment_channel",
            ),
            workspace_deployment_artifact_key=_optional_str(
                payload,
                "workspace_deployment_artifact_key",
            ),
            metadata=dict(metadata) if isinstance(metadata, Mapping) else {},
        )


@dataclass(frozen=True, slots=True)
class ServiceApiRouteAuthoritySelector:
    """Exact selector for authority-aware Service API route resolution."""

    provider_set_id: str | None = None
    workspace_revision_id: UUID | None = None
    workspace_deployment_revision_id: str | None = None
    workspace_deployment_channel: str | None = None
    workspace_deployment_artifact_key: str | None = None

    @property
    def is_empty(self) -> bool:
        return not any(
            (
                _clean_optional_str(self.provider_set_id),
                self.workspace_revision_id,
                _clean_optional_str(self.workspace_deployment_revision_id),
                _clean_optional_str(self.workspace_deployment_channel),
                _clean_optional_str(self.workspace_deployment_artifact_key),
            )
        )

    def matches(self, authority: ServiceApiRouteAuthority | None) -> bool:
        if self.is_empty:
            return True
        if authority is None:
            return False
        if not _optional_token_match(
            expected=self.provider_set_id,
            actual=authority.provider_set_id,
        ):
            return False
        if (
            self.workspace_revision_id is not None
            and authority.workspace_revision_id != self.workspace_revision_id
        ):
            return False
        if not _optional_token_match(
            expected=self.workspace_deployment_revision_id,
            actual=authority.workspace_deployment_revision_id,
        ):
            return False
        if not _optional_token_match(
            expected=self.workspace_deployment_channel,
            actual=authority.workspace_deployment_channel,
        ):
            return False
        if not _optional_token_match(
            expected=self.workspace_deployment_artifact_key,
            actual=authority.workspace_deployment_artifact_key,
        ):
            return False
        return True

    def describe(self) -> str:
        fields: list[str] = []
        if _clean_optional_str(self.provider_set_id):
            fields.append(f"provider_set_id={self.provider_set_id!r}")
        if self.workspace_revision_id is not None:
            fields.append(f"workspace_revision_id={self.workspace_revision_id}")
        if _clean_optional_str(self.workspace_deployment_revision_id):
            fields.append(
                "workspace_deployment_revision_id="
                f"{self.workspace_deployment_revision_id!r}"
            )
        if _clean_optional_str(self.workspace_deployment_channel):
            fields.append(
                "workspace_deployment_channel=" f"{self.workspace_deployment_channel!r}"
            )
        if _clean_optional_str(self.workspace_deployment_artifact_key):
            fields.append(
                "workspace_deployment_artifact_key="
                f"{self.workspace_deployment_artifact_key!r}"
            )
        return ", ".join(fields) if fields else "empty selector"

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        provider_set_id = _clean_optional_str(self.provider_set_id)
        if provider_set_id is not None:
            payload["provider_set_id"] = provider_set_id
        if self.workspace_revision_id is not None:
            payload["workspace_revision_id"] = str(self.workspace_revision_id)
        deployment_revision_id = _clean_optional_str(
            self.workspace_deployment_revision_id
        )
        if deployment_revision_id is not None:
            payload["workspace_deployment_revision_id"] = deployment_revision_id
        deployment_channel = _clean_optional_str(self.workspace_deployment_channel)
        if deployment_channel is not None:
            payload["workspace_deployment_channel"] = deployment_channel
        deployment_artifact_key = _clean_optional_str(
            self.workspace_deployment_artifact_key
        )
        if deployment_artifact_key is not None:
            payload["workspace_deployment_artifact_key"] = deployment_artifact_key
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "ServiceApiRouteAuthoritySelector":
        if not isinstance(payload, Mapping):
            raise RuntimeError(
                "Service API route authority selector payload must be an object."
            )
        return cls(
            provider_set_id=_optional_str(payload, "provider_set_id"),
            workspace_revision_id=_optional_uuid(payload, "workspace_revision_id"),
            workspace_deployment_revision_id=_optional_str(
                payload,
                "workspace_deployment_revision_id",
            ),
            workspace_deployment_channel=_optional_str(
                payload,
                "workspace_deployment_channel",
            ),
            workspace_deployment_artifact_key=_optional_str(
                payload,
                "workspace_deployment_artifact_key",
            ),
        )


@dataclass(frozen=True, slots=True)
class ServiceApiDependencyRouteDescriptor:
    """Serializable route from one ServicePackage API requirement to a provider."""

    consumer_service_package_id: UUID
    consumer_service_package_name: str
    provider_service_package_id: UUID
    provider_service_package_name: str
    api_package_id: UUID
    api_package_name: str | None
    route_kind: ServiceApiDependencyRouteKind
    host_id: str
    host_version: str | None
    protocol_version: str
    socket_path: Path | None
    request_timeout_s: float
    service_names: tuple[str, ...]
    consumer_node_id: UUID | None = None
    provider_node_id: UUID | None = None
    provider_node_base_url: str | None = None
    route_connection_id: UUID | None = None
    endpoint_refs_by_service: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict
    )
    stream_endpoint_refs_by_service: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict
    )
    authority: ServiceApiRouteAuthority | None = None

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-compatible payload for host config/deployment handoff."""

        self._validate_route_transport()
        payload: dict[str, object] = {
            "consumer_service_package_id": str(self.consumer_service_package_id),
            "consumer_service_package_name": self.consumer_service_package_name,
            "provider_service_package_id": str(self.provider_service_package_id),
            "provider_service_package_name": self.provider_service_package_name,
            "api_package_id": str(self.api_package_id),
            "route_kind": self.route_kind.value,
            "host_id": self.host_id,
            "protocol_version": self.protocol_version,
            "request_timeout_s": self.request_timeout_s,
            "service_names": list(self.service_names),
            "endpoint_refs_by_service": _route_map_to_payload(
                self.endpoint_refs_by_service
            ),
            "stream_endpoint_refs_by_service": _route_map_to_payload(
                self.stream_endpoint_refs_by_service
            ),
        }
        if self.api_package_name is not None:
            payload["api_package_name"] = self.api_package_name
        if self.host_version is not None:
            payload["host_version"] = self.host_version
        if self.socket_path is not None:
            payload["socket_path"] = str(self.socket_path)
        if self.consumer_node_id is not None:
            payload["consumer_node_id"] = str(self.consumer_node_id)
        if self.provider_node_id is not None:
            payload["provider_node_id"] = str(self.provider_node_id)
        if self.provider_node_base_url is not None:
            payload["provider_node_base_url"] = self.provider_node_base_url
        if self.route_connection_id is not None:
            payload["route_connection_id"] = str(self.route_connection_id)
        if self.authority is not None and not self.authority.is_empty:
            payload["authority"] = self.authority.to_payload()
        return payload

    def _validate_route_transport(self) -> None:
        if self.route_kind is ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC:
            if self.socket_path is None:
                raise RuntimeError(
                    "Local Service API dependency routes require socket_path."
                )
            return
        if self.route_kind is ServiceApiDependencyRouteKind.REMOTE_NODE_API_ENDPOINT:
            if self.consumer_node_id is None:
                raise RuntimeError(
                    "Remote Service API dependency routes require consumer_node_id."
                )
            if self.provider_node_id is None:
                raise RuntimeError(
                    "Remote Service API dependency routes require provider_node_id."
                )
            if not (self.provider_node_base_url or "").strip():
                raise RuntimeError(
                    "Remote Service API dependency routes require provider_node_base_url."
                )
            return
        raise RuntimeError(
            f"Unsupported Service API dependency route kind: {self.route_kind.value!r}"
        )

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        base_dir: Path | None = None,
    ) -> "ServiceApiDependencyRouteDescriptor":
        if not isinstance(payload, Mapping):
            raise RuntimeError(
                "Service API dependency route payload must be an object."
            )
        route_kind = ServiceApiDependencyRouteKind(_required_str(payload, "route_kind"))
        socket_path = _optional_path(payload, "socket_path", base_dir=base_dir)
        route = cls(
            consumer_service_package_id=_required_uuid(
                payload,
                "consumer_service_package_id",
            ),
            consumer_service_package_name=_required_str(
                payload,
                "consumer_service_package_name",
            ),
            provider_service_package_id=_required_uuid(
                payload,
                "provider_service_package_id",
            ),
            provider_service_package_name=_required_str(
                payload,
                "provider_service_package_name",
            ),
            api_package_id=_required_uuid(payload, "api_package_id"),
            api_package_name=_optional_str(payload, "api_package_name"),
            route_kind=route_kind,
            host_id=_required_str(payload, "host_id"),
            host_version=_optional_str(payload, "host_version"),
            protocol_version=_required_str(payload, "protocol_version"),
            socket_path=socket_path,
            consumer_node_id=_optional_uuid(payload, "consumer_node_id"),
            provider_node_id=_optional_uuid(payload, "provider_node_id"),
            provider_node_base_url=_optional_str(payload, "provider_node_base_url"),
            route_connection_id=_optional_uuid(payload, "route_connection_id"),
            request_timeout_s=_required_float(payload, "request_timeout_s"),
            service_names=_str_tuple_from_payload(payload.get("service_names")),
            endpoint_refs_by_service=_route_map_from_payload(
                payload.get("endpoint_refs_by_service")
            ),
            stream_endpoint_refs_by_service=_route_map_from_payload(
                payload.get("stream_endpoint_refs_by_service")
            ),
            authority=_route_authority_from_payload(payload.get("authority")),
        )
        route._validate_route_transport()
        return route


def service_api_dependency_routes_to_payload(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
) -> list[dict[str, object]]:
    return [route.to_payload() for route in routes]


def service_api_dependency_routes_from_payload(
    payload: object,
    *,
    base_dir: Path | None = None,
) -> tuple[ServiceApiDependencyRouteDescriptor, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        raise RuntimeError("Service API dependency routes payload must be a list.")
    routes: list[ServiceApiDependencyRouteDescriptor] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError(
                "Service API dependency routes payload entries must be objects."
            )
        routes.append(
            ServiceApiDependencyRouteDescriptor.from_payload(item, base_dir=base_dir)
        )
    return tuple(routes)


def _route_map_to_payload(
    value: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    return {
        service_name: list(endpoint_refs)
        for service_name, endpoint_refs in sorted(
            value.items(),
            key=lambda item: item[0].casefold(),
        )
    }


def _route_map_from_payload(payload: object) -> Mapping[str, tuple[str, ...]]:
    if payload is None:
        return {}
    if not isinstance(payload, Mapping):
        raise RuntimeError("Service API dependency route map must be an object.")
    route_map: dict[str, tuple[str, ...]] = {}
    for raw_service_name, raw_endpoint_refs in payload.items():
        if not isinstance(raw_service_name, str):
            raise RuntimeError("Service API dependency route map keys must be strings.")
        service_name = raw_service_name.strip()
        if not service_name:
            continue
        route_map[service_name] = _str_tuple_from_payload(raw_endpoint_refs)
    return route_map


def _route_authority_from_payload(payload: object) -> ServiceApiRouteAuthority | None:
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise RuntimeError("Service API dependency route authority must be an object.")
    authority = ServiceApiRouteAuthority.from_payload(payload)
    return None if authority.is_empty else authority


def _str_tuple_from_payload(payload: object) -> tuple[str, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        raise RuntimeError("Service API dependency route field must be a string list.")
    values: list[str] = []
    for item in payload:
        if not isinstance(item, str):
            raise RuntimeError(
                "Service API dependency route field must contain only strings."
            )
        value = item.strip()
        if value:
            values.append(value)
    return tuple(values)


def _required_uuid(payload: Mapping[str, object], key: str) -> UUID:
    return UUID(_required_str(payload, key))


def _optional_uuid(payload: Mapping[str, object], key: str) -> UUID | None:
    value = _optional_str(payload, key)
    return UUID(value) if value is not None else None


def _optional_path(
    payload: Mapping[str, object],
    key: str,
    *,
    base_dir: Path | None = None,
) -> Path | None:
    value = _optional_str(payload, key)
    if value is None:
        return None
    path = Path(value).expanduser()
    if base_dir is not None and not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _required_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if not isinstance(value, int | float):
        raise RuntimeError(
            f"Service API dependency route field {key!r} must be numeric."
        )
    return float(value)


def _required_str(payload: Mapping[str, object], key: str) -> str:
    value = _optional_str(payload, key)
    if value is None:
        raise RuntimeError(
            f"Service API dependency route field {key!r} must be a non-empty string."
        )
    return value


def _optional_str(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeError(
            f"Service API dependency route field {key!r} must be a string."
        )
    return value.strip() or None


def _clean_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_token_match(*, expected: str | None, actual: str | None) -> bool:
    expected_token = _clean_optional_str(expected)
    if expected_token is None:
        return True
    return expected_token.casefold() == (_clean_optional_str(actual) or "").casefold()


__all__ = [
    "ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY",
    "ONTOLOGY_AUTHORITY_CATALOG_SCHEMA",
    "ServiceApiDependencyRouteDescriptor",
    "ServiceApiDependencyRouteKind",
    "ServiceApiRouteAuthority",
    "ServiceApiRouteAuthoritySelector",
    "service_api_dependency_routes_from_payload",
    "service_api_dependency_routes_to_payload",
]
