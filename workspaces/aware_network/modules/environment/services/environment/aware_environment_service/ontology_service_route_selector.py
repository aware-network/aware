from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_service_runtime.service_api_dependency_routes import (
    ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY,
    ServiceApiDependencyRouteDescriptor,
)


@dataclass(frozen=True, slots=True)
class OntologyServiceApiRouteSelector:
    """Explicit host-owned selector for one Ontology service API route.

    The selector is intentionally limited to service route identity fields that
    already travel through Service API dependency route descriptors. Future
    Node/Service route metadata can extend this object without letting
    Environment inspect Ontology internals.
    """

    provider_service_package_id: UUID | None = None
    provider_service_package_name: str | None = None
    provider_node_id: UUID | None = None
    host_id: str | None = None
    route_connection_id: UUID | None = None
    service_name: str | None = None
    provider_set_id: str | None = None
    workspace_revision_id: UUID | None = None
    workspace_deployment_revision_id: str | None = None
    workspace_deployment_channel: str | None = None
    workspace_deployment_artifact_key: str | None = None
    ontology_package_name: str | None = None
    ontology_fqn_prefix: str | None = None

    @property
    def is_empty(self) -> bool:
        return not any(
            (
                self.provider_service_package_id,
                _clean(self.provider_service_package_name),
                self.provider_node_id,
                _clean(self.host_id),
                self.route_connection_id,
                _clean(self.service_name),
                _clean(self.provider_set_id),
                self.workspace_revision_id,
                _clean(self.workspace_deployment_revision_id),
                _clean(self.workspace_deployment_channel),
                _clean(self.workspace_deployment_artifact_key),
                _clean(self.ontology_package_name),
                _clean(self.ontology_fqn_prefix),
            )
        )

    def describe(self) -> str:
        fields: list[str] = []
        if self.provider_service_package_id is not None:
            fields.append(
                f"provider_service_package_id={self.provider_service_package_id}"
            )
        if _clean(self.provider_service_package_name):
            fields.append(
                "provider_service_package_name="
                f"{self.provider_service_package_name!r}"
            )
        if self.provider_node_id is not None:
            fields.append(f"provider_node_id={self.provider_node_id}")
        if _clean(self.host_id):
            fields.append(f"host_id={self.host_id!r}")
        if self.route_connection_id is not None:
            fields.append(f"route_connection_id={self.route_connection_id}")
        if _clean(self.service_name):
            fields.append(f"service_name={self.service_name!r}")
        if _clean(self.provider_set_id):
            fields.append(f"provider_set_id={self.provider_set_id!r}")
        if self.workspace_revision_id is not None:
            fields.append(f"workspace_revision_id={self.workspace_revision_id}")
        if _clean(self.workspace_deployment_revision_id):
            fields.append(
                "workspace_deployment_revision_id="
                f"{self.workspace_deployment_revision_id!r}"
            )
        if _clean(self.workspace_deployment_channel):
            fields.append(
                "workspace_deployment_channel=" f"{self.workspace_deployment_channel!r}"
            )
        if _clean(self.workspace_deployment_artifact_key):
            fields.append(
                "workspace_deployment_artifact_key="
                f"{self.workspace_deployment_artifact_key!r}"
            )
        if _clean(self.ontology_package_name):
            fields.append(f"ontology_package_name={self.ontology_package_name!r}")
        if _clean(self.ontology_fqn_prefix):
            fields.append(f"ontology_fqn_prefix={self.ontology_fqn_prefix!r}")
        return ", ".join(fields) if fields else "empty selector"

    def matches(self, route: ServiceApiDependencyRouteDescriptor) -> bool:
        if (
            self.provider_service_package_id is not None
            and route.provider_service_package_id != self.provider_service_package_id
        ):
            return False
        if not _optional_token_match(
            expected=self.provider_service_package_name,
            actual=route.provider_service_package_name,
        ):
            return False
        if (
            self.provider_node_id is not None
            and route.provider_node_id != self.provider_node_id
        ):
            return False
        if not _optional_token_match(expected=self.host_id, actual=route.host_id):
            return False
        if (
            self.route_connection_id is not None
            and route.route_connection_id != self.route_connection_id
        ):
            return False
        service_name = _clean(self.service_name)
        if service_name:
            service_names = {
                value.strip().casefold()
                for value in route.service_names
                if value.strip()
            }
            if service_name.casefold() not in service_names:
                return False
        authority = route.authority
        if not _optional_token_match(
            expected=self.provider_set_id,
            actual=authority.provider_set_id if authority is not None else None,
        ):
            return False
        if self.workspace_revision_id is not None and (
            authority is None
            or authority.workspace_revision_id != self.workspace_revision_id
        ):
            return False
        if not _optional_token_match(
            expected=self.workspace_deployment_revision_id,
            actual=(
                authority.workspace_deployment_revision_id
                if authority is not None
                else None
            ),
        ):
            return False
        if not _optional_token_match(
            expected=self.workspace_deployment_channel,
            actual=(
                authority.workspace_deployment_channel
                if authority is not None
                else None
            ),
        ):
            return False
        if not _optional_token_match(
            expected=self.workspace_deployment_artifact_key,
            actual=(
                authority.workspace_deployment_artifact_key
                if authority is not None
                else None
            ),
        ):
            return False
        if not _ontology_authority_catalog_matches(
            route=route,
            ontology_package_name=self.ontology_package_name,
            ontology_fqn_prefix=self.ontology_fqn_prefix,
        ):
            return False
        return True


def _ontology_authority_catalog_matches(
    *,
    route: ServiceApiDependencyRouteDescriptor,
    ontology_package_name: str | None,
    ontology_fqn_prefix: str | None,
) -> bool:
    expected_package_name = _clean(ontology_package_name)
    expected_fqn_prefix = _clean(ontology_fqn_prefix)
    if not expected_package_name and not expected_fqn_prefix:
        return True
    authority = route.authority
    if authority is None:
        return False
    catalog = authority.metadata.get(ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY)
    if not isinstance(catalog, Mapping):
        return False
    targets = _ontology_catalog_targets(catalog)
    if expected_package_name and expected_fqn_prefix:
        return any(
            _optional_token_match(
                expected=expected_package_name,
                actual=_optional_string(target.get("package_name")),
            )
            and _optional_token_match(
                expected=expected_fqn_prefix,
                actual=_optional_string(target.get("fqn_prefix")),
            )
            for target in targets
        )
    if expected_package_name:
        return _catalog_list_contains(
            catalog.get("ontology_package_names"),
            expected=expected_package_name,
        ) or any(
            _optional_token_match(
                expected=expected_package_name,
                actual=_optional_string(target.get("package_name")),
            )
            for target in targets
        )
    return _catalog_list_contains(
        catalog.get("fqn_prefixes"),
        expected=expected_fqn_prefix,
    ) or any(
        _optional_token_match(
            expected=expected_fqn_prefix,
            actual=_optional_string(target.get("fqn_prefix")),
        )
        for target in targets
    )


def _ontology_catalog_targets(
    catalog: Mapping[object, object],
) -> tuple[Mapping[object, object], ...]:
    raw_targets = catalog.get("ontology_targets")
    if not isinstance(raw_targets, list):
        return ()
    return tuple(target for target in raw_targets if isinstance(target, Mapping))


def _catalog_list_contains(raw_values: object, *, expected: str) -> bool:
    if not isinstance(raw_values, list):
        return False
    return any(
        _optional_token_match(expected=expected, actual=_optional_string(value))
        for value in raw_values
    )


def _optional_token_match(*, expected: str | None, actual: str | None) -> bool:
    expected_token = _clean(expected)
    if not expected_token:
        return True
    return expected_token.casefold() == _clean(actual).casefold()


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _clean(value: str | None) -> str:
    return (value or "").strip()


__all__ = ["OntologyServiceApiRouteSelector"]
