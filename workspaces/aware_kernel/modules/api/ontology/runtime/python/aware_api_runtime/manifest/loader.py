from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_api_runtime.manifest.spec import (
    AwareApiCompilationMode,
    AwareApiSemanticPackageExportKind,
    AwareApiTomlBuildSpec,
    AwareApiTomlDartProductTargetSpec,
    AwareApiTomlDartTargetSpec,
    AwareApiTomlDependencySpec,
    AwareApiTomlPackageSpec,
    AwareApiTomlPythonProductTargetSpec,
    AwareApiTomlPythonTargetSpec,
    AwareApiTomlSemanticPackageExportSpec,
    AwareApiTomlSpec,
    AwareApiTomlTargetsSpec,
)


class AwareApiTomlError(ValueError):
    """Raised when `aware.api.toml` fails strict validation."""


def load_aware_api_toml_spec_from_text(*, toml_text: str, toml_path: str | Path | None = None) -> AwareApiTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.api.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareApiTomlError(f"Failed to parse TOML at {path_label}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_api_toml_raw(raw, path_label=path_label)


def load_aware_api_toml_spec(*, toml_path: str | Path) -> AwareApiTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareApiTomlError(f"aware.api.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareApiTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_api_toml_raw(raw, path_label=str(p))


def _parse_aware_api_toml_raw(raw: dict[str, object], *, path_label: str) -> AwareApiTomlSpec:
    _expect_keys(
        raw,
        required={"aware_api", "api", "build"},
        optional={"dependencies", "targets", "semantic_package_exports"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_api", ctx="root")
    if spec_version != 1:
        raise AwareApiTomlError(f"Unsupported aware.api.toml version {spec_version}; expected 1")

    api_tbl = _expect_table(raw, "api", ctx="root")
    _expect_keys(
        api_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[api]",
    )
    package_name = _expect_str(api_tbl, "package_name", ctx="[api]")
    fqn_prefix = _expect_str(api_tbl, "fqn_prefix", ctx="[api]")
    version_number = _expect_opt_int(api_tbl, "version_number", ctx="[api]") or 1
    title = _expect_opt_str(api_tbl, "title", ctx="[api]")
    description = _expect_opt_str(api_tbl, "description", ctx="[api]")

    _validate_package_name(package_name, ctx="[api].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[api].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={"sources_dir", "include_paths", "exclude_paths", "force_fresh_scan", "compilation_mode"},
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "apis"
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or ["**/*.aware"]
    exclude_paths = _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    force_fresh_scan = _expect_opt_bool(build_tbl, "force_fresh_scan", ctx="[build]") or True
    compilation_mode = _expect_opt_compilation_mode(build_tbl, "compilation_mode", ctx="[build]")
    if compilation_mode is None:
        compilation_mode = AwareApiCompilationMode.raw_xor

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for i, path in enumerate(include_paths):
        _validate_rel_path(path, ctx=f"[build].include_paths[{i}]")
    for i, path in enumerate(exclude_paths):
        _validate_rel_path(path, ctx=f"[build].exclude_paths[{i}]")

    deps_tbl = _as_table_list(raw.get("dependencies", []), ctx="[[dependencies]]")
    dependencies: list[AwareApiTomlDependencySpec] = []
    seen_deps: set[str] = set()
    for i, dep_tbl in enumerate(deps_tbl):
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={"version_number"},
            ctx=f"[[dependencies]] (index={i})",
        )
        dep_package_name = _expect_str(dep_tbl, "package_name", ctx=f"dependencies[{i}]")
        dep_version_number = _expect_opt_int(dep_tbl, "version_number", ctx=f"dependencies[{i}]")

        _validate_package_name(dep_package_name, ctx=f"dependencies[{i}].package_name")
        if dep_package_name in seen_deps:
            raise AwareApiTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at dependencies[{i}] in {path_label}"
            )
        seen_deps.add(dep_package_name)
        dependencies.append(
            AwareApiTomlDependencySpec(
                package_name=dep_package_name,
                version_number=dep_version_number,
            )
        )

    targets = _parse_targets(raw=raw, path_label=path_label)
    semantic_package_exports = _parse_semantic_package_exports(
        raw=raw,
        path_label=path_label,
    )

    return AwareApiTomlSpec(
        aware_api=spec_version,
        api=AwareApiTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareApiTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
            compilation_mode=compilation_mode,
        ),
        dependencies=dependencies,
        targets=targets,
        semantic_package_exports=semantic_package_exports,
    )


def _parse_semantic_package_exports(
    *,
    raw: dict[str, object],
    path_label: str,
) -> list[AwareApiTomlSemanticPackageExportSpec]:
    export_tables = _as_table_list(
        raw.get("semantic_package_exports", []),
        ctx="[[semantic_package_exports]]",
    )
    exports: list[AwareApiTomlSemanticPackageExportSpec] = []
    seen_packages: set[str] = set()
    seen_manifest_paths: set[str] = set()
    for i, export_tbl in enumerate(export_tables):
        ctx = f"[[semantic_package_exports]] (index={i})"
        _expect_keys(
            export_tbl,
            required={"kind", "package_name", "manifest_path"},
            optional={
                "code_package_surface",
                "workspace_materialization_primary",
                "workspace_materialization_order",
                "workspace_materialization_branch",
                "workspace_materialization_commit",
                "workspace_manifest_kind",
                "code_package_manifest_kind",
                "semantic_provider_key",
                "semantic_package_family",
                "semantic_package_kind",
                "semantic_package_name",
                "semantic_projection_name",
                "semantic_root_kind",
                "semantic_contract_role",
                "semantic_contract_name",
                "semantic_contract_provider_key",
                "semantic_contract_module",
            },
            ctx=ctx,
        )
        export_kind = _expect_semantic_package_export_kind(
            export_tbl,
            "kind",
            ctx=ctx,
        )
        package_name = _expect_str(export_tbl, "package_name", ctx=ctx)
        manifest_path = _expect_str(export_tbl, "manifest_path", ctx=ctx)
        _validate_package_name(package_name, ctx=f"{ctx}.package_name")
        _validate_rel_path(manifest_path, ctx=f"{ctx}.manifest_path")
        if package_name in seen_packages:
            raise AwareApiTomlError(
                f"Duplicate semantic package export package_name={package_name!r} "
                f"at {ctx} in {path_label}"
            )
        if manifest_path in seen_manifest_paths:
            raise AwareApiTomlError(
                f"Duplicate semantic package export manifest_path={manifest_path!r} "
                f"at {ctx} in {path_label}"
            )
        seen_packages.add(package_name)
        seen_manifest_paths.add(manifest_path)
        exports.append(
            _semantic_package_export_with_defaults(
                export_tbl=export_tbl,
                export_kind=export_kind,
                package_name=package_name,
                manifest_path=manifest_path,
                ctx=ctx,
            )
        )
    return exports


def _semantic_package_export_with_defaults(
    *,
    export_tbl: dict[str, object],
    export_kind: AwareApiSemanticPackageExportKind,
    package_name: str,
    manifest_path: str,
    ctx: str,
) -> AwareApiTomlSemanticPackageExportSpec:
    if export_kind is AwareApiSemanticPackageExportKind.api_dto:
        defaults = {
            "workspace_materialization_primary": True,
            "workspace_materialization_order": 90,
            "workspace_materialization_branch": "semantic",
            "workspace_materialization_commit": False,
            "code_package_surface": "api",
            "workspace_manifest_kind": "api_dto",
            "code_package_manifest_kind": "aware_toml",
            "semantic_provider_key": "aware_api",
            "semantic_package_family": "api",
            "semantic_package_kind": "api_dto_package",
            "semantic_package_name": package_name,
            "semantic_projection_name": "ApiPackage",
            "semantic_root_kind": "api_dto",
            "semantic_contract_role": "aware_api.provider",
            "semantic_contract_name": "aware.semantic_provider",
            "semantic_contract_provider_key": "aware_api",
            "semantic_contract_module": "aware_api_runtime.semantic_contract",
        }
    else:
        raise AwareApiTomlError(f"Unsupported semantic package export kind: {export_kind.value!r}")

    default_primary = cast(bool, defaults["workspace_materialization_primary"])
    default_order = cast(int, defaults["workspace_materialization_order"])
    default_branch = cast(str, defaults["workspace_materialization_branch"])
    default_commit = cast(bool, defaults["workspace_materialization_commit"])
    default_surface = cast(str, defaults["code_package_surface"])
    default_workspace_kind = cast(str, defaults["workspace_manifest_kind"])
    default_code_kind = cast(str, defaults["code_package_manifest_kind"])
    default_provider_key = cast(str, defaults["semantic_provider_key"])
    default_family = cast(str, defaults["semantic_package_family"])
    default_package_kind = cast(str, defaults["semantic_package_kind"])
    default_package_name = cast(str | None, defaults["semantic_package_name"])
    default_projection = cast(str, defaults["semantic_projection_name"])
    default_root_kind = cast(str, defaults["semantic_root_kind"])
    default_contract_role = cast(str, defaults["semantic_contract_role"])
    default_contract_name = cast(str, defaults["semantic_contract_name"])
    default_contract_provider = cast(str, defaults["semantic_contract_provider_key"])
    default_contract_module = cast(str, defaults["semantic_contract_module"])
    primary_override = (
        _expect_opt_bool(export_tbl, "workspace_materialization_primary", ctx=ctx)
        if "workspace_materialization_primary" in export_tbl
        else None
    )
    order_override = (
        _expect_opt_int(export_tbl, "workspace_materialization_order", ctx=ctx)
        if "workspace_materialization_order" in export_tbl
        else None
    )
    commit_override = (
        _expect_opt_bool(export_tbl, "workspace_materialization_commit", ctx=ctx)
        if "workspace_materialization_commit" in export_tbl
        else None
    )

    return AwareApiTomlSemanticPackageExportSpec(
        kind=export_kind,
        package_name=package_name,
        manifest_path=manifest_path,
        code_package_surface=_expect_export_str_with_default(
            export_tbl,
            "code_package_surface",
            default=default_surface,
            ctx=ctx,
        ),
        workspace_materialization_primary=(
            default_primary if primary_override is None else primary_override
        ),
        workspace_materialization_order=(
            default_order if order_override is None else order_override
        ),
        workspace_materialization_branch=_expect_export_str_with_default(
            export_tbl,
            "workspace_materialization_branch",
            default=default_branch,
            ctx=ctx,
        ),
        workspace_materialization_commit=(
            default_commit if commit_override is None else commit_override
        ),
        workspace_manifest_kind=_expect_export_str_with_default(
            export_tbl,
            "workspace_manifest_kind",
            default=default_workspace_kind,
            ctx=ctx,
        ),
        code_package_manifest_kind=_expect_export_str_with_default(
            export_tbl,
            "code_package_manifest_kind",
            default=default_code_kind,
            ctx=ctx,
        ),
        semantic_provider_key=_expect_export_str_with_default(
            export_tbl,
            "semantic_provider_key",
            default=default_provider_key,
            ctx=ctx,
        ),
        semantic_package_family=_expect_export_str_with_default(
            export_tbl,
            "semantic_package_family",
            default=default_family,
            ctx=ctx,
        ),
        semantic_package_kind=_expect_export_str_with_default(
            export_tbl,
            "semantic_package_kind",
            default=default_package_kind,
            ctx=ctx,
        ),
        semantic_package_name=_expect_opt_str(export_tbl, "semantic_package_name", ctx=ctx)
        or default_package_name,
        semantic_projection_name=_expect_export_str_with_default(
            export_tbl,
            "semantic_projection_name",
            default=default_projection,
            ctx=ctx,
        ),
        semantic_root_kind=_expect_export_str_with_default(
            export_tbl,
            "semantic_root_kind",
            default=default_root_kind,
            ctx=ctx,
        ),
        semantic_contract_role=_expect_export_str_with_default(
            export_tbl,
            "semantic_contract_role",
            default=default_contract_role,
            ctx=ctx,
        ),
        semantic_contract_name=_expect_export_str_with_default(
            export_tbl,
            "semantic_contract_name",
            default=default_contract_name,
            ctx=ctx,
        ),
        semantic_contract_provider_key=_expect_export_str_with_default(
            export_tbl,
            "semantic_contract_provider_key",
            default=default_contract_provider,
            ctx=ctx,
        ),
        semantic_contract_module=_expect_export_str_with_default(
            export_tbl,
            "semantic_contract_module",
            default=default_contract_module,
            ctx=ctx,
        ),
    )


def _parse_targets(*, raw: dict[str, object], path_label: str) -> AwareApiTomlTargetsSpec:
    targets_raw = raw.get("targets")
    if targets_raw is None:
        return AwareApiTomlTargetsSpec()
    targets_tbl = _as_table(targets_raw, ctx=f"[targets] at {path_label}")
    _expect_keys(
        targets_tbl,
        required=set(),
        optional={"python", "dart"},
        ctx="[targets]",
    )
    python_raw = targets_tbl.get("python")
    python: AwareApiTomlPythonTargetSpec | None = None
    if python_raw is not None:
        python_tbl = _as_table(python_raw, ctx=f"[targets.python] at {path_label}")
        _expect_keys(
            python_tbl,
            required=set(),
            optional={"root_dir", "public_package", "service_protocol"},
            ctx="[targets.python]",
        )
        root_dir = _expect_opt_str(python_tbl, "root_dir", ctx="[targets.python]")
        if root_dir is not None:
            _validate_rel_path(root_dir, ctx="[targets.python].root_dir")
        public_package = _parse_python_product_target(
            python_tbl=python_tbl,
            key="public_package",
            ctx="[targets.python.public_package]",
        )
        service_protocol = _parse_python_product_target(
            python_tbl=python_tbl,
            key="service_protocol",
            ctx="[targets.python.service_protocol]",
        )
        python = AwareApiTomlPythonTargetSpec(
            root_dir=root_dir,
            public_package=public_package,
            service_protocol=service_protocol,
        )

    dart_raw = targets_tbl.get("dart")
    dart: AwareApiTomlDartTargetSpec | None = None
    if dart_raw is not None:
        dart_tbl = _as_table(dart_raw, ctx=f"[targets.dart] at {path_label}")
        _expect_keys(
            dart_tbl,
            required=set(),
            optional={"root_dir", "public_package"},
            ctx="[targets.dart]",
        )
        root_dir = _expect_opt_str(dart_tbl, "root_dir", ctx="[targets.dart]")
        if root_dir is not None:
            _validate_rel_path(root_dir, ctx="[targets.dart].root_dir")
        public_package = _parse_dart_product_target(
            dart_tbl=dart_tbl,
            key="public_package",
            ctx="[targets.dart.public_package]",
        )
        dart = AwareApiTomlDartTargetSpec(
            root_dir=root_dir,
            public_package=public_package,
        )

    return AwareApiTomlTargetsSpec(
        python=python,
        dart=dart,
    )


def _parse_python_product_target(
    *,
    python_tbl: dict[str, object],
    key: str,
    ctx: str,
) -> AwareApiTomlPythonProductTargetSpec:
    raw = python_tbl.get(key)
    if raw is None:
        return AwareApiTomlPythonProductTargetSpec()
    target_tbl = _as_table(raw, ctx=ctx)
    _expect_keys(
        target_tbl,
        required=set(),
        optional={"package_dir", "root_dir"},
        ctx=ctx,
    )
    package_dir = _expect_opt_str(target_tbl, "package_dir", ctx=ctx)
    if package_dir is not None:
        _validate_rel_path(package_dir, ctx=f"{ctx}.package_dir")
    root_dir = _expect_opt_str(target_tbl, "root_dir", ctx=ctx)
    if root_dir is not None:
        _validate_rel_path(root_dir, ctx=f"{ctx}.root_dir")
    return AwareApiTomlPythonProductTargetSpec(package_dir=package_dir, root_dir=root_dir)


def _parse_dart_product_target(
    *,
    dart_tbl: dict[str, object],
    key: str,
    ctx: str,
) -> AwareApiTomlDartProductTargetSpec:
    raw = dart_tbl.get(key)
    if raw is None:
        return AwareApiTomlDartProductTargetSpec()
    target_tbl = _as_table(raw, ctx=ctx)
    _expect_keys(
        target_tbl,
        required=set(),
        optional={"package_dir", "root_dir"},
        ctx=ctx,
    )
    package_dir = _expect_opt_str(target_tbl, "package_dir", ctx=ctx)
    if package_dir is not None:
        _validate_rel_path(package_dir, ctx=f"{ctx}.package_dir")
    root_dir = _expect_opt_str(target_tbl, "root_dir", ctx=ctx)
    if root_dir is not None:
        _validate_rel_path(root_dir, ctx=f"{ctx}.root_dir")
    return AwareApiTomlDartProductTargetSpec(package_dir=package_dir, root_dir=root_dir)


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareApiTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareApiTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    items = cast(list[object], value)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AwareApiTomlError(f"Expected {ctx}[{i}] to be a table/object")
        payload = cast(dict[object, object], item)
        tables.append({str(k): v for k, v in payload.items()})
    return tables


def _expect_keys(table: dict[str, object], *, required: set[str], optional: set[str], ctx: str) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareApiTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareApiTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be a table; got {type(val)}")
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(root: dict[str, object], key: str, *, ctx: str) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareApiTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _expect_opt_compilation_mode(root: dict[str, object], key: str, *, ctx: str) -> AwareApiCompilationMode | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareApiCompilationMode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in AwareApiCompilationMode)
        raise AwareApiTomlError(f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}") from exc


def _expect_semantic_package_export_kind(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareApiSemanticPackageExportKind:
    value = _expect_str(root, key, ctx=ctx)
    try:
        return AwareApiSemanticPackageExportKind(value)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in AwareApiSemanticPackageExportKind)
        raise AwareApiTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_export_str_with_default(
    root: dict[str, object],
    key: str,
    *,
    default: object,
    ctx: str,
) -> str:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is not None:
        return value
    if isinstance(default, str) and default:
        return default
    raise AwareApiTomlError(f"Missing default for {ctx}.{key}")


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareApiTomlError(f"{ctx} must not contain '.' (single-segment namespace); got {value!r}")
    if any(ch.isspace() for ch in value):
        raise AwareApiTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareApiTomlError(f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}")


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareApiTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareApiTomlError(f"{ctx} must be repo-relative (not absolute): {value!r}")
    if ".." in p.parts:
        raise AwareApiTomlError(f"{ctx} must not contain '..': {value!r}")


__all__ = [
    "AwareApiTomlError",
    "load_aware_api_toml_spec",
    "load_aware_api_toml_spec_from_text",
]
