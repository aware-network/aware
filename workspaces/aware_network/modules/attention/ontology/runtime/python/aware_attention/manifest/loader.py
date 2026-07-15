from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_attention.manifest.spec import (
    AwareAttentionTomlBuildSpec,
    AwareAttentionTomlPackageSpec,
    AwareAttentionTomlSpec,
)


class AwareAttentionTomlError(ValueError):
    """Raised when `aware.attention.toml` fails strict validation."""


def load_aware_attention_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareAttentionTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.attention.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareAttentionTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_attention_toml_raw(raw)


def load_aware_attention_toml_spec(
    *,
    toml_path: str | Path,
) -> AwareAttentionTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareAttentionTomlError(f"aware.attention.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareAttentionTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_attention_toml_raw(raw)


def _parse_aware_attention_toml_raw(
    raw: dict[str, object],
) -> AwareAttentionTomlSpec:
    _expect_keys(
        raw,
        required={"aware_attention", "attention", "build"},
        optional=set(),
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_attention", ctx="root")
    if spec_version != 1:
        raise AwareAttentionTomlError(
            f"Unsupported aware.attention.toml version {spec_version}; expected 1"
        )

    attention_tbl = _expect_table(raw, "attention", ctx="root")
    _expect_keys(
        attention_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[attention]",
    )
    package_name = _expect_str(attention_tbl, "package_name", ctx="[attention]")
    fqn_prefix = _expect_str(attention_tbl, "fqn_prefix", ctx="[attention]")
    version_number = (
        _expect_opt_int(attention_tbl, "version_number", ctx="[attention]") or 1
    )
    title = _expect_opt_str(attention_tbl, "title", ctx="[attention]")
    description = _expect_opt_str(attention_tbl, "description", ctx="[attention]")

    _validate_package_name(package_name, ctx="[attention].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[attention].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={
            "anchor_path",
            "sources_dir",
            "include_paths",
            "exclude_paths",
            "force_fresh_scan",
            "frame_mode",
        },
        ctx="[build]",
    )
    anchor_path = _expect_opt_str(build_tbl, "anchor_path", ctx="[build]")
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "."
    include_paths = (
        _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]")
        or ["**/*.aware"]
    )
    exclude_paths = (
        _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    )
    force_fresh_scan = _expect_opt_bool(
        build_tbl,
        "force_fresh_scan",
        ctx="[build]",
    )
    frame_mode = _expect_opt_str(build_tbl, "frame_mode", ctx="[build]") or "vertical"

    if anchor_path is not None:
        _validate_rel_path(anchor_path, ctx="[build].anchor_path")
    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for index, include_path in enumerate(include_paths):
        _validate_rel_path(include_path, ctx=f"[build].include_paths[{index}]")
    for index, exclude_path in enumerate(exclude_paths):
        _validate_rel_path(exclude_path, ctx=f"[build].exclude_paths[{index}]")
    _validate_symbol(frame_mode, ctx="[build].frame_mode")

    return AwareAttentionTomlSpec(
        aware_attention=spec_version,
        attention=AwareAttentionTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareAttentionTomlBuildSpec(
            anchor_path=anchor_path,
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=True if force_fresh_scan is None else force_fresh_scan,
            frame_mode=frame_mode,
        ),
    )


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareAttentionTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


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
        raise AwareAttentionTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareAttentionTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareAttentionTomlError(
            f"Expected {ctx}.{key} to be a table; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareAttentionTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareAttentionTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareAttentionTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareAttentionTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareAttentionTomlError(f"Expected {ctx}.{key} to be a bool or null")
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
        raise AwareAttentionTomlError(
            f"Expected {ctx}.{key} to be a list[str] or null"
        )
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareAttentionTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _validate_package_name(value: str, *, ctx: str) -> None:
    if not value.strip():
        raise AwareAttentionTomlError(f"{ctx} must be non-empty")
    for char in value:
        if not (char.islower() or char.isdigit() or char in {"-", "_"}):
            raise AwareAttentionTomlError(
                f"{ctx} must contain only lowercase letters, digits, '-' or '_'"
            )


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    _validate_symbol_ref(value, ctx=ctx)


def _validate_rel_path(value: str, *, ctx: str) -> None:
    normalized = value.strip()
    if not normalized:
        raise AwareAttentionTomlError(f"{ctx} must be a non-empty relative path")
    token = Path(normalized)
    if token.is_absolute():
        raise AwareAttentionTomlError(f"{ctx} must be relative, not absolute")
    if ".." in token.parts:
        raise AwareAttentionTomlError(f"{ctx} must not contain '..'")


def _validate_symbol(value: str, *, ctx: str) -> None:
    _validate_symbol_ref(value, ctx=ctx)


def _validate_symbol_ref(value: str, *, ctx: str) -> None:
    if not value or any(char.isspace() for char in value):
        raise AwareAttentionTomlError(
            f"{ctx} must be a non-empty token without whitespace"
        )
    for char in value:
        if not (char.isalnum() or char in {"_", "-", "."}):
            raise AwareAttentionTomlError(
                f"{ctx} must contain only letters, digits, '_', '-', or '.'"
            )


__all__ = [
    "AwareAttentionTomlError",
    "load_aware_attention_toml_spec",
    "load_aware_attention_toml_spec_from_text",
]
