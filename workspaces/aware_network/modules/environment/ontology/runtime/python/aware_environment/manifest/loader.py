from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_environment.manifest.spec import (
    AwareEnvironmentProfileTomlBuildSpec,
    AwareEnvironmentProfileTomlDependencySpec,
    AwareEnvironmentProfileTomlPackageSpec,
    AwareEnvironmentProfileTomlSpec,
)


class AwareEnvironmentProfileTomlError(ValueError):
    """Raised when `aware.environment.profile.toml` fails strict validation."""


def load_aware_environment_profile_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareEnvironmentProfileTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.environment.profile.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareEnvironmentProfileTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_environment_profile_toml_raw(raw, path_label=path_label)


def load_aware_environment_profile_toml_spec(
    *,
    toml_path: str | Path,
) -> AwareEnvironmentProfileTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareEnvironmentProfileTomlError(
            f"aware.environment.profile.toml not found: {p}"
        )

    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareEnvironmentProfileTomlError(
            f"Failed to parse TOML at {p}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_environment_profile_toml_raw(raw, path_label=str(p))


def _parse_aware_environment_profile_toml_raw(
    raw: dict[str, object],
    *,
    path_label: str,
) -> AwareEnvironmentProfileTomlSpec:
    _expect_keys(
        raw,
        required={"aware_environment_profile", "environment_profile", "build"},
        optional={"dependencies"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_environment_profile", ctx="root")
    if spec_version != 1:
        raise AwareEnvironmentProfileTomlError(
            "Unsupported aware.environment.profile.toml version "
            f"{spec_version}; expected 1"
        )

    profile_tbl = _expect_table(raw, "environment_profile", ctx="root")
    _expect_keys(
        profile_tbl,
        required={"package_name", "profile_key", "environment_handle"},
        optional={"version_number", "title", "description"},
        ctx="[environment_profile]",
    )
    package_name = _expect_str(
        profile_tbl,
        "package_name",
        ctx="[environment_profile]",
    )
    profile_key = _expect_str(
        profile_tbl,
        "profile_key",
        ctx="[environment_profile]",
    )
    environment_handle = _expect_str(
        profile_tbl,
        "environment_handle",
        ctx="[environment_profile]",
    )
    version_number = (
        _expect_opt_int(profile_tbl, "version_number", ctx="[environment_profile]") or 1
    )
    title = _expect_opt_str(profile_tbl, "title", ctx="[environment_profile]")
    description = _expect_opt_str(
        profile_tbl,
        "description",
        ctx="[environment_profile]",
    )

    _validate_symbol(package_name, ctx="[environment_profile].package_name")
    _validate_symbol(profile_key, ctx="[environment_profile].profile_key")
    _validate_symbol(
        environment_handle,
        ctx="[environment_profile].environment_handle",
    )

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={
            "sources_dir",
            "include_paths",
            "exclude_paths",
            "force_fresh_scan",
        },
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "profiles"
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or [
        "**/*.aware"
    ]
    exclude_paths = (
        _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    )
    force_fresh_scan = _expect_opt_bool(
        build_tbl,
        "force_fresh_scan",
        ctx="[build]",
    )

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for index, include_path in enumerate(include_paths):
        _validate_rel_path(include_path, ctx=f"[build].include_paths[{index}]")
    for index, exclude_path in enumerate(exclude_paths):
        _validate_rel_path(exclude_path, ctx=f"[build].exclude_paths[{index}]")

    dependencies: list[AwareEnvironmentProfileTomlDependencySpec] = []
    seen_dependencies: set[str] = set()
    for index, dep_tbl in enumerate(
        _as_table_list(raw.get("dependencies", []), ctx="[[dependencies]]")
    ):
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={"version_number", "expected_hash_sha256"},
            ctx=f"[[dependencies]] (index={index})",
        )
        dep_package_name = _expect_str(
            dep_tbl,
            "package_name",
            ctx=f"dependencies[{index}]",
        )
        _validate_symbol(dep_package_name, ctx=f"dependencies[{index}].package_name")
        if dep_package_name in seen_dependencies:
            raise AwareEnvironmentProfileTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at "
                f"dependencies[{index}] in {path_label}"
            )
        seen_dependencies.add(dep_package_name)
        dependencies.append(
            AwareEnvironmentProfileTomlDependencySpec(
                package_name=dep_package_name,
                version_number=_expect_opt_int(
                    dep_tbl,
                    "version_number",
                    ctx=f"dependencies[{index}]",
                ),
                expected_hash_sha256=_expect_opt_str(
                    dep_tbl,
                    "expected_hash_sha256",
                    ctx=f"dependencies[{index}]",
                ),
            )
        )

    return AwareEnvironmentProfileTomlSpec(
        aware_environment_profile=spec_version,
        environment_profile=AwareEnvironmentProfileTomlPackageSpec(
            package_name=package_name,
            profile_key=profile_key,
            environment_handle=environment_handle,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareEnvironmentProfileTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=True if force_fresh_scan is None else force_fresh_scan,
        ),
        dependencies=dependencies,
    )


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareEnvironmentProfileTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx} to be an array of tables"
        )
    tables: list[dict[str, object]] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, dict):
            raise AwareEnvironmentProfileTomlError(
                f"Expected {ctx}[{index}] to be a table/object"
            )
        payload = cast(dict[object, object], item)
        tables.append({str(k): v for k, v in payload.items()})
    return tables


def _expect_keys(
    table: dict[str, object],
    *,
    required: set[str],
    optional: set[str],
    ctx: str,
) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareEnvironmentProfileTomlError(
            f"Unknown keys in {ctx}: {sorted(extra)}"
        )
    if missing:
        raise AwareEnvironmentProfileTomlError(
            f"Missing keys in {ctx}: {sorted(missing)}"
        )


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx}.{key} to be a table; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx}.{key} to be a non-empty string"
        )
    return val.strip()


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx}.{key} to be a string or null"
        )
    return val.strip() or None


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareEnvironmentProfileTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx}.{key} to be an int or null"
        )
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx}.{key} to be a bool or null"
        )
    return val


def _expect_opt_str_list(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx}.{key} to be a string list"
        )
    out: list[str] = []
    for index, item in enumerate(cast(list[object], val)):
        if not isinstance(item, str) or not item.strip():
            raise AwareEnvironmentProfileTomlError(
                f"Expected {ctx}.{key}[{index}] to be a non-empty string"
            )
        out.append(item.strip())
    return out


def _validate_symbol(value: str, *, ctx: str) -> None:
    if not value.strip():
        raise AwareEnvironmentProfileTomlError(f"Expected non-empty {ctx}")
    if any(ch.isspace() for ch in value):
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx} to be a compact symbol; got {value!r}"
        )


def _validate_rel_path(value: str, *, ctx: str) -> None:
    if not value.strip():
        raise AwareEnvironmentProfileTomlError(f"Expected non-empty {ctx}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise AwareEnvironmentProfileTomlError(
            f"Expected {ctx} to be a safe relative path; got {value!r}"
        )


__all__ = [
    "AwareEnvironmentProfileTomlError",
    "load_aware_environment_profile_toml_spec",
    "load_aware_environment_profile_toml_spec_from_text",
]
