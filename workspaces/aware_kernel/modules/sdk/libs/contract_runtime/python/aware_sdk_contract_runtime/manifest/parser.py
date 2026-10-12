from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast
from uuid import UUID

from .model import (
    AwareSdkCompilationMode,
    AwareSdkDependencyKind,
    AwareSdkTomlBuildSpec,
    AwareSdkTomlDartProductTargetSpec,
    AwareSdkTomlDartTargetSpec,
    AwareSdkTomlDependencySpec,
    AwareSdkTomlGenerationProfileSpec,
    AwareSdkTomlObjectConfigGraphPackageSpec,
    AwareSdkTomlPackageSpec,
    AwareSdkTomlPythonProductTargetSpec,
    AwareSdkTomlPythonTargetSpec,
    AwareSdkTomlSpec,
    AwareSdkTomlTargetsSpec,
    validate_sdk_manifest_version,
)


class AwareSdkTomlError(ValueError):
    """Raised when `aware.sdk.toml` fails strict validation."""


def load_aware_sdk_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareSdkTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.sdk.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareSdkTomlError(f"Failed to parse TOML at {path_label}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_sdk_toml_raw(raw, path_label=path_label)


def parse_sdk_manifest_bytes(
    body: bytes, *, path_label: str = "<aware.sdk.toml>"
) -> AwareSdkTomlSpec:
    """Interpret exact UTF-8 manifest bytes without filesystem authority."""
    if type(body) is not bytes:
        raise TypeError("SDK manifest body must be exact bytes")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AwareSdkTomlError(f"Failed to decode UTF-8 at {path_label}") from exc
    return load_aware_sdk_toml_spec_from_text(toml_text=text, toml_path=path_label)


def _parse_aware_sdk_toml_raw(
    raw: dict[str, object], *, path_label: str
) -> AwareSdkTomlSpec:
    _expect_keys(
        raw,
        required={"aware_sdk", "sdk", "build"},
        optional={
            "dependencies",
            "object_config_graph_packages",
            "targets",
            "generation_profiles",
        },
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_sdk", ctx="root")
    if type(spec_version) is not int:
        raise AwareSdkTomlError("aware_sdk must be a positive integer")
    if spec_version != 1:
        raise AwareSdkTomlError(
            f"Unsupported aware.sdk.toml version {spec_version}; expected 1"
        )

    sdk_tbl = _expect_table(raw, "sdk", ctx="root")
    _expect_keys(
        sdk_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[sdk]",
    )
    package_name = _expect_str(sdk_tbl, "package_name", ctx="[sdk]")
    fqn_prefix = _expect_str(sdk_tbl, "fqn_prefix", ctx="[sdk]")
    version_number = _expect_opt_int(sdk_tbl, "version_number", ctx="[sdk]") or 1
    title = _expect_opt_str(sdk_tbl, "title", ctx="[sdk]")
    description = _expect_opt_str(sdk_tbl, "description", ctx="[sdk]")

    _validate_package_name(package_name, ctx="[sdk].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[sdk].fqn_prefix")

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
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "sdks"
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
        compilation_mode = AwareSdkCompilationMode.raw_xor

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for i, path in enumerate(include_paths):
        _validate_rel_path(path, ctx=f"[build].include_paths[{i}]")
    for i, path in enumerate(exclude_paths):
        _validate_rel_path(path, ctx=f"[build].exclude_paths[{i}]")

    deps_tbl = _as_table_list(raw.get("dependencies", []), ctx="[[dependencies]]")
    dependencies: list[AwareSdkTomlDependencySpec] = []
    seen_deps: set[str] = set()
    for i, dep_tbl in enumerate(deps_tbl):
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={
                "version_number",
                "kind",
                "expected_hash_sha256",
                "object_instance_graph_commit_id",
            },
            ctx=f"[[dependencies]] (index={i})",
        )
        dep_package_name = _expect_str(
            dep_tbl, "package_name", ctx=f"dependencies[{i}]"
        )
        dep_version_number = _expect_opt_int(
            dep_tbl, "version_number", ctx=f"dependencies[{i}]"
        )
        dep_kind = _expect_opt_dependency_kind(
            dep_tbl, "kind", ctx=f"dependencies[{i}]"
        )
        if dep_kind is None:
            dep_kind = AwareSdkDependencyKind.package
        dep_expected_hash = _expect_opt_str(
            dep_tbl, "expected_hash_sha256", ctx=f"dependencies[{i}]"
        )
        dep_oig_commit_id = _expect_opt_str(
            dep_tbl,
            "object_instance_graph_commit_id",
            ctx=f"dependencies[{i}]",
        )

        _validate_package_name(dep_package_name, ctx=f"dependencies[{i}].package_name")
        if dep_expected_hash is not None:
            dep_expected_hash = dep_expected_hash.strip().lower()
            _validate_sha256(
                dep_expected_hash, ctx=f"dependencies[{i}].expected_hash_sha256"
            )
        if dep_oig_commit_id is not None:
            dep_oig_commit_id = _normalize_uuid(
                dep_oig_commit_id,
                ctx=f"dependencies[{i}].object_instance_graph_commit_id",
            )
        if dep_package_name in seen_deps:
            raise AwareSdkTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at dependencies[{i}] in {path_label}"
            )
        seen_deps.add(dep_package_name)
        dependencies.append(
            AwareSdkTomlDependencySpec(
                package_name=dep_package_name,
                version_number=dep_version_number,
                kind=dep_kind,
                expected_hash_sha256=dep_expected_hash,
                object_instance_graph_commit_id=dep_oig_commit_id,
            )
        )

    ocg_pkg_tbls = _as_table_list(
        raw.get("object_config_graph_packages", []),
        ctx="[[object_config_graph_packages]]",
    )
    object_config_graph_packages: list[AwareSdkTomlObjectConfigGraphPackageSpec] = []
    seen_ocg_package_manifests: set[str] = set()
    for i, ocg_pkg_tbl in enumerate(ocg_pkg_tbls):
        ctx = f"[[object_config_graph_packages]] (index={i})"
        _expect_keys(
            ocg_pkg_tbl,
            required={"manifest"},
            optional={
                "role",
                "description",
                "expected_hash_sha256",
                "object_instance_graph_commit_id",
            },
            ctx=ctx,
        )
        manifest = _expect_str(
            ocg_pkg_tbl,
            "manifest",
            ctx=f"object_config_graph_packages[{i}]",
        )
        role = (
            _expect_opt_str(
                ocg_pkg_tbl,
                "role",
                ctx=f"object_config_graph_packages[{i}]",
            )
            or "local_state"
        )
        description = _expect_opt_str(
            ocg_pkg_tbl,
            "description",
            ctx=f"object_config_graph_packages[{i}]",
        )
        expected_hash = _expect_opt_str(
            ocg_pkg_tbl,
            "expected_hash_sha256",
            ctx=f"object_config_graph_packages[{i}]",
        )
        oig_commit_id = _expect_opt_str(
            ocg_pkg_tbl,
            "object_instance_graph_commit_id",
            ctx=f"object_config_graph_packages[{i}]",
        )
        _validate_rel_path(
            manifest,
            ctx=f"object_config_graph_packages[{i}].manifest",
        )
        if Path(manifest).name != "aware.toml":
            raise AwareSdkTomlError(
                "object_config_graph_packages entries must point at an "
                f"aware.toml manifest; got {manifest!r}"
            )
        if manifest in seen_ocg_package_manifests:
            raise AwareSdkTomlError(
                "Duplicate object_config_graph_packages manifest="
                f"{manifest!r} at index={i} in {path_label}"
            )
        seen_ocg_package_manifests.add(manifest)
        if expected_hash is not None:
            expected_hash = expected_hash.strip().lower()
            _validate_sha256(
                expected_hash,
                ctx=f"object_config_graph_packages[{i}].expected_hash_sha256",
            )
        if oig_commit_id is not None:
            oig_commit_id = _normalize_uuid(
                oig_commit_id,
                ctx=f"object_config_graph_packages[{i}].object_instance_graph_commit_id",
            )
        object_config_graph_packages.append(
            AwareSdkTomlObjectConfigGraphPackageSpec(
                manifest=manifest,
                role=role,
                description=description,
                expected_hash_sha256=expected_hash,
                object_instance_graph_commit_id=oig_commit_id,
            )
        )

    targets = _parse_targets(raw=raw, path_label=path_label)

    result = AwareSdkTomlSpec(
        aware_sdk=spec_version,
        sdk=AwareSdkTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareSdkTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
            compilation_mode=compilation_mode,
        ),
        dependencies=dependencies,
        object_config_graph_packages=object_config_graph_packages,
        targets=targets,
        generation_profiles=_parse_generation_profiles(raw),
    )
    try:
        validate_sdk_manifest_version(result)
    except ValueError as error:
        raise AwareSdkTomlError(str(error)) from error
    return result


def _parse_generation_profiles(
    raw: dict[str, object],
) -> list[AwareSdkTomlGenerationProfileSpec]:
    if "generation_profiles" not in raw:
        return []
    tables = _expect_table(raw, "generation_profiles", ctx="root")
    if not 1 <= len(tables) <= 32:
        raise AwareSdkTomlError("generation_profiles requires 1..32 tables")
    profiles: list[AwareSdkTomlGenerationProfileSpec] = []
    fields = {
        "renderer_version",
        "operations",
        "python_generated_dir",
        "dart_generated_dir",
        "materialized_dir",
    }
    for name in sorted(tables, key=lambda name: name.encode()):
        ctx = f"[generation_profiles.{name}]"
        table = _expect_table(tables, name, ctx="generation_profiles")
        _expect_keys(table, required=fields, optional=set(), ctx=ctx)
        operations = _expect_opt_str_list(table, "operations", ctx=ctx)
        if operations is None:
            raise AwareSdkTomlError("profile operations requires an exact list")
        profiles.append(
            AwareSdkTomlGenerationProfileSpec(
                name=name,
                renderer_version=_expect_str(table, "renderer_version", ctx=ctx),
                operations=operations,
                python_generated_dir=_expect_str(
                    table, "python_generated_dir", ctx=ctx
                ),
                dart_generated_dir=_expect_str(table, "dart_generated_dir", ctx=ctx),
                materialized_dir=_expect_str(table, "materialized_dir", ctx=ctx),
            )
        )
    return profiles


def _parse_targets(
    *, raw: dict[str, object], path_label: str
) -> AwareSdkTomlTargetsSpec:
    targets_raw = raw.get("targets")
    if targets_raw is None:
        return AwareSdkTomlTargetsSpec()
    targets_tbl = _as_table(targets_raw, ctx=f"[targets] at {path_label}")
    _expect_keys(
        targets_tbl,
        required=set(),
        optional={"python", "dart"},
        ctx="[targets]",
    )
    python_raw = targets_tbl.get("python")
    python: AwareSdkTomlPythonTargetSpec | None = None
    if python_raw is not None:
        python_tbl = _as_table(python_raw, ctx=f"[targets.python] at {path_label}")
        _expect_keys(
            python_tbl,
            required=set(),
            optional={"root_dir", "public_package"},
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
        python = AwareSdkTomlPythonTargetSpec(
            root_dir=root_dir,
            public_package=public_package,
        )

    dart_raw = targets_tbl.get("dart")
    dart: AwareSdkTomlDartTargetSpec | None = None
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
        dart = AwareSdkTomlDartTargetSpec(
            root_dir=root_dir,
            public_package=public_package,
        )

    return AwareSdkTomlTargetsSpec(
        python=python,
        dart=dart,
    )


def _parse_python_product_target(
    *,
    python_tbl: dict[str, object],
    key: str,
    ctx: str,
) -> AwareSdkTomlPythonProductTargetSpec:
    raw = python_tbl.get(key)
    if raw is None:
        return AwareSdkTomlPythonProductTargetSpec()
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
    return AwareSdkTomlPythonProductTargetSpec(
        package_dir=package_dir, root_dir=root_dir
    )


def _parse_dart_product_target(
    *,
    dart_tbl: dict[str, object],
    key: str,
    ctx: str,
) -> AwareSdkTomlDartProductTargetSpec:
    raw = dart_tbl.get(key)
    if raw is None:
        return AwareSdkTomlDartProductTargetSpec()
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
    return AwareSdkTomlDartProductTargetSpec(package_dir=package_dir, root_dir=root_dir)


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareSdkTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareSdkTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    items = cast(list[object], value)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AwareSdkTomlError(f"Expected {ctx}[{i}] to be a table/object")
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
        raise AwareSdkTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareSdkTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareSdkTomlError(f"Expected {ctx}.{key} to be a table; got {type(val)}")
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareSdkTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareSdkTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareSdkTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareSdkTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareSdkTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(
    root: dict[str, object], key: str, *, ctx: str
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareSdkTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareSdkTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _expect_opt_compilation_mode(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareSdkCompilationMode | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareSdkCompilationMode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in AwareSdkCompilationMode)
        raise AwareSdkTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_opt_dependency_kind(
    root: dict[str, object], key: str, *, ctx: str
) -> AwareSdkDependencyKind | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareSdkDependencyKind(value)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in AwareSdkDependencyKind)
        raise AwareSdkTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareSdkTomlError(
            f"{ctx} must not contain '.' (single-segment namespace); got {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise AwareSdkTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareSdkTomlError(
            f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}"
        )


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareSdkTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareSdkTomlError(
            f"{ctx} must be repo-relative (not absolute): {value!r}"
        )
    if ".." in p.parts:
        raise AwareSdkTomlError(f"{ctx} must not contain '..': {value!r}")


def _validate_sha256(value: str, *, ctx: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise AwareSdkTomlError(
            f"{ctx} must be a lowercase 64-character sha256 hex string; got {value!r}"
        )


def _normalize_uuid(value: str, *, ctx: str) -> str:
    raw = value.strip()
    if not raw:
        raise AwareSdkTomlError(f"{ctx} must be a non-empty UUID")
    try:
        return str(UUID(raw))
    except ValueError as exc:
        raise AwareSdkTomlError(f"{ctx} must be a valid UUID") from exc


__all__ = [
    "AwareSdkTomlError",
    "load_aware_sdk_toml_spec_from_text",
    "parse_sdk_manifest_bytes",
]
