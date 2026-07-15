from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_node.manifest.spec import (
    AwareNodeCompilationMode,
    AwareNodeDependencyKind,
    AwareNodeTomlBuildSpec,
    AwareNodeTomlDependencySpec,
    AwareNodeTomlPackageSpec,
    AwareNodeTomlSpec,
)


class AwareNodeTomlError(ValueError):
    """Raised when `aware.node.toml` fails strict validation."""


def load_aware_node_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareNodeTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.node.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareNodeTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_node_toml_raw(raw, path_label=path_label)


def load_aware_node_toml_spec(*, toml_path: str | Path) -> AwareNodeTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareNodeTomlError(f"aware.node.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareNodeTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_node_toml_raw(raw, path_label=str(p))


def _parse_aware_node_toml_raw(
    raw: dict[str, object],
    *,
    path_label: str,
) -> AwareNodeTomlSpec:
    _expect_keys(
        raw,
        required={"aware_node", "node", "build"},
        optional={"dependencies"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_node", ctx="root")
    if spec_version != 1:
        raise AwareNodeTomlError(
            f"Unsupported aware.node.toml version {spec_version}; expected 1"
        )

    node_tbl = _expect_table(raw, "node", ctx="root")
    _expect_keys(
        node_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[node]",
    )
    package_name = _expect_str(node_tbl, "package_name", ctx="[node]")
    fqn_prefix = _expect_str(node_tbl, "fqn_prefix", ctx="[node]")
    version_number = _expect_opt_int(node_tbl, "version_number", ctx="[node]") or 1
    title = _expect_opt_str(node_tbl, "title", ctx="[node]")
    description = _expect_opt_str(node_tbl, "description", ctx="[node]")

    _validate_package_name(package_name, ctx="[node].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[node].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={
            "sources_dir",
            "include_paths",
            "exclude_paths",
            "force_fresh_scan",
            "compilation_mode",
        },
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "nodes"
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or [
        "**/*.aware"
    ]
    exclude_paths = (
        _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    )
    force_fresh_scan = _expect_opt_bool(build_tbl, "force_fresh_scan", ctx="[build]")
    if force_fresh_scan is None:
        force_fresh_scan = True
    compilation_mode = _expect_opt_compilation_mode(
        build_tbl, "compilation_mode", ctx="[build]"
    )
    if compilation_mode is None:
        compilation_mode = AwareNodeCompilationMode.raw_xor

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for index, path in enumerate(include_paths):
        _validate_rel_path(path, ctx=f"[build].include_paths[{index}]")
    for index, path in enumerate(exclude_paths):
        _validate_rel_path(path, ctx=f"[build].exclude_paths[{index}]")

    dependencies = _parse_dependencies(raw=raw, path_label=path_label)

    return AwareNodeTomlSpec(
        aware_node=spec_version,
        node=AwareNodeTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareNodeTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
            compilation_mode=compilation_mode,
        ),
        dependencies=dependencies,
    )


def _parse_dependencies(
    *,
    raw: dict[str, object],
    path_label: str,
) -> list[AwareNodeTomlDependencySpec]:
    deps_tbl = _as_table_list(raw.get("dependencies", []), ctx="[[dependencies]]")
    dependencies: list[AwareNodeTomlDependencySpec] = []
    seen_deps: set[str] = set()
    for index, dep_tbl in enumerate(deps_tbl):
        ctx = f"dependencies[{index}]"
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={"version_number", "kind"},
            ctx=f"[[dependencies]] (index={index})",
        )
        dep_package_name = _expect_str(dep_tbl, "package_name", ctx=ctx)
        dep_version_number = _expect_opt_int(dep_tbl, "version_number", ctx=ctx)
        dep_kind = _expect_opt_dependency_kind(dep_tbl, "kind", ctx=ctx)
        if dep_kind is None:
            dep_kind = AwareNodeDependencyKind.package

        _validate_package_name(dep_package_name, ctx=f"{ctx}.package_name")
        if dep_package_name in seen_deps:
            raise AwareNodeTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at {ctx} in {path_label}"
            )
        seen_deps.add(dep_package_name)
        dependencies.append(
            AwareNodeTomlDependencySpec(
                package_name=dep_package_name,
                version_number=dep_version_number,
                kind=dep_kind,
            )
        )
    return dependencies


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareNodeTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareNodeTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    items = cast(list[object], value)
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise AwareNodeTomlError(f"Expected {ctx}[{index}] to be a table/object")
        payload = cast(dict[object, object], item)
        tables.append({str(k): v for k, v in payload.items()})
    return tables


def _expect_keys(
    table: dict[str, object], *, required: set[str], optional: set[str], ctx: str
) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareNodeTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareNodeTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareNodeTomlError(f"Expected {ctx}.{key} to be a table; got {type(val)}")
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareNodeTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareNodeTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareNodeTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareNodeTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareNodeTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(
    root: dict[str, object], key: str, *, ctx: str
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareNodeTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for index, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareNodeTomlError(f"Expected {ctx}.{key}[{index}] to be a string")
        out.append(item)
    return out


def _expect_opt_compilation_mode(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareNodeCompilationMode | None:
    val = _expect_opt_str(root, key, ctx=ctx)
    if val is None:
        return None
    try:
        return AwareNodeCompilationMode(val)
    except ValueError as exc:
        raise AwareNodeTomlError(
            f"{ctx}.{key} must be one of {[item.value for item in AwareNodeCompilationMode]}"
        ) from exc


def _expect_opt_dependency_kind(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareNodeDependencyKind | None:
    val = _expect_opt_str(root, key, ctx=ctx)
    if val is None:
        return None
    try:
        return AwareNodeDependencyKind(val)
    except ValueError as exc:
        raise AwareNodeTomlError(
            f"{ctx}.{key} must be one of {[item.value for item in AwareNodeDependencyKind]}"
        ) from exc


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareNodeTomlError(
            f"{ctx} must not contain '.' (single-segment namespace); got {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise AwareNodeTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareNodeTomlError(
            f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}"
        )


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareNodeTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareNodeTomlError(
            f"{ctx} must be repo-relative (not absolute): {value!r}"
        )
    if ".." in p.parts:
        raise AwareNodeTomlError(f"{ctx} must not contain '..': {value!r}")


__all__ = [
    "AwareNodeTomlError",
    "load_aware_node_toml_spec",
    "load_aware_node_toml_spec_from_text",
]
