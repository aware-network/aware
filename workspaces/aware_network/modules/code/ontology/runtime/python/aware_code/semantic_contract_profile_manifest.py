from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast
import re
import tomllib

from aware_code.module_manifest.loader import AwareModuleTomlError

_MANIFEST_VERSION_KEY = "aware_semantic_contract_profile"
_PROFILE_KEY_RE = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")
_MODULE_ID_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PROVIDER_KEY_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_RUNTIME_IMPORT_MODE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_STATUS_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfileProviderSpec:
    module_id: str
    provider_key: str
    required: bool = True
    status: str = "active"


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfileDescriptorSpec:
    key: str
    package_key: str
    runtime_import_mode: str = "dynamic_contract_module"
    runtime_import_required: bool = True
    status: str = "active"


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfileManifestSpec:
    aware_semantic_contract_profile: int
    profile: CodeSemanticContractProfileDescriptorSpec
    providers: tuple[CodeSemanticContractProfileProviderSpec, ...]


def load_code_semantic_contract_profile_manifest(
    *,
    toml_path: Path,
) -> CodeSemanticContractProfileManifestSpec:
    path = toml_path.expanduser().resolve()
    if not path.is_file():
        raise AwareModuleTomlError(
            f"aware.semantic_contract_profile.toml not found: {path}"
        )
    try:
        raw_obj = cast(object, tomllib.loads(path.read_text(encoding="utf-8")))
    except tomllib.TOMLDecodeError as exc:
        raise AwareModuleTomlError(f"Failed to parse TOML at {path}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path}")
    _expect_keys(
        raw,
        required={_MANIFEST_VERSION_KEY, "profile", "providers"},
        optional=set(),
        ctx="root",
    )
    version = _expect_int(raw, _MANIFEST_VERSION_KEY, ctx="root")
    if version != 1:
        raise AwareModuleTomlError(
            f"{_MANIFEST_VERSION_KEY} must be 1 in {path}; got {version!r}"
        )
    profile = _parse_profile(raw.get("profile"))
    providers = _parse_providers(raw.get("providers"))
    return CodeSemanticContractProfileManifestSpec(
        aware_semantic_contract_profile=version,
        profile=profile,
        providers=providers,
    )


def _parse_profile(value: object) -> CodeSemanticContractProfileDescriptorSpec:
    tbl = _as_table(value, ctx="[profile]")
    _expect_keys(
        tbl,
        required={"key", "package_key"},
        optional={"runtime_import_mode", "runtime_import_required", "status"},
        ctx="[profile]",
    )
    key = _expect_str(tbl, "key", ctx="[profile]").strip()
    _validate_profile_key(key, ctx="[profile].key")
    package_key = _expect_str(tbl, "package_key", ctx="[profile]").strip()
    _validate_profile_key(package_key, ctx="[profile].package_key")
    runtime_import_mode = (
        _expect_opt_str(tbl, "runtime_import_mode", ctx="[profile]")
        or "dynamic_contract_module"
    ).strip()
    if not _RUNTIME_IMPORT_MODE_RE.fullmatch(runtime_import_mode):
        raise AwareModuleTomlError(
            "[profile].runtime_import_mode must match ^[a-z_][a-z0-9_]*$"
        )
    runtime_import_required = _expect_opt_bool(
        tbl,
        "runtime_import_required",
        ctx="[profile]",
    )
    status = (_expect_opt_str(tbl, "status", ctx="[profile]") or "active").strip()
    _validate_status(status, ctx="[profile].status")
    return CodeSemanticContractProfileDescriptorSpec(
        key=key,
        package_key=package_key,
        runtime_import_mode=runtime_import_mode,
        runtime_import_required=(
            True if runtime_import_required is None else runtime_import_required
        ),
        status=status,
    )


def _parse_providers(
    value: object,
) -> tuple[CodeSemanticContractProfileProviderSpec, ...]:
    provider_tables = _as_table_list(value, ctx="[[providers]]")
    if not provider_tables:
        raise AwareModuleTomlError("[[providers]] must include at least one provider")
    seen_provider_keys: set[str] = set()
    providers: list[CodeSemanticContractProfileProviderSpec] = []
    for index, provider_tbl in enumerate(provider_tables):
        ctx = f"providers[{index}]"
        _expect_keys(
            provider_tbl,
            required={"module_id", "provider_key"},
            optional={"required", "status"},
            ctx=ctx,
        )
        module_id = _expect_str(provider_tbl, "module_id", ctx=ctx).strip()
        if not _MODULE_ID_RE.fullmatch(module_id):
            raise AwareModuleTomlError(
                f"{ctx}.module_id must match ^[a-z_][a-z0-9_]*$"
            )
        provider_key = _expect_str(provider_tbl, "provider_key", ctx=ctx).strip()
        if not _PROVIDER_KEY_RE.fullmatch(provider_key):
            raise AwareModuleTomlError(
                f"{ctx}.provider_key must match ^[a-z_][a-z0-9_]*$"
            )
        if provider_key in seen_provider_keys:
            raise AwareModuleTomlError(
                f"[[providers]] declares duplicate provider_key {provider_key!r}"
            )
        seen_provider_keys.add(provider_key)
        required = _expect_opt_bool(provider_tbl, "required", ctx=ctx)
        status = (_expect_opt_str(provider_tbl, "status", ctx=ctx) or "active").strip()
        _validate_status(status, ctx=f"{ctx}.status")
        providers.append(
            CodeSemanticContractProfileProviderSpec(
                module_id=module_id,
                provider_key=provider_key,
                required=True if required is None else required,
                status=status,
            )
        )
    return tuple(providers)


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareModuleTomlError(f"Expected {ctx} to be a table/object")
    return cast(dict[str, object], value)


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise AwareModuleTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, dict):
            raise AwareModuleTomlError(f"Expected {ctx}[{index}] to be a table/object")
        tables.append(cast(dict[str, object], item))
    return tables


def _expect_keys(
    tbl: dict[str, object],
    *,
    required: set[str],
    optional: set[str],
    ctx: str,
) -> None:
    allowed = required | optional
    extra = set(tbl) - allowed
    missing = required - set(tbl)
    if extra:
        raise AwareModuleTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareModuleTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    value = root.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return value


def _expect_opt_str(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> str | None:
    value = root.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be a string or null")
    return value


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    value = root.get(key)
    if not isinstance(value, int):
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be an int")
    return value


def _expect_opt_bool(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> bool | None:
    value = root.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return value


def _validate_profile_key(value: str, *, ctx: str) -> None:
    if not _PROFILE_KEY_RE.fullmatch(value):
        raise AwareModuleTomlError(
            f"{ctx} must match ^[a-z_][a-z0-9_]*(\\.[a-z_][a-z0-9_]*)*$"
        )


def _validate_status(value: str, *, ctx: str) -> None:
    if not _STATUS_RE.fullmatch(value):
        raise AwareModuleTomlError(f"{ctx} must match ^[a-z_][a-z0-9_]*$")


__all__ = [
    "CodeSemanticContractProfileDescriptorSpec",
    "CodeSemanticContractProfileManifestSpec",
    "CodeSemanticContractProfileProviderSpec",
    "load_code_semantic_contract_profile_manifest",
]
