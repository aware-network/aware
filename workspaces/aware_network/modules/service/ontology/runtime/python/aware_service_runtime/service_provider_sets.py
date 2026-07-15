from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_service_runtime.service_api_dependency_routes import (
    ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY,
    ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
    ServiceApiRouteAuthority,
)


SERVICE_API_PROVIDER_SET_CONTRACT_VERSION = "aware.service.api_provider_set.v1"


@dataclass(frozen=True, slots=True)
class ServiceApiProviderRef:
    """Serializable remote ServicePackage provider advertised by a Node."""

    provider_node_id: UUID
    provider_node_base_url: str
    service_package_ref: Mapping[str, object]
    provider_node_package: str | None = None
    provider_node_runtime_source: Mapping[str, object] | None = None
    route_connection_id: UUID | None = None
    request_timeout_s: float | None = None
    hosted_service_advertisement: Mapping[str, object] | None = None
    authority: ServiceApiRouteAuthority | None = None

    def to_payload(self) -> dict[str, object]:
        base_url = self.provider_node_base_url.strip()
        if not base_url:
            raise ValueError(
                "Service API provider refs require provider_node_base_url."
            )
        if not self.service_package_ref:
            raise ValueError("Service API provider refs require service_package_ref.")
        payload: dict[str, object] = {
            "provider_node_id": str(self.provider_node_id),
            "provider_node_base_url": base_url,
            "service_package_ref": dict(self.service_package_ref),
        }
        if self.provider_node_package is not None:
            provider_node_package = self.provider_node_package.strip()
            if provider_node_package:
                payload["provider_node_package"] = provider_node_package
        if self.provider_node_runtime_source is not None:
            payload["provider_node_runtime_source"] = dict(
                self.provider_node_runtime_source
            )
        if self.route_connection_id is not None:
            payload["route_connection_id"] = str(self.route_connection_id)
        if self.request_timeout_s is not None:
            payload["request_timeout_s"] = self.request_timeout_s
        if self.hosted_service_advertisement is not None:
            payload["hosted_service_advertisement"] = dict(
                self.hosted_service_advertisement
            )
        if self.authority is not None and not self.authority.is_empty:
            payload["authority"] = self.authority.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "ServiceApiProviderRef":
        service_package_ref = payload.get("service_package_ref")
        if not isinstance(service_package_ref, Mapping):
            raise ValueError(
                "Service API provider ref payload requires service_package_ref."
            )
        return cls(
            provider_node_id=_required_uuid(payload, "provider_node_id"),
            provider_node_base_url=_required_str(payload, "provider_node_base_url"),
            service_package_ref=dict(service_package_ref),
            provider_node_package=_optional_str(payload, "provider_node_package"),
            provider_node_runtime_source=_optional_mapping(
                payload,
                "provider_node_runtime_source",
            ),
            route_connection_id=_optional_uuid(payload, "route_connection_id"),
            request_timeout_s=_optional_float(payload, "request_timeout_s"),
            hosted_service_advertisement=_optional_mapping(
                payload,
                "hosted_service_advertisement",
            ),
            authority=_route_authority_from_payload(payload.get("authority")),
        )


@dataclass(frozen=True, slots=True)
class ServiceApiProviderSet:
    """Service-owned provider set produced by a service-node deployment."""

    provider_set_id: str
    provider_refs: tuple[ServiceApiProviderRef, ...]
    contract_version: str = SERVICE_API_PROVIDER_SET_CONTRACT_VERSION
    workspace_profile_path: str | None = None
    workspace_revision_id: UUID | None = None
    workspace_deployment_revision_id: str | None = None
    workspace_deployment_channel: str | None = None
    workspace_deployment_artifact_key: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        provider_set_id = self.provider_set_id.strip()
        if not provider_set_id:
            raise ValueError("Service API provider sets require provider_set_id.")
        payload: dict[str, object] = {
            "contract_version": self.contract_version,
            "provider_set_id": provider_set_id,
            "provider_refs": [
                provider_ref.to_payload() for provider_ref in self.provider_refs
            ],
        }
        if self.workspace_profile_path is not None:
            payload["workspace_profile_path"] = self.workspace_profile_path
        if self.workspace_revision_id is not None:
            payload["workspace_revision_id"] = str(self.workspace_revision_id)
        if self.workspace_deployment_revision_id is not None:
            payload["workspace_deployment_revision_id"] = (
                self.workspace_deployment_revision_id
            )
        if self.workspace_deployment_channel is not None:
            payload["workspace_deployment_channel"] = self.workspace_deployment_channel
        if self.workspace_deployment_artifact_key is not None:
            payload["workspace_deployment_artifact_key"] = (
                self.workspace_deployment_artifact_key
            )
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "ServiceApiProviderSet":
        contract_version = _required_str(payload, "contract_version")
        if contract_version != SERVICE_API_PROVIDER_SET_CONTRACT_VERSION:
            raise ValueError(
                "Unsupported Service API provider-set contract_version: "
                f"{contract_version!r}"
            )
        raw_provider_refs = payload.get("provider_refs")
        if not isinstance(raw_provider_refs, list):
            raise ValueError("Service API provider-set payload requires provider_refs.")
        provider_refs: list[ServiceApiProviderRef] = []
        for item in raw_provider_refs:
            if not isinstance(item, Mapping):
                raise ValueError(
                    "Service API provider-set provider_refs entries must be objects."
                )
            provider_refs.append(ServiceApiProviderRef.from_payload(item))
        return cls(
            contract_version=contract_version,
            provider_set_id=_required_str(payload, "provider_set_id"),
            provider_refs=tuple(provider_refs),
            workspace_profile_path=_optional_str(payload, "workspace_profile_path"),
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
            metadata=_optional_mapping(payload, "metadata") or {},
        )


def service_api_provider_refs_to_payload(
    provider_refs: Sequence[ServiceApiProviderRef],
) -> list[dict[str, object]]:
    return [provider_ref.to_payload() for provider_ref in provider_refs]


def service_api_provider_refs_from_payload(
    payload: object,
) -> tuple[ServiceApiProviderRef, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        raise ValueError("Service API provider refs payload must be a list.")
    refs: list[ServiceApiProviderRef] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Service API provider refs entries must be objects.")
        refs.append(ServiceApiProviderRef.from_payload(item))
    return tuple(refs)


def service_api_provider_refs_to_json(
    provider_refs: Sequence[ServiceApiProviderRef],
) -> str:
    return json.dumps(
        service_api_provider_refs_to_payload(provider_refs),
        sort_keys=True,
        separators=(",", ":"),
    )


def service_api_provider_refs_from_provider_sets(
    provider_sets: Sequence[ServiceApiProviderSet],
) -> tuple[ServiceApiProviderRef, ...]:
    refs: list[ServiceApiProviderRef] = []
    for provider_set in provider_sets:
        refs.extend(
            replace(
                provider_ref,
                authority=_route_authority_from_provider_set(
                    provider_set=provider_set,
                    provider_ref=provider_ref,
                ),
            )
            for provider_ref in provider_set.provider_refs
        )
    return tuple(refs)


def build_ontology_authority_catalog_metadata(
    provider_node_runtime_source: Mapping[str, object] | None,
) -> dict[str, object]:
    catalog = build_ontology_authority_catalog(provider_node_runtime_source)
    if catalog is None:
        return {}
    return {ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY: catalog}


def build_ontology_authority_catalog(
    provider_node_runtime_source: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if not isinstance(provider_node_runtime_source, Mapping):
        return None
    raw_targets = provider_node_runtime_source.get("ontology_targets")
    if not isinstance(raw_targets, list):
        return None
    targets_by_key: dict[tuple[str, str | None], dict[str, object]] = {}
    for raw_target in raw_targets:
        if not isinstance(raw_target, Mapping):
            continue
        package_name = _clean_value(raw_target.get("package_name"))
        fqn_prefix = _clean_value(raw_target.get("fqn_prefix"))
        if package_name is None and fqn_prefix is None:
            continue
        target: dict[str, object] = {}
        if package_name is not None:
            target["package_name"] = package_name
        if fqn_prefix is not None:
            target["fqn_prefix"] = fqn_prefix
        targets_by_key[(package_name or "", fqn_prefix)] = target
    if not targets_by_key:
        return None

    ontology_targets = [
        target
        for _, target in sorted(
            targets_by_key.items(),
            key=lambda item: (
                item[0][0].casefold(),
                (item[0][1] or "").casefold(),
            ),
        )
    ]
    package_names = [
        str(target["package_name"])
        for target in ontology_targets
        if isinstance(target.get("package_name"), str)
    ]
    catalog: dict[str, object] = {
        "schema": ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
        "ontology_package_names": package_names,
        "ontology_targets": ontology_targets,
    }
    source_kind = _clean_value(provider_node_runtime_source.get("source_kind"))
    if source_kind is not None:
        catalog["source_kind"] = source_kind
    fqn_prefixes = [
        str(target["fqn_prefix"])
        for target in ontology_targets
        if isinstance(target.get("fqn_prefix"), str)
    ]
    if fqn_prefixes:
        catalog["fqn_prefixes"] = fqn_prefixes
    return catalog


def write_service_api_provider_set(
    *,
    path: Path,
    provider_set: ServiceApiProviderSet,
) -> Path:
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(provider_set.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return resolved


def load_service_api_provider_set(path: Path) -> ServiceApiProviderSet:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Service API provider-set file must contain an object.")
    return ServiceApiProviderSet.from_payload(payload)


def load_service_api_provider_sets(
    paths: Sequence[Path],
) -> tuple[ServiceApiProviderSet, ...]:
    return tuple(load_service_api_provider_set(path) for path in paths)


def _required_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Service API provider-set payload requires {key}.")
    return value.strip()


def _optional_str(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Service API provider-set {key} must be a string.")
    normalized = value.strip()
    return normalized or None


def _required_uuid(payload: Mapping[str, object], key: str) -> UUID:
    return UUID(_required_str(payload, key))


def _optional_uuid(payload: Mapping[str, object], key: str) -> UUID | None:
    value = _optional_str(payload, key)
    return UUID(value) if value is not None else None


def _optional_float(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ValueError(f"Service API provider-set {key} must be numeric.")
    return float(value)


def _optional_mapping(
    payload: Mapping[str, object],
    key: str,
) -> dict[str, Any] | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"Service API provider-set {key} must be an object.")
    return dict(value)


def _route_authority_from_provider_set(
    *,
    provider_set: ServiceApiProviderSet,
    provider_ref: ServiceApiProviderRef,
) -> ServiceApiRouteAuthority:
    metadata = dict(provider_set.metadata)
    metadata.update(
        build_ontology_authority_catalog_metadata(
            provider_ref.provider_node_runtime_source
        )
    )
    return ServiceApiRouteAuthority(
        provider_set_id=provider_set.provider_set_id,
        workspace_revision_id=provider_set.workspace_revision_id,
        workspace_deployment_revision_id=provider_set.workspace_deployment_revision_id,
        workspace_deployment_channel=provider_set.workspace_deployment_channel,
        workspace_deployment_artifact_key=provider_set.workspace_deployment_artifact_key,
        metadata=metadata,
    )


def _route_authority_from_payload(payload: object) -> ServiceApiRouteAuthority | None:
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise ValueError("Service API provider ref authority must be an object.")
    authority = ServiceApiRouteAuthority.from_payload(payload)
    return None if authority.is_empty else authority


def _clean_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


__all__ = [
    "SERVICE_API_PROVIDER_SET_CONTRACT_VERSION",
    "ServiceApiProviderRef",
    "ServiceApiProviderSet",
    "build_ontology_authority_catalog",
    "build_ontology_authority_catalog_metadata",
    "load_service_api_provider_set",
    "load_service_api_provider_sets",
    "service_api_provider_refs_from_payload",
    "service_api_provider_refs_from_provider_sets",
    "service_api_provider_refs_to_json",
    "service_api_provider_refs_to_payload",
    "write_service_api_provider_set",
]
