from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_interface.manifest.interface_spec import (
    AwareInterfaceCompilationMode,
    AwareInterfaceDependencyKind,
    AwareInterfaceTomlBuildSpec,
    AwareInterfaceTomlDartSpec,
    AwareInterfaceTomlDependencySpec,
    AwareInterfaceTomlPackageSpec,
    AwareInterfaceTomlSpec,
)


class AwareInterfaceTomlError(ValueError):
    """Raised when `aware.interface.toml` fails strict validation."""


def load_aware_interface_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareInterfaceTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.interface.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareInterfaceTomlError(f"Failed to parse TOML at {path_label}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_interface_toml_raw(raw, path_label=path_label)


def load_aware_interface_toml_spec(*, toml_path: str | Path) -> AwareInterfaceTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareInterfaceTomlError(f"aware.interface.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareInterfaceTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_interface_toml_raw(raw, path_label=str(p))


def _parse_aware_interface_toml_raw(
    raw: dict[str, object],
    *,
    path_label: str,
) -> AwareInterfaceTomlSpec:
    _expect_keys(
        raw,
        required={"aware_interface", "interface", "build"},
        optional={"dart", "dependencies"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_interface", ctx="root")
    if spec_version != 1:
        raise AwareInterfaceTomlError(
            f"Unsupported aware.interface.toml version {spec_version}; expected 1"
        )

    interface_tbl = _expect_table(raw, "interface", ctx="root")
    _expect_keys(
        interface_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[interface]",
    )
    package_name = _expect_str(interface_tbl, "package_name", ctx="[interface]")
    fqn_prefix = _expect_str(interface_tbl, "fqn_prefix", ctx="[interface]")
    version_number = _expect_opt_int(interface_tbl, "version_number", ctx="[interface]") or 1
    title = _expect_opt_str(interface_tbl, "title", ctx="[interface]")
    description = _expect_opt_str(interface_tbl, "description", ctx="[interface]")

    _validate_package_name(package_name, ctx="[interface].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[interface].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required={"config_bundle_path"},
        optional={"sources_dir", "include_paths", "exclude_paths", "force_fresh_scan", "compilation_mode"},
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "."
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or ["**/*.aware"]
    exclude_paths = _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    force_fresh_scan = _expect_opt_bool(build_tbl, "force_fresh_scan", ctx="[build]")
    config_bundle_path = _expect_str(build_tbl, "config_bundle_path", ctx="[build]")
    compilation_mode_token = _expect_opt_str(build_tbl, "compilation_mode", ctx="[build]") or "raw_xor"

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for index, include_path in enumerate(include_paths):
        _validate_rel_path(include_path, ctx=f"[build].include_paths[{index}]")
    for index, exclude_path in enumerate(exclude_paths):
        _validate_rel_path(exclude_path, ctx=f"[build].exclude_paths[{index}]")
    _validate_rel_path(config_bundle_path, ctx="[build].config_bundle_path")

    try:
        compilation_mode = AwareInterfaceCompilationMode(compilation_mode_token)
    except ValueError as exc:
        raise AwareInterfaceTomlError(
            "[build].compilation_mode must be one of "
            + f"{[item.value for item in AwareInterfaceCompilationMode]}; got {compilation_mode_token!r}"
        ) from exc

    dart_spec = None
    if "dart" in raw:
        dart_tbl = _expect_table(raw, "dart", ctx="root")
        _expect_keys(
            dart_tbl,
            required={"package_path", "package_name"},
            optional=set(),
            ctx="[dart]",
        )
        dart_package_path = _expect_str(dart_tbl, "package_path", ctx="[dart]")
        dart_package_name = _expect_str(dart_tbl, "package_name", ctx="[dart]")
        _validate_rel_path(dart_package_path, ctx="[dart].package_path")
        _validate_dart_package_name(dart_package_name, ctx="[dart].package_name")
        dart_spec = AwareInterfaceTomlDartSpec(
            package_path=dart_package_path,
            package_name=dart_package_name,
        )

    dependencies_raw = raw.get("dependencies", [])
    dependencies_list = _expect_list_of_tables(dependencies_raw, ctx="[[dependencies]]")
    dependencies: list[AwareInterfaceTomlDependencySpec] = []
    for index, dep_tbl in enumerate(dependencies_list):
        dep_ctx = f"[[dependencies]][{index}]"
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={"version_number", "kind"},
            ctx=dep_ctx,
        )
        dependency_package_name = _expect_str(dep_tbl, "package_name", ctx=dep_ctx)
        dependency_version_number = _expect_opt_int(dep_tbl, "version_number", ctx=dep_ctx)
        dependency_kind_token = (
            _expect_opt_str(dep_tbl, "kind", ctx=dep_ctx)
            or AwareInterfaceDependencyKind.package.value
        )
        try:
            dependency_kind = AwareInterfaceDependencyKind(dependency_kind_token)
        except ValueError as exc:
            raise AwareInterfaceTomlError(
                f"{dep_ctx}.kind must be one of {[item.value for item in AwareInterfaceDependencyKind]}; "
                + f"got {dependency_kind_token!r}"
            ) from exc
        dependencies.append(
            AwareInterfaceTomlDependencySpec(
                package_name=dependency_package_name,
                version_number=dependency_version_number,
                kind=dependency_kind,
            )
        )

    return AwareInterfaceTomlSpec(
        aware_interface=spec_version,
        interface=AwareInterfaceTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareInterfaceTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=True if force_fresh_scan is None else force_fresh_scan,
            config_bundle_path=config_bundle_path,
            compilation_mode=compilation_mode,
        ),
        dart=dart_spec,
        dependencies=dependencies,
    )


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareInterfaceTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _expect_keys(table: dict[str, object], *, required: set[str], optional: set[str], ctx: str) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareInterfaceTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareInterfaceTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareInterfaceTomlError(f"Expected {ctx}.{key} to be a table; got {type(val)}")
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareInterfaceTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareInterfaceTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareInterfaceTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareInterfaceTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareInterfaceTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(root: dict[str, object], key: str, *, ctx: str) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareInterfaceTomlError(f"Expected {ctx}.{key} to be a list of strings")
    out: list[str] = []
    for index, item in enumerate(val):
        if not isinstance(item, str) or not item.strip():
            raise AwareInterfaceTomlError(f"Expected {ctx}.{key}[{index}] to be a non-empty string")
        out.append(item)
    return out


def _expect_list_of_tables(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareInterfaceTomlError(f"Expected {ctx} to be a list of tables")
    out: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise AwareInterfaceTomlError(f"Expected {ctx}[{index}] to be a table/object")
        payload = cast(dict[object, object], item)
        out.append({str(k): v for k, v in payload.items()})
    return out


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareInterfaceTomlError(
            f"{ctx} must not contain '.' (single-segment namespace); got {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise AwareInterfaceTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareInterfaceTomlError(
            f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}"
        )


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareInterfaceTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_dart_package_name(value: str, *, ctx: str) -> None:
    _validate_package_name(value, ctx=ctx)
    if not value.replace("_", "").isalnum():
        raise AwareInterfaceTomlError(
            f"{ctx} must contain only lowercase letters, digits, or underscores; got {value!r}"
        )
    if value.lower() != value:
        raise AwareInterfaceTomlError(f"{ctx} must be lowercase; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareInterfaceTomlError(f"{ctx} must be repo-relative (not absolute): {value!r}")
    if ".." in p.parts:
        raise AwareInterfaceTomlError(f"{ctx} must not contain '..': {value!r}")


__all__ = [
    "AwareInterfaceTomlError",
    "load_aware_interface_toml_spec",
    "load_aware_interface_toml_spec_from_text",
]
