from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from aware_api_runtime.source import load_api_ownership_from_sources
from aware_api_runtime.workspace import APIWorkspace
from aware_api_runtime.manifest.loader import load_aware_api_toml_spec
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec


@dataclass(frozen=True, slots=True)
class ServiceApiTruth:
    endpoint_refs: frozenset[str]


@dataclass(frozen=True, slots=True)
class ServiceDependencyScope:
    service_package_name: str
    manifest_path: Path
    declared_api_package_names: tuple[str, ...]
    resolved_api_package_names: tuple[str, ...]
    api_catalog: dict[str, ServiceApiTruth]


def _ancestor_roots(*, start: Path) -> tuple[Path, ...]:
    cursor = start.resolve()
    if cursor.is_file():
        cursor = cursor.parent
    return tuple([cursor, *cursor.parents])


def _hash_json_artifact(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _find_service_protocol_plan_path(*, start: Path, package_name: str) -> Path | None:
    for root in _ancestor_roots(start=start):
        candidate = (
            root
            / ".aware"
            / "api"
            / "runtime"
            / package_name
            / "api.service_protocol_plan.json"
        ).resolve()
        if candidate.is_file():
            return candidate
    return None


def _load_api_catalog_from_service_protocol_plan(
    *,
    path: Path,
) -> dict[str, ServiceApiTruth]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    apis = payload.get("apis")
    if not isinstance(apis, list):
        return {}

    endpoint_refs_by_api: dict[str, set[str]] = {}
    for api_row in apis:
        if not isinstance(api_row, dict):
            continue
        capabilities = api_row.get("capabilities")
        if not isinstance(capabilities, list):
            continue
        for capability_row in capabilities:
            if not isinstance(capability_row, dict):
                continue
            endpoints = capability_row.get("endpoints")
            if not isinstance(endpoints, list):
                continue
            for endpoint_row in endpoints:
                if not isinstance(endpoint_row, dict):
                    continue
                endpoint_ref = str(endpoint_row.get("endpoint_ref") or "").strip()
                if not endpoint_ref:
                    continue
                api_name = endpoint_ref.split(".", 1)[0].strip()
                if not api_name:
                    continue
                endpoint_refs_by_api.setdefault(api_name.casefold(), set()).add(
                    endpoint_ref
                )

    return {
        api_key: ServiceApiTruth(endpoint_refs=frozenset(sorted(endpoint_refs)))
        for api_key, endpoint_refs in endpoint_refs_by_api.items()
    }


def _find_workspace_api_manifest_paths(*, start: Path) -> tuple[Path, ...]:
    for root in _ancestor_roots(start=start):
        search_root = (root / "apis").resolve()
        if not search_root.is_dir():
            continue
        matches = tuple(
            sorted(
                path.resolve()
                for path in search_root.glob("*/aware.api.toml")
                if path.is_file()
            )
        )
        if matches:
            return matches
    return ()


def _find_api_manifest_by_package_name(
    *, start: Path, package_name: str
) -> Path | None:
    package_key = package_name.casefold()
    for manifest_path in _find_workspace_api_manifest_paths(start=start):
        try:
            spec = load_aware_api_toml_spec(toml_path=manifest_path)
        except Exception:
            continue
        manifest_package_name = (spec.api.package_name or "").strip().casefold()
        if manifest_package_name == package_key:
            return manifest_path
    return None


def _load_api_catalog_from_manifest(
    *,
    manifest_path: Path,
) -> dict[str, ServiceApiTruth]:
    try:
        snapshot = APIWorkspace.from_toml(
            toml_path=manifest_path, repo_root=manifest_path.parent
        ).build_snapshot()
        ownership = load_api_ownership_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
        )
    except Exception:
        return {}

    catalog: dict[str, ServiceApiTruth] = {}
    for api in ownership:
        endpoint_refs = frozenset(
            sorted(
                f"{api.name}.{capability.name}.{endpoint.name}"
                for capability in api.capabilities
                for endpoint in capability.endpoints
            )
        )
        catalog[api.name.casefold()] = ServiceApiTruth(endpoint_refs=endpoint_refs)
    return catalog


def _merge_api_catalogs(
    *, catalogs: tuple[dict[str, ServiceApiTruth], ...]
) -> dict[str, ServiceApiTruth]:
    endpoint_refs_by_api: dict[str, set[str]] = {}
    for catalog in catalogs:
        for api_key, truth in catalog.items():
            endpoint_refs_by_api.setdefault(api_key, set()).update(truth.endpoint_refs)
    return {
        api_key: ServiceApiTruth(endpoint_refs=frozenset(sorted(endpoint_refs)))
        for api_key, endpoint_refs in endpoint_refs_by_api.items()
    }


def load_service_dependency_scope(*, manifest_path: Path) -> ServiceDependencyScope:
    spec = load_aware_service_toml_spec(toml_path=manifest_path)
    resolved_manifest_path = manifest_path.resolve()
    package_root = resolved_manifest_path.parent
    service_package_name = (
        spec.service.package_name or ""
    ).strip() or package_root.name
    declared_api_package_names = tuple(
        sorted(
            {
                dependency.package_name.strip()
                for dependency in spec.dependencies
                if dependency.package_name.strip()
            },
            key=str.casefold,
        )
    )

    catalogs: list[dict[str, ServiceApiTruth]] = []
    resolved_api_package_names: set[str] = set()
    dependency_package_name_keys = {
        package_name.casefold() for package_name in declared_api_package_names
    }

    for dependency in spec.dependencies:
        dependency_package_name = dependency.package_name.strip()
        if not dependency_package_name:
            continue
        expected_hash_sha256 = (dependency.expected_hash_sha256 or "").strip() or None
        service_protocol_plan_path = _find_service_protocol_plan_path(
            start=package_root,
            package_name=dependency_package_name,
        )
        if service_protocol_plan_path is not None:
            actual_hash_sha256 = _hash_json_artifact(service_protocol_plan_path)
            if (
                expected_hash_sha256 is None
                or actual_hash_sha256 == expected_hash_sha256
            ):
                catalog = _load_api_catalog_from_service_protocol_plan(
                    path=service_protocol_plan_path
                )
                if catalog:
                    catalogs.append(catalog)
                    resolved_api_package_names.add(dependency_package_name)
                    continue

        manifest_candidate = _find_api_manifest_by_package_name(
            start=package_root,
            package_name=dependency_package_name,
        )
        if manifest_candidate is not None:
            catalog = _load_api_catalog_from_manifest(manifest_path=manifest_candidate)
            if catalog:
                catalogs.append(catalog)
                resolved_api_package_names.add(dependency_package_name)

    if catalogs:
        return ServiceDependencyScope(
            service_package_name=service_package_name,
            manifest_path=resolved_manifest_path,
            declared_api_package_names=declared_api_package_names,
            resolved_api_package_names=tuple(
                sorted(resolved_api_package_names, key=str.casefold)
            ),
            api_catalog=_merge_api_catalogs(catalogs=tuple(catalogs)),
        )

    workspace_api_catalogs: list[tuple[str, dict[str, ServiceApiTruth]]] = []
    for workspace_manifest_path in _find_workspace_api_manifest_paths(
        start=package_root
    ):
        try:
            manifest_spec = load_aware_api_toml_spec(toml_path=workspace_manifest_path)
        except Exception:
            continue
        workspace_package_name = (manifest_spec.api.package_name or "").strip()
        catalog = _load_api_catalog_from_manifest(manifest_path=workspace_manifest_path)
        workspace_api_catalogs.append((workspace_package_name, catalog))

    filtered_workspace_catalogs = tuple(
        (package_name, catalog)
        for package_name, catalog in workspace_api_catalogs
        if (
            catalog
            and (
                not dependency_package_name_keys
                or package_name.casefold() in dependency_package_name_keys
            )
        )
    )
    selected_workspace_catalogs = filtered_workspace_catalogs
    if dependency_package_name_keys and not selected_workspace_catalogs:
        selected_workspace_catalogs = tuple(
            (package_name, catalog)
            for package_name, catalog in workspace_api_catalogs
            if catalog
        )

    return ServiceDependencyScope(
        service_package_name=service_package_name,
        manifest_path=resolved_manifest_path,
        declared_api_package_names=declared_api_package_names,
        resolved_api_package_names=tuple(
            sorted(
                {
                    package_name
                    for package_name, _catalog in selected_workspace_catalogs
                    if package_name
                },
                key=str.casefold,
            )
        ),
        api_catalog=_merge_api_catalogs(
            catalogs=tuple(
                catalog for _package_name, catalog in selected_workspace_catalogs
            )
        ),
    )


__all__ = [
    "ServiceApiTruth",
    "ServiceDependencyScope",
    "load_service_dependency_scope",
]
