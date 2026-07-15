from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_skill.manifest.spec import (
    AwareSkillCompilationMode,
    AwareSkillDependencyKind,
    AwareSkillTomlBuildSpec,
    AwareSkillTomlDependencySpec,
    AwareSkillTomlPackageSpec,
    AwareSkillTomlSpec,
)


class AwareSkillTomlError(ValueError):
    """Raised when `aware.skill.toml` fails strict validation."""


def load_aware_skill_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareSkillTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.skill.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareSkillTomlError(f"Failed to parse TOML at {path_label}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_skill_toml_raw(raw, path_label=path_label)


def load_aware_skill_toml_spec(*, toml_path: str | Path) -> AwareSkillTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareSkillTomlError(f"aware.skill.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareSkillTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_skill_toml_raw(raw, path_label=str(p))


def _parse_aware_skill_toml_raw(raw: dict[str, object], *, path_label: str) -> AwareSkillTomlSpec:
    _expect_keys(
        raw,
        required={"aware_skill", "skill", "build"},
        optional={"dependencies"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_skill", ctx="root")
    if spec_version != 1:
        raise AwareSkillTomlError(f"Unsupported aware.skill.toml version {spec_version}; expected 1")

    skill_tbl = _expect_table(raw, "skill", ctx="root")
    _expect_keys(
        skill_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[skill]",
    )
    package_name = _expect_str(skill_tbl, "package_name", ctx="[skill]")
    fqn_prefix = _expect_str(skill_tbl, "fqn_prefix", ctx="[skill]")
    version_number = _expect_opt_int(skill_tbl, "version_number", ctx="[skill]") or 1
    title = _expect_opt_str(skill_tbl, "title", ctx="[skill]")
    description = _expect_opt_str(skill_tbl, "description", ctx="[skill]")

    _validate_package_name(package_name, ctx="[skill].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[skill].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={"sources_dir", "include_paths", "exclude_paths", "force_fresh_scan", "compilation_mode"},
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "skills"
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or ["**/*.aware"]
    exclude_paths = _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    force_fresh_scan = _expect_opt_bool(build_tbl, "force_fresh_scan", ctx="[build]")
    if force_fresh_scan is None:
        force_fresh_scan = True
    compilation_mode = _expect_opt_compilation_mode(build_tbl, "compilation_mode", ctx="[build]")
    if compilation_mode is None:
        compilation_mode = AwareSkillCompilationMode.raw_xor

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for i, path in enumerate(include_paths):
        _validate_rel_path(path, ctx=f"[build].include_paths[{i}]")
    for i, path in enumerate(exclude_paths):
        _validate_rel_path(path, ctx=f"[build].exclude_paths[{i}]")

    deps_tbl = _as_table_list(raw.get("dependencies", []), ctx="[[dependencies]]")
    dependencies: list[AwareSkillTomlDependencySpec] = []
    seen_deps: set[str] = set()
    for i, dep_tbl in enumerate(deps_tbl):
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={"version_number", "kind", "expected_hash_sha256"},
            ctx=f"[[dependencies]] (index={i})",
        )
        dep_package_name = _expect_str(dep_tbl, "package_name", ctx=f"dependencies[{i}]")
        dep_version_number = _expect_opt_int(dep_tbl, "version_number", ctx=f"dependencies[{i}]")
        dep_kind = _expect_opt_dependency_kind(dep_tbl, "kind", ctx=f"dependencies[{i}]")
        if dep_kind is None:
            dep_kind = AwareSkillDependencyKind.package
        dep_expected_hash = _expect_opt_str(dep_tbl, "expected_hash_sha256", ctx=f"dependencies[{i}]")

        _validate_package_name(dep_package_name, ctx=f"dependencies[{i}].package_name")
        if dep_expected_hash is not None:
            dep_expected_hash = dep_expected_hash.strip().lower()
            _validate_sha256(dep_expected_hash, ctx=f"dependencies[{i}].expected_hash_sha256")
        if dep_package_name in seen_deps:
            raise AwareSkillTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at dependencies[{i}] in {path_label}"
            )
        seen_deps.add(dep_package_name)
        dependencies.append(
            AwareSkillTomlDependencySpec(
                package_name=dep_package_name,
                version_number=dep_version_number,
                kind=dep_kind,
                expected_hash_sha256=dep_expected_hash,
            )
        )

    return AwareSkillTomlSpec(
        aware_skill=spec_version,
        skill=AwareSkillTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareSkillTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
            compilation_mode=compilation_mode,
        ),
        dependencies=dependencies,
    )


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareSkillTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareSkillTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    items = cast(list[object], value)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AwareSkillTomlError(f"Expected {ctx}[{i}] to be a table/object")
        payload = cast(dict[object, object], item)
        tables.append({str(k): v for k, v in payload.items()})
    return tables


def _expect_keys(table: dict[str, object], *, required: set[str], optional: set[str], ctx: str) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareSkillTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareSkillTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be a table; got {type(val)}")
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(root: dict[str, object], key: str, *, ctx: str) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareSkillTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _expect_opt_compilation_mode(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareSkillCompilationMode | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareSkillCompilationMode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in AwareSkillCompilationMode)
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}") from exc


def _expect_opt_dependency_kind(root: dict[str, object], key: str, *, ctx: str) -> AwareSkillDependencyKind | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareSkillDependencyKind(value)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in AwareSkillDependencyKind)
        raise AwareSkillTomlError(f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}") from exc


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareSkillTomlError(f"{ctx} must not contain '.' (single-segment namespace); got {value!r}")
    if any(ch.isspace() for ch in value):
        raise AwareSkillTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareSkillTomlError(f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}")


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareSkillTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareSkillTomlError(f"{ctx} must be repo-relative (not absolute): {value!r}")
    if ".." in p.parts:
        raise AwareSkillTomlError(f"{ctx} must not contain '..': {value!r}")


def _validate_sha256(value: str, *, ctx: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise AwareSkillTomlError(f"{ctx} must be a lowercase 64-character sha256 hex string; got {value!r}")


__all__ = [
    "AwareSkillTomlError",
    "load_aware_skill_toml_spec",
    "load_aware_skill_toml_spec_from_text",
]
