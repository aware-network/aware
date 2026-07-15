from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from uuid import UUID


BUNDLE_CONTRACT_FILENAME = "bundle.contract.json"
MODULE_EVOLUTION_RECORD_RELATIVE_PATH = (
    Path(".aware") / "compiler" / "module.evolution.record.json"
)


@dataclass(frozen=True, slots=True)
class EnvironmentBundleModuleServiceProviderVectorEntry:
    module_id: str
    provider_modules: tuple[str, ...] = ()

    def to_json_object(self) -> dict[str, object]:
        return {
            "module_id": self.module_id,
            "provider_modules": list(self.provider_modules),
        }


@dataclass(frozen=True, slots=True)
class EnvironmentBundleContract:
    schema_version: int
    bundle_head_id: str
    bundle_manifest_sha256: str
    bundle_manifest_size_bytes: int
    release_identity: object | None
    environment_config_id: str | None = None
    environment_service_provider_modules: tuple[str, ...] = ()
    environment_module_service_provider_vector: tuple[
        EnvironmentBundleModuleServiceProviderVectorEntry, ...
    ] = ()

    def to_json_object(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "bundle_head_id": self.bundle_head_id,
            "bundle_manifest_sha256": self.bundle_manifest_sha256,
            "bundle_manifest_size_bytes": self.bundle_manifest_size_bytes,
            "release_identity": self.release_identity,
            "environment_service_provider_modules": list(
                self.environment_service_provider_modules
            ),
            "environment_module_service_provider_vector": [
                entry.to_json_object()
                for entry in self.environment_module_service_provider_vector
            ],
        }
        if self.environment_config_id is not None:
            payload["environment_config_id"] = self.environment_config_id
        return payload


def _sha256_hex(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _canonical_json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _resolve_bundle_root_from_manifest_path(manifest_path: Path) -> Path:
    parts = manifest_path.parts
    reversed_parts = tuple(reversed(parts))
    for marker in (".aware", "_aware"):
        try:
            aware_idx = len(parts) - 1 - reversed_parts.index(marker)
        except ValueError:
            continue
        return Path(*parts[:aware_idx]).resolve()
    return manifest_path.parent.resolve()


def bundle_contract_path_for_manifest(*, manifest_path: Path) -> Path:
    return (manifest_path.parent / BUNDLE_CONTRACT_FILENAME).resolve()


def _optional_record_str(payload: dict[str, object], *, field: str) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str):
        return None
    token = value.strip()
    if not token:
        return None
    return token


def _optional_record_int(payload: dict[str, object], *, field: str) -> int | None:
    value = payload.get(field)
    if isinstance(value, int):
        return value
    return None


def _required_record_str(payload: dict[str, object], *, field: str, path: Path) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid module evolution record field '{field}' at {path}")
    return value.strip()


def _optional_record_str_list(payload: dict[str, object], *, field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            continue
        token = entry.strip()
        if not token:
            continue
        normalized.append(token)
    return normalized


def _optional_record_contract_vector(
    payload: dict[str, object],
) -> list[dict[str, str]]:
    value = payload.get("public_structure_contract_vector")
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, str]] = []
    for raw_entry in value:
        if not isinstance(raw_entry, dict):
            continue
        entry = dict(raw_entry)
        package_name = entry.get("package_name")
        package_kind = entry.get("package_kind")
        contract_hash = entry.get("contract_hash")
        compatibility_class = entry.get("compatibility_class")
        if (
            not isinstance(package_name, str)
            or not package_name.strip()
            or not isinstance(package_kind, str)
            or not package_kind.strip()
            or not isinstance(contract_hash, str)
            or not contract_hash.strip()
            or not isinstance(compatibility_class, str)
            or not compatibility_class.strip()
        ):
            continue
        normalized.append(
            {
                "package_name": package_name.strip(),
                "package_kind": package_kind.strip(),
                "contract_hash": contract_hash.strip(),
                "compatibility_class": compatibility_class.strip(),
            }
        )
    normalized.sort(
        key=lambda item: (
            item["package_name"],
            item["package_kind"],
            item["contract_hash"],
            item["compatibility_class"],
        )
    )
    return normalized


def _normalize_module_evolution_record(*, path: Path) -> dict[str, object]:
    decoded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError(f"module evolution record root must be object: {path}")
    payload = dict(decoded)
    return {
        "schema_version": _optional_record_int(payload, field="schema_version"),
        "source_stage": _optional_record_str(payload, field="source_stage"),
        "package_name": _required_record_str(
            payload,
            field="package_name",
            path=path,
        ),
        "package_kind": _required_record_str(
            payload,
            field="package_kind",
            path=path,
        ),
        "package_version_number": _optional_record_int(
            payload,
            field="package_version_number",
        ),
        "dependency_package_names": _optional_record_str_list(
            payload,
            field="dependency_package_names",
        ),
        "ontology_anchor_package_name": _optional_record_str(
            payload,
            field="ontology_anchor_package_name",
        ),
        "ontology_anchor_contract_hash": _optional_record_str(
            payload,
            field="ontology_anchor_contract_hash",
        ),
        "ontology_anchor_commit_id": _optional_record_str(
            payload,
            field="ontology_anchor_commit_id",
        ),
        "runtime_revision": _optional_record_int(payload, field="runtime_revision"),
        "representation_revision": _optional_record_int(
            payload,
            field="representation_revision",
        ),
        "public_structure_contract_vector": _optional_record_contract_vector(payload),
    }


def _candidate_module_evolution_record_paths(
    *, manifest_path: Path
) -> tuple[Path, ...]:
    bundle_root = _resolve_bundle_root_from_manifest_path(manifest_path)
    candidates: list[Path] = [bundle_root / MODULE_EVOLUTION_RECORD_RELATIVE_PATH]
    try:
        decoded = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        decoded = None
    if isinstance(decoded, dict):
        raw_modules = decoded.get("modules")
        if isinstance(raw_modules, list):
            for raw_entry in raw_modules:
                if not isinstance(raw_entry, dict):
                    continue
                module_manifest_raw = raw_entry.get("manifest_path")
                if (
                    not isinstance(module_manifest_raw, str)
                    or not module_manifest_raw.strip()
                ):
                    continue
                module_manifest_path = Path(module_manifest_raw.strip()).expanduser()
                if not module_manifest_path.is_absolute():
                    module_manifest_path = (
                        bundle_root / module_manifest_path
                    ).resolve()
                else:
                    module_manifest_path = module_manifest_path.resolve()
                module_root = _resolve_bundle_root_from_manifest_path(
                    module_manifest_path
                )
                candidates.append(module_root / MODULE_EVOLUTION_RECORD_RELATIVE_PATH)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return tuple(deduped)


def _build_release_identity(
    *,
    manifest_path: Path,
    environment_config_id: UUID,
) -> dict[str, object] | None:
    records: list[dict[str, object]] = []
    for candidate in _candidate_module_evolution_record_paths(
        manifest_path=manifest_path
    ):
        if not candidate.is_file():
            continue
        records.append(_normalize_module_evolution_record(path=candidate))
    if not records:
        return None
    records.sort(
        key=lambda item: (
            str(item.get("package_name") or ""),
            str(item.get("package_kind") or ""),
            str(item.get("package_version_number") or ""),
            str(item.get("ontology_anchor_contract_hash") or ""),
        )
    )
    return {
        "schema_version": 1,
        "environment_config_id": str(environment_config_id),
        "module_evolution_record_vector": records,
    }


def _dedupe_nonempty_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for raw in values:
        token = str(raw).strip()
        if not token or token in seen:
            continue
        deduped.append(token)
        seen.add(token)
    return deduped


def _normalize_provider_modules(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            continue
        token = entry.strip()
        if token:
            out.append(token)
    return _dedupe_nonempty_strings(out)


def _resolve_environment_service_provider_contract(
    *,
    manifest_path: Path,
) -> tuple[list[str], list[EnvironmentBundleModuleServiceProviderVectorEntry]]:
    try:
        decoded = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return ([], [])
    if not isinstance(decoded, dict):
        return ([], [])

    payload = dict(decoded)
    aggregate = _normalize_provider_modules(
        payload.get("environment_service_provider_modules")
    )
    module_vector: list[EnvironmentBundleModuleServiceProviderVectorEntry] = []
    raw_modules = payload.get("modules")
    if isinstance(raw_modules, list):
        for raw_entry in raw_modules:
            if not isinstance(raw_entry, dict):
                continue
            module_entry = dict(raw_entry)
            module_id_raw = module_entry.get("module_id")
            if not isinstance(module_id_raw, str) or not module_id_raw.strip():
                continue
            provider_modules = _normalize_provider_modules(
                module_entry.get("environment_service_provider_modules")
            )
            module_vector.append(
                EnvironmentBundleModuleServiceProviderVectorEntry(
                    module_id=module_id_raw.strip(),
                    provider_modules=tuple(provider_modules),
                )
            )

    if not aggregate and module_vector:
        combined: list[str] = []
        for entry in module_vector:
            combined.extend(entry.provider_modules)
        aggregate = _dedupe_nonempty_strings(combined)

    return (aggregate, module_vector)


def build_bundle_contract_for_manifest(
    *,
    manifest_path: Path,
    environment_config_id: UUID,
    release_identity: object | None = None,
) -> EnvironmentBundleContract:
    resolved_manifest = manifest_path.resolve()
    manifest_sha256 = _sha256_hex(resolved_manifest)
    identity = (
        release_identity
        if release_identity is not None
        else _build_release_identity(
            manifest_path=resolved_manifest,
            environment_config_id=environment_config_id,
        )
    )
    (
        environment_service_provider_modules,
        environment_module_service_provider_vector,
    ) = _resolve_environment_service_provider_contract(
        manifest_path=resolved_manifest,
    )
    if identity is None:
        head_id = manifest_sha256
    else:
        head_id = hashlib.sha256(
            _canonical_json_bytes(
                {
                    "schema_version": 1,
                    "manifest_sha256": manifest_sha256,
                    "release_identity": identity,
                }
            )
        ).hexdigest()
    return EnvironmentBundleContract(
        schema_version=1,
        environment_config_id=str(environment_config_id),
        bundle_head_id=head_id,
        bundle_manifest_sha256=manifest_sha256,
        bundle_manifest_size_bytes=resolved_manifest.stat().st_size,
        release_identity=identity,
        environment_service_provider_modules=tuple(
            environment_service_provider_modules
        ),
        environment_module_service_provider_vector=tuple(
            environment_module_service_provider_vector
        ),
    )


def write_bundle_contract_for_manifest(
    *,
    manifest_path: Path,
    environment_config_id: UUID,
    release_identity: object | None = None,
) -> tuple[Path, EnvironmentBundleContract]:
    contract = build_bundle_contract_for_manifest(
        manifest_path=manifest_path,
        environment_config_id=environment_config_id,
        release_identity=release_identity,
    )
    output_path = bundle_contract_path_for_manifest(manifest_path=manifest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = contract.to_json_object()
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path, contract


def load_bundle_contract_for_manifest(
    *,
    manifest_path: Path,
) -> EnvironmentBundleContract | None:
    contract_path = bundle_contract_path_for_manifest(manifest_path=manifest_path)
    if not contract_path.is_file():
        return None
    decoded = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError(f"Bundle contract root must be object: {contract_path}")
    schema_version = decoded.get("schema_version")
    if not isinstance(schema_version, int):
        raise ValueError(f"bundle.contract schema_version must be int: {contract_path}")
    bundle_head_id = decoded.get("bundle_head_id")
    if not isinstance(bundle_head_id, str) or not bundle_head_id.strip():
        raise ValueError(f"bundle.contract missing bundle_head_id: {contract_path}")
    bundle_manifest_sha256 = decoded.get("bundle_manifest_sha256")
    if (
        not isinstance(bundle_manifest_sha256, str)
        or not bundle_manifest_sha256.strip()
    ):
        raise ValueError(
            f"bundle.contract missing bundle_manifest_sha256: {contract_path}"
        )
    bundle_manifest_size_bytes = decoded.get("bundle_manifest_size_bytes")
    if not isinstance(bundle_manifest_size_bytes, int):
        raise ValueError(
            f"bundle.contract missing bundle_manifest_size_bytes: {contract_path}"
        )
    environment_config_id_raw = decoded.get("environment_config_id")
    environment_config_id = (
        environment_config_id_raw.strip()
        if isinstance(environment_config_id_raw, str)
        and environment_config_id_raw.strip()
        else None
    )
    environment_service_provider_modules = _normalize_provider_modules(
        decoded.get("environment_service_provider_modules")
    )
    module_vector: list[EnvironmentBundleModuleServiceProviderVectorEntry] = []
    raw_module_vector = decoded.get("environment_module_service_provider_vector")
    if isinstance(raw_module_vector, list):
        for raw_entry in raw_module_vector:
            if not isinstance(raw_entry, dict):
                continue
            entry = dict(raw_entry)
            module_id = entry.get("module_id")
            if not isinstance(module_id, str) or not module_id.strip():
                continue
            provider_modules = _normalize_provider_modules(
                entry.get("provider_modules")
            )
            module_vector.append(
                EnvironmentBundleModuleServiceProviderVectorEntry(
                    module_id=module_id.strip(),
                    provider_modules=tuple(provider_modules),
                )
            )
    if not environment_service_provider_modules and module_vector:
        combined: list[str] = []
        for entry in module_vector:
            combined.extend(entry.provider_modules)
        environment_service_provider_modules = _dedupe_nonempty_strings(combined)
    return EnvironmentBundleContract(
        schema_version=schema_version,
        environment_config_id=environment_config_id,
        bundle_head_id=bundle_head_id.strip(),
        bundle_manifest_sha256=bundle_manifest_sha256.strip(),
        bundle_manifest_size_bytes=bundle_manifest_size_bytes,
        release_identity=decoded.get("release_identity"),
        environment_service_provider_modules=tuple(
            environment_service_provider_modules
        ),
        environment_module_service_provider_vector=tuple(module_vector),
    )


__all__ = [
    "BUNDLE_CONTRACT_FILENAME",
    "EnvironmentBundleContract",
    "EnvironmentBundleModuleServiceProviderVectorEntry",
    "build_bundle_contract_for_manifest",
    "bundle_contract_path_for_manifest",
    "load_bundle_contract_for_manifest",
    "write_bundle_contract_for_manifest",
]
