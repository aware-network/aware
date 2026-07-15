from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from aware_network_ontology.network.network_directory import NetworkDirectory
from aware_network_ontology.network.network_directory_response import (
    NetworkDirectoryEnvironmentItem,
    NetworkDirectoryExperienceServiceCandidate,
    NetworkDirectoryHostedServiceItem,
    NetworkDirectoryNodeRouteItem,
    NetworkDirectoryPeerItem,
    NetworkDirectoryTerritoryNodeItem,
)


async def load_nodes(
    *,
    network_directory: NetworkDirectory,
    node_id: UUID | None,
    limit_nodes: int | None,
) -> list[NetworkDirectoryNodeRouteItem]:
    limit = limit_nodes if limit_nodes is not None else 1000
    rows = await network_directory.session.execute_query(
        """
        SELECT
            id AS node_id,
            public_key,
            hostname,
            port,
            base_url,
            status,
            last_seen_at
        FROM network.network_node
        WHERE ($1::uuid IS NULL OR id = $1::uuid)
        ORDER BY hostname ASC, port ASC, id ASC
        LIMIT $2
        """,
        node_id,
        limit,
    )
    return [
        NetworkDirectoryNodeRouteItem(
            node_id=_required_uuid(row, "node_id"),
            public_key=_optional_string(row.get("public_key")),
            hostname=_required_string(row, "hostname"),
            port=_required_int(row, "port"),
            base_url=_node_base_url(row),
            status=_enum_or_string(row.get("status"), default="active"),
            last_seen_at=_optional_datetime_string(row.get("last_seen_at")),
        )
        for row in rows
    ]


async def load_environments_by_node(
    *,
    network_directory: NetworkDirectory,
    node_ids: tuple[UUID, ...],
    active_only: bool,
) -> dict[UUID, list[NetworkDirectoryEnvironmentItem]]:
    if not node_ids:
        return {}
    rows = await network_directory.session.execute_query(
        """
        SELECT
            nne.network_node_id AS node_id,
            nne.environment_id,
            nne.role,
            nne.is_active,
            nne.priority,
            env.key AS environment_key,
            env.title AS environment_title,
            env.config_id AS environment_config_id,
            env_config.handle AS environment_config_key,
            primary_experience.fqn_prefix AS primary_experience_name
        FROM network.network_node_environment nne
        LEFT JOIN environment.environment env
            ON env.id = nne.environment_id
        LEFT JOIN environment.environment_config env_config
            ON env_config.id = env.config_id
        LEFT JOIN environment.environment_experience_profile primary_profile
            ON primary_profile.id = env.environment_experience_profile_id
        LEFT JOIN environment.environment_experience primary_experience
            ON primary_experience.id = primary_profile.environment_experience_id
        WHERE nne.network_node_id = ANY($1::uuid[])
          AND ($2::boolean IS FALSE OR nne.is_active = TRUE)
        ORDER BY nne.priority DESC, env.title ASC, env.key ASC, nne.environment_id ASC
        """,
        list(node_ids),
        active_only,
    )
    experience_names_by_environment = await _load_environment_experience_names(
        network_directory=network_directory,
        environment_ids=tuple(
            environment_id
            for row in rows
            for environment_id in [_optional_uuid(row.get("environment_id"))]
            if environment_id is not None
        ),
    )

    by_node: dict[UUID, list[NetworkDirectoryEnvironmentItem]] = {}
    for row in rows:
        node_id = _required_uuid(row, "node_id")
        environment_id = _required_uuid(row, "environment_id")
        primary_experience_name = _optional_string(row.get("primary_experience_name"))
        experience_names = clean_unique_strings(
            (
                *(experience_names_by_environment.get(environment_id, ())),
                *((primary_experience_name,) if primary_experience_name else ()),
            )
        )
        by_node.setdefault(node_id, []).append(
            NetworkDirectoryEnvironmentItem(
                node_id=node_id,
                environment_id=environment_id,
                environment_key=_optional_string(row.get("environment_key")),
                environment_title=_optional_string(row.get("environment_title")),
                role=_enum_or_string(row.get("role"), default="replica"),
                is_active=_optional_bool(row.get("is_active"), default=True),
                priority=_optional_int(row.get("priority"), default=0) or 0,
                status=("active" if _optional_bool(row.get("is_active"), default=True) else "inactive"),
                experience_names=list(experience_names),
                environment_config_id=_optional_uuid(row.get("environment_config_id")),
                environment_config_key=_optional_string(row.get("environment_config_key")),
            )
        )
    return by_node


async def load_services_by_node(
    *,
    network_directory: NetworkDirectory,
    node_ids: tuple[UUID, ...],
) -> dict[UUID, list[NetworkDirectoryHostedServiceItem]]:
    if not node_ids:
        return {}
    rows = await network_directory.session.execute_query(
        """
        SELECT
            nns.network_node_id AS node_id,
            nns.service_id,
            service.name AS service_name,
            service_package.name AS service_package_name,
            nns.endpoint_refs,
            nns.stream_endpoint_refs,
            nns.host_id,
            nns.host_version,
            nns.protocol_version,
            nns.supports_stream_events
        FROM network.network_node_service nns
        LEFT JOIN service.service service
            ON service.id = nns.service_id
        LEFT JOIN service.service_package service_package
            ON service_package.service_config_id = service.service_config_id
        WHERE nns.network_node_id = ANY($1::uuid[])
        ORDER BY service.name ASC, nns.service_id ASC
        """,
        list(node_ids),
    )
    item_by_key: dict[tuple[UUID, UUID], NetworkDirectoryHostedServiceItem] = {}
    package_names_by_key: dict[tuple[UUID, UUID], list[str]] = {}
    for row in rows:
        node_id = _required_uuid(row, "node_id")
        service_id = _required_uuid(row, "service_id")
        service_name = _optional_string(row.get("service_name"))
        if not service_name:
            raise RuntimeError("NetworkDirectory requires NetworkNodeService.service to resolve " "Service.name")
        key = (node_id, service_id)
        if key not in item_by_key:
            item_by_key[key] = NetworkDirectoryHostedServiceItem(
                service_id=service_id,
                service_name=service_name,
                service_package_names=[],
                endpoint_refs=_string_list(row.get("endpoint_refs")),
                stream_endpoint_refs=_string_list(row.get("stream_endpoint_refs")),
                host_id=_required_string(row, "host_id"),
                host_version=_optional_string(row.get("host_version")),
                protocol_version=_required_string(row, "protocol_version"),
                supports_stream_events=_optional_bool(
                    row.get("supports_stream_events"),
                    default=False,
                ),
            )
        package_name = _optional_string(row.get("service_package_name"))
        if package_name:
            package_names_by_key.setdefault(key, []).append(package_name)

    by_node: dict[UUID, list[NetworkDirectoryHostedServiceItem]] = {}
    for (node_id, service_id), item in item_by_key.items():
        item.service_package_names = list(clean_unique_strings(package_names_by_key.get((node_id, service_id), [])))
        by_node.setdefault(node_id, []).append(item)
    for items in by_node.values():
        items.sort(key=lambda item: (item.service_name.casefold(), str(item.service_id)))
    return by_node


async def load_peers_by_node(
    *,
    network_directory: NetworkDirectory,
    node_ids: tuple[UUID, ...],
    accepted_only: bool,
) -> dict[UUID, list[NetworkDirectoryPeerItem]]:
    if not node_ids:
        return {}
    rows = await network_directory.session.execute_query(
        """
        SELECT
            peer.branch_id AS edge_id,
            peer.source_peer_node_id,
            peer.target_peer_node_id,
            peer.status,
            peer.peer_http_base_url,
            peer.trust_score,
            peer.connected_at,
            peer.last_ping_at,
            source_node.base_url AS source_base_url,
            source_node.hostname AS source_hostname,
            source_node.port AS source_port,
            target_node.base_url AS target_base_url,
            target_node.hostname AS target_hostname,
            target_node.port AS target_port
        FROM network.network_node_peer peer
        LEFT JOIN network.network_node source_node
            ON source_node.id = peer.source_peer_node_id
        LEFT JOIN network.network_node target_node
            ON target_node.id = peer.target_peer_node_id
        WHERE (
            peer.source_peer_node_id = ANY($1::uuid[])
            OR peer.target_peer_node_id = ANY($1::uuid[])
        )
          AND ($2::boolean IS FALSE OR peer.status = 'accepted')
        ORDER BY peer.connected_at DESC
        """,
        list(node_ids),
        accepted_only,
    )
    node_lookup = set(node_ids)
    by_node: dict[UUID, list[NetworkDirectoryPeerItem]] = {}
    for row in rows:
        source_id = _required_uuid(row, "source_peer_node_id")
        target_id = _required_uuid(row, "target_peer_node_id")
        if source_id in node_lookup:
            by_node.setdefault(source_id, []).append(
                _peer_item(
                    row=row,
                    peer_node_id=target_id,
                    direction="outgoing",
                    peer_base_url=(
                        _optional_string(row.get("peer_http_base_url"))
                        or _base_url_from_parts(
                            base_url=row.get("target_base_url"),
                            hostname=row.get("target_hostname"),
                            port=row.get("target_port"),
                        )
                    ),
                )
            )
        if target_id in node_lookup:
            by_node.setdefault(target_id, []).append(
                _peer_item(
                    row=row,
                    peer_node_id=source_id,
                    direction="incoming",
                    peer_base_url=_base_url_from_parts(
                        base_url=row.get("source_base_url"),
                        hostname=row.get("source_hostname"),
                        port=row.get("source_port"),
                    ),
                )
            )
    return by_node


async def load_route_hints(
    *,
    network_directory: NetworkDirectory,
    consumer_node_id: UUID | None,
    provider_node_ids: tuple[UUID, ...],
    accepted_only: bool,
) -> dict[UUID, dict[str, object]]:
    if consumer_node_id is None or not provider_node_ids:
        return {}
    rows = await network_directory.session.execute_query(
        """
        SELECT
            peer.branch_id AS edge_id,
            peer.target_peer_node_id AS provider_node_id,
            peer.peer_http_base_url,
            peer.status
        FROM network.network_node_peer peer
        WHERE peer.source_peer_node_id = $1::uuid
          AND peer.target_peer_node_id = ANY($2::uuid[])
          AND ($3::boolean IS FALSE OR peer.status = 'accepted')
        """,
        consumer_node_id,
        list(provider_node_ids),
        accepted_only,
    )
    hints: dict[UUID, dict[str, object]] = {}
    for row in rows:
        provider_node_id = _optional_uuid(row.get("provider_node_id"))
        if provider_node_id is None:
            continue
        hints[provider_node_id] = {
            "route_connection_id": _optional_uuid(row.get("edge_id")),
            "provider_node_base_url": _optional_string(row.get("peer_http_base_url")),
            "route_status": (
                "reachable"
                if _enum_or_string(row.get("status"), default="accepted").casefold() == "accepted"
                else "peer_required"
            ),
        }
    return hints


def resolve_route_hint(
    *,
    node: NetworkDirectoryNodeRouteItem,
    consumer_node_id: UUID | None,
    route_hints: dict[UUID, dict[str, object]],
    include_route_hints: bool,
    require_access_evidence: bool,
    access_evidence_refs: Iterable[str],
) -> dict[str, object]:
    route_status = "reachable"
    provider_node_base_url: str | None = node.base_url
    route_connection_id: UUID | None = None
    if consumer_node_id is not None and consumer_node_id != node.node_id:
        route_status = "peer_required"
        hint = route_hints.get(node.node_id)
        if hint is not None:
            route_status = _optional_string(hint.get("route_status")) or "reachable"
            route_connection_id = _optional_uuid(hint.get("route_connection_id"))
            provider_node_base_url = _optional_string(hint.get("provider_node_base_url")) or node.base_url
    if route_status == "reachable" and require_access_evidence and not clean_unique_strings(access_evidence_refs):
        route_status = "access_required"
    if not include_route_hints:
        provider_node_base_url = None
        route_connection_id = None
    return {
        "route_status": route_status,
        "provider_node_base_url": provider_node_base_url,
        "route_connection_id": route_connection_id,
    }


def experience_service_candidates(
    *,
    node: NetworkDirectoryNodeRouteItem,
    hosted_services: Iterable[NetworkDirectoryHostedServiceItem],
    route_hint: dict[str, object],
    required_service_package_names: tuple[str, ...],
    required_endpoint_refs: tuple[str, ...],
    required_services: bool,
) -> tuple[NetworkDirectoryExperienceServiceCandidate, ...]:
    candidates: list[NetworkDirectoryExperienceServiceCandidate] = []
    for hosted_service in hosted_services:
        matched_package_names = _matched_required_values(
            required_values=required_service_package_names,
            available_values=hosted_service.service_package_names,
        )
        matched_endpoint_refs = _matched_required_values(
            required_values=required_endpoint_refs,
            available_values=(
                *hosted_service.endpoint_refs,
                *hosted_service.stream_endpoint_refs,
            ),
        )
        if required_services and not (matched_package_names or matched_endpoint_refs):
            continue
        candidates.append(
            NetworkDirectoryExperienceServiceCandidate(
                hosted_service=hosted_service,
                provider_node_id=node.node_id,
                provider_node_base_url=_optional_string(route_hint.get("provider_node_base_url")),
                route_connection_id=_optional_uuid(route_hint.get("route_connection_id")),
                route_status=_optional_string(route_hint.get("route_status")) or "reachable",
                matched_service_package_names=list(matched_package_names),
                matched_endpoint_refs=list(matched_endpoint_refs),
                missing_service_package_names=missing_required_values(
                    required_values=required_service_package_names,
                    matched_values=matched_package_names,
                ),
                missing_endpoint_refs=missing_required_values(
                    required_values=required_endpoint_refs,
                    matched_values=matched_endpoint_refs,
                ),
            )
        )
    return tuple(candidates)


def entry_route_status(
    *,
    route_status: str,
    required_services: bool,
    service_candidates: Iterable[NetworkDirectoryExperienceServiceCandidate],
    missing_service_package_names: Iterable[str],
    missing_endpoint_refs: Iterable[str],
) -> str:
    candidates = tuple(service_candidates)
    if required_services and (not candidates or tuple(missing_service_package_names) or tuple(missing_endpoint_refs)):
        return "unavailable"
    if not candidates:
        return route_status
    route_statuses = {candidate.route_status for candidate in candidates}
    if "access_required" in route_statuses:
        return "access_required"
    if "reachable" in route_statuses:
        return "reachable"
    if "peer_required" in route_statuses:
        return "peer_required"
    return "unavailable"


def territory_summary(nodes: Iterable[NetworkDirectoryTerritoryNodeItem]) -> str:
    node_list = tuple(nodes)
    environment_count = sum(len(node.environments) for node in node_list)
    hosted_service_count = sum(len(node.hosted_services) for node in node_list)
    return f"{len(node_list)} nodes, " f"{environment_count} environments, " f"{hosted_service_count} hosted services"


def experience_matches(
    *,
    environment: NetworkDirectoryEnvironmentItem,
    experience_name: str,
) -> bool:
    normalized = experience_name.strip().casefold()
    return normalized in {
        candidate.strip().casefold() for candidate in environment.experience_names if candidate.strip()
    }


def missing_required_values(
    *,
    required_values: Iterable[str],
    matched_values: Iterable[str],
) -> list[str]:
    matched_lookup = {value.strip().casefold() for value in matched_values}
    return [required for required in required_values if required.strip().casefold() not in matched_lookup]


def clean_unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return tuple(cleaned)


async def _load_environment_experience_names(
    *,
    network_directory: NetworkDirectory,
    environment_ids: tuple[UUID, ...],
) -> dict[UUID, tuple[str, ...]]:
    if not environment_ids:
        return {}
    try:
        rows = await network_directory.session.execute_query(
            """
            SELECT
                mount.environment_id,
                experience.fqn_prefix AS experience_name
            FROM environment.environment_experience_profile_mount mount
            JOIN environment.environment_experience_profile profile
                ON profile.id = mount.environment_experience_profile_id
            JOIN environment.environment_experience experience
                ON experience.id = profile.environment_experience_id
            WHERE mount.environment_id = ANY($1::uuid[])
            ORDER BY mount.position ASC NULLS LAST, mount.mount_key ASC
            """,
            list(environment_ids),
        )
    except Exception:
        return {}

    names_by_environment: dict[UUID, list[str]] = {}
    for row in rows:
        environment_id = _optional_uuid(row.get("environment_id"))
        experience_name = _optional_string(row.get("experience_name"))
        if environment_id is None or not experience_name:
            continue
        names_by_environment.setdefault(environment_id, []).append(experience_name)
    return {environment_id: clean_unique_strings(names) for environment_id, names in names_by_environment.items()}


def _peer_item(
    *,
    row: dict[str, object],
    peer_node_id: UUID,
    direction: str,
    peer_base_url: str,
) -> NetworkDirectoryPeerItem:
    return NetworkDirectoryPeerItem(
        edge_id=_optional_uuid(row.get("edge_id")),
        source_node_id=_required_uuid(row, "source_peer_node_id"),
        target_node_id=_required_uuid(row, "target_peer_node_id"),
        peer_node_id=peer_node_id,
        peer_base_url=peer_base_url,
        direction=direction,
        status=_enum_or_string(row.get("status"), default="accepted"),
        trust_score=_optional_float(row.get("trust_score"), default=0.0),
        connected_at=_optional_datetime_string(row.get("connected_at")),
        last_ping_at=_optional_datetime_string(row.get("last_ping_at")),
    )


def _matched_required_values(
    *,
    required_values: Iterable[str],
    available_values: Iterable[str],
) -> tuple[str, ...]:
    available_lookup = {value.strip().casefold() for value in available_values if value.strip()}
    return tuple(required for required in required_values if required.strip().casefold() in available_lookup)


def _node_base_url(row: dict[str, object]) -> str:
    return _base_url_from_parts(
        base_url=row.get("base_url"),
        hostname=row.get("hostname"),
        port=row.get("port"),
    )


def _base_url_from_parts(
    *,
    base_url: object,
    hostname: object,
    port: object,
) -> str:
    normalized = _optional_string(base_url)
    if normalized:
        return normalized.rstrip("/")
    host = _optional_string(hostname) or "127.0.0.1"
    resolved_port = _optional_int(port, default=0) or 0
    return f"http://{host}:{resolved_port}" if resolved_port > 0 else f"http://{host}"


def _required_uuid(row: dict[str, object], key: str) -> UUID:
    value = _optional_uuid(row.get(key))
    if value is None:
        raise RuntimeError(f"NetworkDirectory query returned missing UUID {key!r}")
    return value


def _optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def _required_string(row: dict[str, object], key: str) -> str:
    value = _optional_string(row.get(key))
    if value is None:
        raise RuntimeError(f"NetworkDirectory query returned missing string {key!r}")
    return value


def _optional_string(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    if value is None:
        return None
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        normalized = enum_value.strip()
        return normalized or None
    normalized = str(value).strip()
    return normalized or None


def _enum_or_string(value: object, *, default: str) -> str:
    return _optional_string(value) or default


def _required_int(row: dict[str, object], key: str) -> int:
    value = _optional_int(row.get(key), default=None)
    if value is None:
        raise RuntimeError(f"NetworkDirectory query returned missing int {key!r}")
    return value


def _optional_int(value: object, *, default: int | None) -> int | None:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _optional_float(value: object, *, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _optional_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return default


def _optional_datetime_string(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return _optional_string(value)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]
