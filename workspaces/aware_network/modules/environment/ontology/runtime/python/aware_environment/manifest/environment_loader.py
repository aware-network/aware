"""Strict loader for `aware.environment.toml` -> AwareEnvironmentSpec."""

from __future__ import annotations

from pathlib import Path
import re
from typing import cast
from uuid import UUID

import tomllib

from aware_environment.manifest.environment_spec import (
    AwareEnvironmentBuildSpec,
    AwareEnvironmentDescriptorSpec,
    AwareEnvironmentSpec,
)


class AwareEnvironmentTomlError(ValueError):
    """Raised when `aware.environment.toml` fails strict validation."""


_HANDLE_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareEnvironmentTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def load_aware_environment_spec(*, toml_path: str | Path) -> AwareEnvironmentSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareEnvironmentTomlError(f"aware.environment.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        raise AwareEnvironmentTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")

    _expect_keys(
        raw,
        required={"aware", "environment"},
        optional={"build"},
        ctx="root",
    )
    aware_version = _expect_int(raw, "aware", ctx="root")
    if aware_version != 1:
        raise AwareEnvironmentTomlError(
            f"Unsupported aware.environment.toml version {aware_version}; expected 1"
        )

    env_tbl = _expect_table(raw, "environment", ctx="root")
    _expect_keys(
        env_tbl,
        required={"handle"},
        optional={
            "id",
            "title",
            "canonical_language",
            "modules",
            "ontologies",
            "base_environment_manifest_paths",
        },
        ctx="[environment]",
    )

    handle = _expect_str(env_tbl, "handle", ctx="[environment]").strip()
    _validate_handle(handle, ctx="[environment].handle")

    env_id = _expect_opt_str(env_tbl, "id", ctx="[environment]")
    if env_id is not None:
        env_id = env_id.strip()
        if not env_id:
            raise AwareEnvironmentTomlError(
                "[environment].id must be a non-empty string or null"
            )
        try:
            _ = UUID(env_id)
        except Exception as exc:
            raise AwareEnvironmentTomlError(
                f"Invalid UUID string for [environment].id: {env_id!r}"
            ) from exc

    title = _expect_opt_str(env_tbl, "title", ctx="[environment]")
    if title is not None and not title.strip():
        title = None

    canonical_language = (
        _expect_opt_str(env_tbl, "canonical_language", ctx="[environment]") or "aware"
    )
    canonical_language = canonical_language.strip()
    if not canonical_language:
        canonical_language = "aware"

    modules = _expect_opt_str_list(env_tbl, "modules", ctx="[environment]")
    cleaned: list[str] = []
    for i, m in enumerate(modules):
        mid = m.strip()
        if not mid:
            raise AwareEnvironmentTomlError(
                f"[environment].modules[{i}] must be a non-empty string"
            )
        _validate_handle(mid, ctx=f"[environment].modules[{i}]")
        cleaned.append(mid)
    deduped: list[str] = []
    seen: set[str] = set()
    for m in cleaned:
        if m in seen:
            continue
        seen.add(m)
        deduped.append(m)

    ontology_paths = _dedupe_ontology_manifest_paths(
        _expect_opt_str_list(env_tbl, "ontologies", ctx="[environment]"),
        label="[environment].ontologies",
    )
    if not deduped and not ontology_paths:
        raise AwareEnvironmentTomlError(
            "[environment] requires at least one module or ontology selector"
        )

    base_environment_manifest_paths = _dedupe_nonempty_string_list(
        _expect_opt_str_list(
            env_tbl,
            "base_environment_manifest_paths",
            ctx="[environment]",
        ),
        label="[environment].base_environment_manifest_paths",
    )

    build = _parse_build_spec(raw, path_label=str(p)) if "build" in raw else None

    return AwareEnvironmentSpec(
        aware=aware_version,
        environment=AwareEnvironmentDescriptorSpec(
            handle=handle,
            environment_config_id=env_id,
            title=title,
            canonical_language=canonical_language,
        ),
        build=build,
        modules=tuple(deduped),
        ontologies=tuple(ontology_paths),
        base_environment_manifest_paths=tuple(base_environment_manifest_paths),
    )


def _parse_build_spec(
    raw: dict[str, object],
    *,
    path_label: str,
) -> AwareEnvironmentBuildSpec:
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

    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "aware"
    sources_dir = sources_dir.strip()
    _validate_rel_path(sources_dir, ctx="[build].sources_dir")

    include_paths = _expect_opt_str_list(
        build_tbl,
        "include_paths",
        ctx="[build]",
    ) or ["**/*.aware"]
    exclude_paths = _expect_opt_str_list(
        build_tbl,
        "exclude_paths",
        ctx="[build]",
    )
    force_fresh_scan = _expect_opt_bool(
        build_tbl,
        "force_fresh_scan",
        ctx="[build]",
    )

    includes = tuple(
        _validate_rel_path(path.strip(), ctx=f"[build].include_paths[{index}]")
        for index, path in enumerate(include_paths)
    )
    excludes = tuple(
        _validate_rel_path(path.strip(), ctx=f"[build].exclude_paths[{index}]")
        for index, path in enumerate(exclude_paths)
    )
    if not includes:
        raise AwareEnvironmentTomlError(
            f"[build].include_paths must not be empty in {path_label}"
        )

    return AwareEnvironmentBuildSpec(
        sources_dir=sources_dir,
        include_paths=includes,
        exclude_paths=excludes,
        force_fresh_scan=True if force_fresh_scan is None else force_fresh_scan,
    )


def _expect_keys(
    tbl: dict[str, object], *, required: set[str], optional: set[str], ctx: str
) -> None:
    allowed = required | optional
    extra = set(tbl.keys()) - allowed
    missing = required - set(tbl.keys())
    if extra:
        raise AwareEnvironmentTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareEnvironmentTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    return _as_table(val, ctx=f"{ctx}.{key}")


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareEnvironmentTomlError(
            f"Expected {ctx}.{key} to be a non-empty string"
        )
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareEnvironmentTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareEnvironmentTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareEnvironmentTomlError(f"Expected {ctx}.{key} to be a bool")
    return val


def _expect_str_list(root: dict[str, object], key: str, *, ctx: str) -> list[str]:
    val = root.get(key)
    if not isinstance(val, list):
        raise AwareEnvironmentTomlError(f"Expected {ctx}.{key} to be a list[str]")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareEnvironmentTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _expect_opt_str_list(root: dict[str, object], key: str, *, ctx: str) -> list[str]:
    if key not in root:
        return []
    val = root.get(key)
    if not isinstance(val, list):
        raise AwareEnvironmentTomlError(f"Expected {ctx}.{key} to be a list[str]")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareEnvironmentTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _dedupe_nonempty_string_list(values: list[str], *, label: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for i, raw in enumerate(values):
        token = raw.strip()
        if not token:
            raise AwareEnvironmentTomlError(f"{label}[{i}] must be a non-empty string")
        if token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _dedupe_ontology_manifest_paths(values: list[str], *, label: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for i, raw in enumerate(values):
        token = raw.strip()
        if not token:
            raise AwareEnvironmentTomlError(f"{label}[{i}] must be a non-empty string")
        path = Path(token)
        if path.is_absolute() or ".." in path.parts:
            raise AwareEnvironmentTomlError(
                f"{label}[{i}] must be a workspace-relative path"
            )
        if path.name != "aware.ontology.toml":
            raise AwareEnvironmentTomlError(
                f"{label}[{i}] must point to aware.ontology.toml"
            )
        normalized = path.as_posix()
        if normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _validate_handle(value: str, *, ctx: str) -> None:
    if not _HANDLE_RE.match(value):
        raise AwareEnvironmentTomlError(
            f"{ctx} must match {_HANDLE_RE.pattern!r} (lowercase letters/digits, '-' or '_')"
        )


def _validate_rel_path(value: str, *, ctx: str) -> str:
    token = (value or "").strip()
    if not token:
        raise AwareEnvironmentTomlError(f"{ctx} must be a non-empty string")
    path = Path(token)
    if path.is_absolute() or ".." in path.parts:
        raise AwareEnvironmentTomlError(f"{ctx} must be a workspace-relative path")
    return path.as_posix()


__all__ = [
    "AwareEnvironmentTomlError",
    "load_aware_environment_spec",
]
