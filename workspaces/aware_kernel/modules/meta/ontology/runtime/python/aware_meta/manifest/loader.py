from pathlib import Path
from typing import cast
from uuid import UUID

import tomllib

from aware_meta.manifest.spec import (
    AwareTomlBuildSpec,
    AwareTomlDependencySpec,
    AwareTomlLanguageMaterializationSpec,
    AwareTomlNamespaceMappingSpec,
    AwareTomlNamespaceSpec,
    AwareTomlPackageSpec,
    AwareTomlSpec,
    AwarePackageKind,
)


class AwareTomlError(ValueError):
    """Raised when `aware.toml` fails strict validation."""


RawTomlTable = dict[str, object]


def load_aware_toml_spec_from_text(
    *, toml_text: str, toml_path: str | Path | None = None
) -> AwareTomlSpec:
    """Parse `aware.toml` content from an in-memory string.

    This is used by editor tooling (LSP) where the authoritative contents may be an
    unsaved buffer rather than what's on disk.
    """
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.toml>"
    try:
        raw = tomllib.loads(toml_text or "")
    except Exception as exc:
        raise AwareTomlError(f"Failed to parse TOML at {path_label}: {exc}") from exc
    if not isinstance(raw, dict):
        raise AwareTomlError(f"Expected TOML root to be a table/object at {path_label}")
    return _parse_aware_toml_raw(cast(RawTomlTable, raw), path_label=path_label)


def load_aware_toml_spec(*, toml_path: str | Path) -> AwareTomlSpec:
    """
    Parse `aware.toml` into a pure spec object (no ORM, no UUID minting, no stubs).

    Notes:
    - Intentionally strict: unknown keys raise.
    - `dependencies` are identity-only entries; resolution/linking happens elsewhere.
    """
    p = Path(toml_path)
    if not p.exists():
        raise AwareTomlError(f"aware.toml not found: {p}")

    try:
        raw = tomllib.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AwareTomlError(f"Failed to parse TOML at {p}: {exc}") from exc

    if not isinstance(raw, dict):
        raise AwareTomlError(f"Expected TOML root to be a table/object at {p}")

    return _parse_aware_toml_raw(cast(RawTomlTable, raw), path_label=str(p))


def _parse_aware_toml_raw(raw: RawTomlTable, *, path_label: str) -> AwareTomlSpec:
    _expect_keys(
        raw,
        required={"aware", "package", "build"},
        optional={"dependencies", "language_materializations"},
        ctx="root",
    )
    aware_version = _expect_int(raw, "aware", ctx="root")
    if aware_version != 1:
        raise AwareTomlError(
            f"Unsupported aware.toml version {aware_version}; expected 1"
        )

    pkg_tbl = _expect_table(raw, "package", ctx="root")
    _expect_keys(
        pkg_tbl,
        required={"package_name", "fqn_prefix", "kind"},
        optional={
            "title",
            "description",
            "version_number",
            "function_impl_ownership",
            "function_impl_parity_policy",
        },
        ctx="[package]",
    )
    package_name = _expect_str(pkg_tbl, "package_name", ctx="[package]")
    fqn_prefix = _expect_str(pkg_tbl, "fqn_prefix", ctx="[package]")
    title = _expect_opt_str(pkg_tbl, "title", ctx="[package]")
    description = _expect_opt_str(pkg_tbl, "description", ctx="[package]")
    version_number = _expect_opt_int(pkg_tbl, "version_number", ctx="[package]") or 1
    function_impl_ownership = _normalize_function_impl_ownership(
        _expect_opt_str(
            pkg_tbl,
            "function_impl_ownership",
            ctx="[package]",
        )
    )
    function_impl_parity_policy = _normalize_function_impl_parity_policy(
        _expect_opt_str(
            pkg_tbl,
            "function_impl_parity_policy",
            ctx="[package]",
        )
    )
    kind_raw = _expect_str(pkg_tbl, "kind", ctx="[package]")

    try:
        kind = AwarePackageKind(kind_raw)
    except Exception as exc:
        raise AwareTomlError(
            f"Unsupported [package].kind={kind_raw!r}; expected one of {[p.value for p in AwarePackageKind]}"
        ) from exc
    _validate_package_name(package_name, ctx="[package].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[package].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required={"environment_slug"},
        optional={
            "sources_dir",
            "include_paths",
            "exclude_paths",
            "force_fresh_scan",
            "namespace",
        },
        ctx="[build]",
    )
    environment_slug = _expect_str(build_tbl, "environment_slug", ctx="[build]")
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "aware"
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or [
        "**/*.aware"
    ]
    exclude_paths = (
        _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    )
    force_fresh_scan = (
        _expect_opt_bool(build_tbl, "force_fresh_scan", ctx="[build]") or True
    )

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for i, s in enumerate(include_paths):
        _validate_rel_path(s, ctx=f"[build].include_paths[{i}]")
    for i, s in enumerate(exclude_paths):
        _validate_rel_path(s, ctx=f"[build].exclude_paths[{i}]")
    namespace = _parse_namespace_spec(build_tbl, path_label=path_label)

    deps_list = raw.get("dependencies", [])
    if deps_list is None:
        deps_list = []
    if not isinstance(deps_list, list):
        raise AwareTomlError(
            f"Expected 'dependencies' to be an array of tables at root; got {type(deps_list)}"
        )

    deps: list[AwareTomlDependencySpec] = []
    seen_deps: set[str] = set()
    for i, dep_tbl in enumerate(deps_list):
        if not isinstance(dep_tbl, dict):
            raise AwareTomlError(
                f"Expected dependencies[{i}] to be a table; got {type(dep_tbl)}"
            )
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={"ocg_commit_id", "version_number"},
            ctx=f"[[dependencies]] (index={i})",
        )
        dep_package_name = _expect_str(
            dep_tbl, "package_name", ctx=f"dependencies[{i}]"
        )
        ocg_commit_id_str = _expect_opt_str(
            dep_tbl, "ocg_commit_id", ctx=f"dependencies[{i}]"
        )
        dep_version_number = _expect_opt_int(
            dep_tbl, "version_number", ctx=f"dependencies[{i}]"
        )

        _validate_package_name(dep_package_name, ctx=f"dependencies[{i}].package_name")
        if dep_package_name in seen_deps:
            raise AwareTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at dependencies[{i}] in {path_label}"
            )
        seen_deps.add(dep_package_name)

        ocg_commit_id: UUID | None = None
        if ocg_commit_id_str is not None:
            try:
                ocg_commit_id = UUID(ocg_commit_id_str)
            except Exception as exc:
                raise AwareTomlError(
                    f"Invalid UUID for dependencies[{i}].ocg_commit_id: {ocg_commit_id_str}"
                ) from exc

        deps.append(
            AwareTomlDependencySpec(
                package_name=dep_package_name,
                version_number=dep_version_number,
                ocg_commit_id=ocg_commit_id,
            )
        )

    language_materializations = _parse_language_materialization_specs(
        raw, path_label=path_label
    )

    return AwareTomlSpec(
        aware=aware_version,
        package=AwareTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            kind=kind,
            title=title,
            description=description,
            function_impl_ownership=function_impl_ownership,
            function_impl_parity_policy=function_impl_parity_policy,
        ),
        build=AwareTomlBuildSpec(
            environment_slug=environment_slug,
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
            namespace=namespace,
        ),
        dependencies=deps,
        language_materializations=language_materializations,
    )


def _parse_language_materialization_specs(
    raw: RawTomlTable, *, path_label: str
) -> list[AwareTomlLanguageMaterializationSpec]:
    raw_language_materializations = raw.get("language_materializations", [])
    if raw_language_materializations is None:
        raw_language_materializations = []
    if not isinstance(raw_language_materializations, list):
        raise AwareTomlError(
            "Expected 'language_materializations' to be an array of tables "
            f"at root; got {type(raw_language_materializations)}"
        )

    materializations: list[AwareTomlLanguageMaterializationSpec] = []
    seen_targets: set[tuple[str, str, str, str | None]] = set()
    seen_roles: set[str] = set()
    for i, raw_materialization in enumerate(raw_language_materializations):
        if not isinstance(raw_materialization, dict):
            raise AwareTomlError(
                f"Expected language_materializations[{i}] to be a table; "
                f"got {type(raw_materialization)}"
            )
        tbl = cast(RawTomlTable, raw_materialization)
        _expect_keys(
            tbl,
            required={
                "role",
                "language",
                "output_dir",
                "import_root",
                "package_name",
            },
            optional={
                "materialization_source",
                "renderer_kind",
                "renderer_profile",
                "stable_ids_import_root",
                "stable_ids_resolution_policy",
                "source_is_runtime",
            },
            ctx=f"[[language_materializations]] (index={i})",
        )
        role = _expect_str(tbl, "role", ctx=f"language_materializations[{i}]").strip()
        language = _expect_str(
            tbl, "language", ctx=f"language_materializations[{i}]"
        ).strip()
        output_dir = _expect_str(
            tbl, "output_dir", ctx=f"language_materializations[{i}]"
        ).strip()
        import_root = _expect_str(
            tbl, "import_root", ctx=f"language_materializations[{i}]"
        ).strip()
        package_name = _expect_str(
            tbl, "package_name", ctx=f"language_materializations[{i}]"
        ).strip()
        materialization_source = (
            _expect_opt_str(
                tbl,
                "materialization_source",
                ctx=f"language_materializations[{i}]",
            )
            or "ontology"
        ).strip()
        renderer_kind = _strip_optional_str(
            _expect_opt_str(
                tbl,
                "renderer_kind",
                ctx=f"language_materializations[{i}]",
            )
        )
        renderer_profile = _strip_optional_str(
            _expect_opt_str(
                tbl,
                "renderer_profile",
                ctx=f"language_materializations[{i}]",
            )
        )
        stable_ids_import_root = _strip_optional_str(
            _expect_opt_str(
                tbl,
                "stable_ids_import_root",
                ctx=f"language_materializations[{i}]",
            )
        )
        stable_ids_resolution_policy = _strip_optional_str(
            _expect_opt_str(
                tbl,
                "stable_ids_resolution_policy",
                ctx=f"language_materializations[{i}]",
            )
        )
        if (
            stable_ids_resolution_policy is not None
            and stable_ids_resolution_policy != "class_strict"
        ):
            raise AwareTomlError(
                "language_materializations"
                f"[{i}].stable_ids_resolution_policy must be class_strict"
            )
        source_is_runtime = (
            _expect_opt_bool(
                tbl,
                "source_is_runtime",
                ctx=f"language_materializations[{i}]",
            )
            or False
        )

        _validate_rel_path(output_dir, ctx=f"language_materializations[{i}].output_dir")
        _validate_fqn_prefix(
            import_root, ctx=f"language_materializations[{i}].import_root"
        )
        _validate_package_name(
            package_name, ctx=f"language_materializations[{i}].package_name"
        )
        if stable_ids_import_root is not None:
            _validate_fqn_prefix(
                stable_ids_import_root,
                ctx=f"language_materializations[{i}].stable_ids_import_root",
            )
        if not materialization_source:
            raise AwareTomlError(
                "language_materializations"
                f"[{i}].materialization_source must be non-empty"
            )
        if role in seen_roles:
            raise AwareTomlError(
                f"Duplicate language_materializations role={role!r} in {path_label}"
            )
        seen_roles.add(role)

        identity = (language, output_dir, materialization_source, renderer_kind)
        if identity in seen_targets:
            raise AwareTomlError(
                "Duplicate language materialization target "
                f"language={language!r} output_dir={output_dir!r} "
                f"source={materialization_source!r} renderer_kind={renderer_kind!r} "
                f"in {path_label}"
            )
        seen_targets.add(identity)
        materializations.append(
            AwareTomlLanguageMaterializationSpec(
                role=role,
                language=language,
                output_dir=output_dir,
                import_root=import_root,
                package_name=package_name,
                materialization_source=materialization_source,
                renderer_kind=renderer_kind,
                renderer_profile=renderer_profile,
                stable_ids_import_root=stable_ids_import_root,
                stable_ids_resolution_policy=stable_ids_resolution_policy,
                source_is_runtime=source_is_runtime,
            )
        )
    return materializations


def _expect_keys(
    tbl: RawTomlTable, *, required: set[str], optional: set[str], ctx: str
) -> None:
    allowed = required | optional
    extra = set(tbl.keys()) - allowed
    missing = required - set(tbl.keys())
    if extra:
        raise AwareTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _strip_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_function_impl_ownership(value: str | None) -> str:
    normalized = str(value or "authored").strip().lower() or "authored"
    if normalized not in {"authored", "compiler"}:
        raise AwareTomlError(
            "[package].function_impl_ownership must be one of: authored, compiler"
        )
    return normalized


def _normalize_function_impl_parity_policy(value: str | None) -> str:
    normalized = str(value or "off").strip().lower() or "off"
    if normalized not in {"off", "warn", "error"}:
        raise AwareTomlError(
            "[package].function_impl_parity_policy must be one of: off, warn, error"
        )
    return normalized


def _parse_namespace_spec(
    build_tbl: RawTomlTable, *, path_label: str
) -> AwareTomlNamespaceSpec:
    raw_namespace = build_tbl.get("namespace")
    if raw_namespace is None:
        return AwareTomlNamespaceSpec()
    if not isinstance(raw_namespace, dict):
        raise AwareTomlError(
            f"Expected [build].namespace to be a table at {path_label}; got {type(raw_namespace)}"
        )
    namespace_tbl = cast(RawTomlTable, raw_namespace)
    mappings: list[AwareTomlNamespaceMappingSpec] = []
    for path, raw_namespace_value in sorted(namespace_tbl.items()):
        if path in {"mode", "roots"}:
            raise AwareTomlError(
                "[build.namespace] is a path-to-namespace mapping; "
                + f"old key {path!r} is not supported"
            )
        if not isinstance(raw_namespace_value, str):
            raise AwareTomlError(
                "[build.namespace] values must be namespace strings; "
                + f"path {path!r} has {type(raw_namespace_value)}"
            )
        namespace = raw_namespace_value.strip()
        if not namespace:
            raise AwareTomlError(
                f"[build.namespace].{path!r} must map to a non-empty namespace"
            )
        _validate_rel_path(path, ctx=f"[build.namespace].{path!r}")
        _validate_namespace_path(
            namespace,
            ctx=f"[build.namespace].{path!r}",
        )
        mappings.append(
            AwareTomlNamespaceMappingSpec(
                path=path,
                namespace=namespace,
            )
        )
    return AwareTomlNamespaceSpec(mappings=mappings)


def _expect_table(root: RawTomlTable, key: str, *, ctx: str) -> RawTomlTable:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareTomlError(f"Expected {ctx}.{key} to be a table; got {type(val)}")
    return cast(RawTomlTable, val)


def _expect_str(root: RawTomlTable, key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: RawTomlTable, key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: RawTomlTable, key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: RawTomlTable, key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: RawTomlTable, key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(root: RawTomlTable, key: str, *, ctx: str) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    for i, item in enumerate(val):
        if not isinstance(item, str):
            raise AwareTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareTomlError(
            f"{ctx} must not contain '.' (single-segment namespace); got {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise AwareTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareTomlError(
            f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}"
        )


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_namespace_segment(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    forbidden = (".", "/", "\\", "-")
    if any(ch in value for ch in forbidden):
        raise AwareTomlError(
            f"{ctx} must be a single FQN segment without '.', '/', '\\\\', or '-'; got {value!r}"
        )


def _validate_namespace_path(value: str, *, ctx: str) -> None:
    parts = [part.strip() for part in value.split(".")]
    if any(not part for part in parts):
        raise AwareTomlError(
            f"{ctx} namespace must contain non-empty dot-separated segments; got {value!r}"
        )
    for index, part in enumerate(parts):
        _validate_namespace_segment(part, ctx=f"{ctx}.namespace[{index}]")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareTomlError(f"{ctx} must be repo-relative (not absolute): {value!r}")
    if ".." in p.parts:
        raise AwareTomlError(f"{ctx} must not contain '..': {value!r}")


__all__ = [
    "AwareTomlError",
    "load_aware_toml_spec",
    "load_aware_toml_spec_from_text",
]
