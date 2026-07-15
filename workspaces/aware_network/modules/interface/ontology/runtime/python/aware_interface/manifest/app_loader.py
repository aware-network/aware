from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_interface.manifest.app_spec import (
    AwareAppTomlBuildSpec,
    AwareAppTomlControlSpec,
    AwareAppTomlDependencySpec,
    AwareAppTomlDartSpec,
    AwareAppTomlFactorySpec,
    AwareAppTomlInterfaceSpec,
    AwareAppTomlLaunchSpec,
    AwareAppTomlPackageSpec,
    AwareAppTomlPlatformSpec,
    AwareAppTomlSpec,
)


class AwareAppTomlError(ValueError):
    """Raised when `aware.app.toml` fails strict validation."""


def load_aware_app_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareAppTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.app.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareAppTomlError(f"Failed to parse TOML at {path_label}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_app_toml_raw(raw, path_label=path_label)


def load_aware_app_toml_spec(*, toml_path: str | Path) -> AwareAppTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareAppTomlError(f"aware.app.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareAppTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_app_toml_raw(raw, path_label=str(p))


def _parse_aware_app_toml_raw(
    raw: dict[str, object],
    *,
    path_label: str,
) -> AwareAppTomlSpec:
    _expect_keys(
        raw,
        required={"aware_app", "app", "dart", "factory", "platforms"},
        optional={"build", "control", "dependencies", "launch", "interfaces"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_app", ctx="root")
    if spec_version != 1:
        raise AwareAppTomlError(f"Unsupported aware.app.toml version {spec_version}; expected 1")

    app = _parse_app_section(_expect_table(raw, "app", ctx="root"))
    dart = _parse_dart_section(_expect_table(raw, "dart", ctx="root"))
    factory = _parse_factory_section(_expect_table(raw, "factory", ctx="root"))
    build = _parse_build_section(_expect_table(raw, "build", ctx="root")) if "build" in raw else AwareAppTomlBuildSpec()
    dependencies = _parse_dependencies(raw.get("dependencies", []))
    control = (
        _parse_control_section(_expect_table(raw, "control", ctx="root"))
        if "control" in raw
        else AwareAppTomlControlSpec()
    )
    launch = (
        _parse_launch_section(_expect_table(raw, "launch", ctx="root")) if "launch" in raw else AwareAppTomlLaunchSpec()
    )
    platforms = _parse_platforms(raw.get("platforms"), path_label=path_label)
    interfaces = _parse_interfaces(raw.get("interfaces", []))
    return AwareAppTomlSpec(
        aware_app=spec_version,
        app=app,
        dart=dart,
        factory=factory,
        build=build,
        dependencies=dependencies,
        control=control,
        launch=launch,
        platforms=platforms,
        interfaces=interfaces,
    )


def _parse_app_section(section: dict[str, object]) -> AwareAppTomlPackageSpec:
    _expect_keys(
        section,
        required={"package_name", "app_name", "fqn_prefix"},
        optional={"kind", "version_number", "title", "description"},
        ctx="[app]",
    )
    package_name = _expect_str(section, "package_name", ctx="[app]")
    app_name = _expect_str(section, "app_name", ctx="[app]")
    fqn_prefix = _expect_str(section, "fqn_prefix", ctx="[app]")
    kind = _expect_opt_str(section, "kind", ctx="[app]") or "app"
    version_number = _expect_opt_int(section, "version_number", ctx="[app]") or 1
    title = _expect_opt_str(section, "title", ctx="[app]")
    description = _expect_opt_str(section, "description", ctx="[app]")

    _validate_package_name(package_name, ctx="[app].package_name")
    _validate_package_name(app_name, ctx="[app].app_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[app].fqn_prefix")
    if kind != "app":
        raise AwareAppTomlError(f"[app].kind must be 'app'; got {kind!r}")

    return AwareAppTomlPackageSpec(
        package_name=package_name,
        app_name=app_name,
        fqn_prefix=fqn_prefix,
        kind=kind,
        version_number=version_number,
        title=title,
        description=description,
    )


def _parse_dart_section(section: dict[str, object]) -> AwareAppTomlDartSpec:
    _expect_keys(
        section,
        required={"package_path", "package_name"},
        optional={"entrypoint"},
        ctx="[dart]",
    )
    package_path = _expect_str(section, "package_path", ctx="[dart]")
    package_name = _expect_str(section, "package_name", ctx="[dart]")
    entrypoint = _expect_opt_str(section, "entrypoint", ctx="[dart]") or "lib/main.dart"

    _validate_rel_path(package_path, ctx="[dart].package_path")
    _validate_dart_package_name(package_name, ctx="[dart].package_name")
    _validate_rel_path(entrypoint, ctx="[dart].entrypoint")

    return AwareAppTomlDartSpec(
        package_path=package_path,
        package_name=package_name,
        entrypoint=entrypoint,
    )


def _parse_factory_section(section: dict[str, object]) -> AwareAppTomlFactorySpec:
    _expect_keys(
        section,
        required={"package_name"},
        optional={"package_path"},
        ctx="[factory]",
    )
    package_path = _expect_opt_str(section, "package_path", ctx="[factory]")
    package_name = _expect_str(section, "package_name", ctx="[factory]")

    if package_path is not None:
        _validate_rel_path(package_path, ctx="[factory].package_path")
    _validate_dart_package_name(package_name, ctx="[factory].package_name")

    return AwareAppTomlFactorySpec(
        package_path=package_path,
        package_name=package_name,
    )


def _parse_build_section(section: dict[str, object]) -> AwareAppTomlBuildSpec:
    _expect_keys(
        section,
        required=set(),
        optional={"sources_dir", "include_paths", "exclude_paths"},
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(section, "sources_dir", ctx="[build]") or "."
    include_paths = _expect_opt_str_list(section, "include_paths", ctx="[build]") or ["*.aware"]
    exclude_paths = _expect_opt_str_list(section, "exclude_paths", ctx="[build]")
    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for index, item in enumerate(include_paths):
        _validate_rel_path(item, ctx=f"[build].include_paths[{index}]")
    for index, item in enumerate(exclude_paths):
        _validate_rel_path(item, ctx=f"[build].exclude_paths[{index}]")
    return AwareAppTomlBuildSpec(
        sources_dir=sources_dir,
        include_paths=tuple(include_paths),
        exclude_paths=tuple(exclude_paths),
    )


def _parse_dependencies(value: object) -> list[AwareAppTomlDependencySpec]:
    dependencies_raw = _expect_list_of_tables(value, ctx="[[dependencies]]")
    dependencies: list[AwareAppTomlDependencySpec] = []
    seen: set[tuple[str, str, str]] = set()
    for index, dependency_tbl in enumerate(dependencies_raw):
        ctx = f"[[dependencies]][{index}]"
        _expect_keys(
            dependency_tbl,
            required={"package_name", "kind", "role"},
            optional=set(),
            ctx=ctx,
        )
        package_name = _expect_str(dependency_tbl, "package_name", ctx=ctx)
        kind = _expect_str(dependency_tbl, "kind", ctx=ctx)
        role = _expect_str(dependency_tbl, "role", ctx=ctx)
        _validate_package_name(package_name, ctx=f"{ctx}.package_name")
        _validate_token(kind, ctx=f"{ctx}.kind")
        _validate_token(role, ctx=f"{ctx}.role")
        key = (package_name, kind, role)
        if key in seen:
            raise AwareAppTomlError(
                "Duplicate dependency " f"package_name={package_name!r} kind={kind!r} role={role!r}"
            )
        seen.add(key)
        dependencies.append(
            AwareAppTomlDependencySpec(
                package_name=package_name,
                kind=kind,
                role=role,
            )
        )
    return dependencies


def _parse_control_section(section: dict[str, object]) -> AwareAppTomlControlSpec:
    _expect_keys(
        section,
        required=set(),
        optional={
            "requires_actor",
            "default_screen",
            "admitted_screen",
        },
        ctx="[control]",
    )
    requires_actor = _expect_opt_bool(section, "requires_actor", ctx="[control]")
    default_screen = _expect_opt_str(section, "default_screen", ctx="[control]") or "control"
    admitted_screen = _expect_opt_str(section, "admitted_screen", ctx="[control]")
    _validate_token(default_screen, ctx="[control].default_screen")
    if admitted_screen is not None:
        _validate_token(admitted_screen, ctx="[control].admitted_screen")
    return AwareAppTomlControlSpec(
        requires_actor=True if requires_actor is None else requires_actor,
        default_screen=default_screen,
        admitted_screen=admitted_screen,
    )


def _parse_launch_section(section: dict[str, object]) -> AwareAppTomlLaunchSpec:
    _expect_keys(
        section,
        required=set(),
        optional={"seed_color_value", "generated_manifest_path"},
        ctx="[launch]",
    )
    seed_color_value = _expect_opt_int(section, "seed_color_value", ctx="[launch]")
    generated_manifest_path = (
        _expect_opt_str(section, "generated_manifest_path", ctx="[launch]") or "lib/aware_app_launch_manifest.g.dart"
    )
    _validate_rel_path(generated_manifest_path, ctx="[launch].generated_manifest_path")
    return AwareAppTomlLaunchSpec(
        seed_color_value=0xFF2563EB if seed_color_value is None else seed_color_value,
        generated_manifest_path=generated_manifest_path,
    )


def _parse_platforms(
    value: object,
    *,
    path_label: str,
) -> list[AwareAppTomlPlatformSpec]:
    platforms_raw = _expect_list_of_tables(value, ctx="[[platforms]]")
    if not platforms_raw:
        raise AwareAppTomlError(f"{path_label} must declare at least one [[platforms]]")
    platforms: list[AwareAppTomlPlatformSpec] = []
    seen_targets: set[str] = set()
    for index, platform_tbl in enumerate(platforms_raw):
        ctx = f"[[platforms]][{index}]"
        _expect_keys(
            platform_tbl,
            required={"target", "runner_path"},
            optional={"materializer", "binary_name", "application_id", "enabled"},
            ctx=ctx,
        )
        target = _expect_str(platform_tbl, "target", ctx=ctx)
        runner_path = _expect_str(platform_tbl, "runner_path", ctx=ctx)
        materializer = _expect_opt_str(platform_tbl, "materializer", ctx=ctx) or "flutter_create"
        binary_name = _expect_opt_str(platform_tbl, "binary_name", ctx=ctx)
        application_id = _expect_opt_str(platform_tbl, "application_id", ctx=ctx)
        enabled = _expect_opt_bool(platform_tbl, "enabled", ctx=ctx)
        _validate_token(target, ctx=f"{ctx}.target")
        _validate_rel_path(runner_path, ctx=f"{ctx}.runner_path")
        _validate_token(materializer, ctx=f"{ctx}.materializer")
        if binary_name is not None:
            _validate_token(binary_name, ctx=f"{ctx}.binary_name")
        if application_id is not None:
            _validate_application_id(application_id, ctx=f"{ctx}.application_id")
        if target in seen_targets:
            raise AwareAppTomlError(f"Duplicate platform target {target!r}")
        seen_targets.add(target)
        platforms.append(
            AwareAppTomlPlatformSpec(
                target=target,
                runner_path=runner_path,
                materializer=materializer,
                binary_name=binary_name,
                application_id=application_id,
                enabled=True if enabled is None else enabled,
            )
        )
    return platforms


def _parse_interfaces(value: object) -> list[AwareAppTomlInterfaceSpec]:
    interfaces_raw = _expect_list_of_tables(value, ctx="[[interfaces]]")
    interfaces: list[AwareAppTomlInterfaceSpec] = []
    seen_package_names: set[str] = set()
    for index, interface_tbl in enumerate(interfaces_raw):
        ctx = f"[[interfaces]][{index}]"
        _expect_keys(
            interface_tbl,
            required={"package_name", "role"},
            optional={
                "runtime_import",
                "runtime_import_alias",
                "runtime_factory",
            },
            ctx=ctx,
        )
        package_name = _expect_str(interface_tbl, "package_name", ctx=ctx)
        role = _expect_str(interface_tbl, "role", ctx=ctx)
        runtime_import = _expect_opt_str(interface_tbl, "runtime_import", ctx=ctx)
        runtime_import_alias = _expect_opt_str(interface_tbl, "runtime_import_alias", ctx=ctx)
        runtime_factory = _expect_opt_str(interface_tbl, "runtime_factory", ctx=ctx) or "buildInterfacePackageRuntime"
        _validate_package_name(package_name, ctx=f"{ctx}.package_name")
        _validate_token(role, ctx=f"{ctx}.role")
        if runtime_import is not None and not runtime_import.strip():
            raise AwareAppTomlError(f"Expected {ctx}.runtime_import to be a non-empty string")
        if runtime_import_alias is not None:
            _validate_dart_package_name(runtime_import_alias, ctx=f"{ctx}.runtime_import_alias")
        _validate_dart_identifier(runtime_factory, ctx=f"{ctx}.runtime_factory")
        if package_name in seen_package_names:
            raise AwareAppTomlError(f"Duplicate interface package {package_name!r}")
        seen_package_names.add(package_name)
        interfaces.append(
            AwareAppTomlInterfaceSpec(
                package_name=package_name,
                role=role,
                runtime_import=runtime_import,
                runtime_import_alias=runtime_import_alias,
                runtime_factory=runtime_factory,
            )
        )
    return interfaces


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareAppTomlError(f"Expected {ctx} to be a table/object")
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
        raise AwareAppTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareAppTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareAppTomlError(f"Expected {ctx}.{key} to be a table; got {type(val)}")
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareAppTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareAppTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_opt_str_list(root: dict[str, object], key: str, *, ctx: str) -> list[str]:
    val = root.get(key, None)
    if val is None:
        return []
    if not isinstance(val, list):
        raise AwareAppTomlError(f"Expected {ctx}.{key} to be a list of strings or null")
    out: list[str] = []
    for index, item in enumerate(val):
        if not isinstance(item, str) or not item.strip():
            raise AwareAppTomlError(f"Expected {ctx}.{key}[{index}] to be a non-empty string")
        out.append(item)
    return out


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareAppTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareAppTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareAppTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_list_of_tables(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareAppTomlError(f"Expected {ctx} to be a list of tables")
    out: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise AwareAppTomlError(f"Expected {ctx}[{index}] to be a table/object")
        payload = cast(dict[object, object], item)
        out.append({str(k): v for k, v in payload.items()})
    return out


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareAppTomlError(f"{ctx} must not contain '.' (single-segment namespace); got {value!r}")
    if any(ch.isspace() for ch in value):
        raise AwareAppTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareAppTomlError(f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}")


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareAppTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_dart_package_name(value: str, *, ctx: str) -> None:
    _validate_package_name(value, ctx=ctx)
    if not value.replace("_", "").isalnum():
        raise AwareAppTomlError(f"{ctx} must contain only lowercase letters, digits, or underscores; got {value!r}")
    if value.lower() != value:
        raise AwareAppTomlError(f"{ctx} must be lowercase; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareAppTomlError(f"{ctx} must be repo-relative (not absolute): {value!r}")
    if ".." in p.parts:
        raise AwareAppTomlError(f"{ctx} must not contain '..': {value!r}")


def _validate_token(value: str, *, ctx: str) -> None:
    if value.strip() != value or any(ch.isspace() for ch in value):
        raise AwareAppTomlError(f"{ctx} must be a non-empty token without whitespace")
    if value.lower() != value:
        raise AwareAppTomlError(f"{ctx} must be lowercase; got {value!r}")


def _validate_application_id(value: str, *, ctx: str) -> None:
    if value.strip() != value or any(ch.isspace() for ch in value):
        raise AwareAppTomlError(f"{ctx} must be a non-empty reverse-DNS token without whitespace")
    parts = value.split(".")
    if len(parts) < 2:
        raise AwareAppTomlError(f"{ctx} must contain at least two dot-separated segments; got {value!r}")
    for part in parts:
        if not part:
            raise AwareAppTomlError(f"{ctx} must not contain empty segments; got {value!r}")
        first = part[0]
        if not (first.isalpha() or first == "_"):
            raise AwareAppTomlError(f"{ctx} segments must start with a letter or '_'; got {value!r}")
        for ch in part[1:]:
            if not (ch.isalnum() or ch == "_"):
                raise AwareAppTomlError(f"{ctx} segments must contain letters, digits, or '_'; got {value!r}")


def _validate_dart_identifier(value: str, *, ctx: str) -> None:
    if not value or value.strip() != value:
        raise AwareAppTomlError(f"{ctx} must be a non-empty Dart identifier")
    parts = value.split(".")
    for part in parts:
        if not part:
            raise AwareAppTomlError(f"{ctx} must be a Dart identifier path; got {value!r}")
        first = part[0]
        if not (first == "_" or first.isalpha()):
            raise AwareAppTomlError(f"{ctx} segment must start with a letter or '_'; got {value!r}")
        for ch in part[1:]:
            if not (ch == "_" or ch.isalnum()):
                raise AwareAppTomlError(f"{ctx} segment must contain only letters, digits, or '_'; got {value!r}")


__all__ = [
    "AwareAppTomlError",
    "load_aware_app_toml_spec",
    "load_aware_app_toml_spec_from_text",
]
