from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_experience.manifest.spec import (
    AwareExperienceDependencyKind,
    AwareExperienceTomlBuildSpec,
    AwareExperienceTomlDependencySpec,
    AwareExperienceTomlLanguageTargetSpec,
    AwareExperienceTomlPackageSpec,
    AwareExperienceTomlSpec,
)


class AwareExperienceTomlError(ValueError):
    """Raised when `aware.experience.toml` fails strict validation."""


def load_aware_experience_toml_spec_from_text(
    *, toml_text: str, toml_path: str | Path | None = None
) -> AwareExperienceTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.experience.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareExperienceTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_experience_toml_raw(raw, path_label=path_label)


def load_aware_experience_toml_spec(
    *, toml_path: str | Path
) -> AwareExperienceTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareExperienceTomlError(f"aware.experience.toml not found: {p}")

    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareExperienceTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_experience_toml_raw(raw, path_label=str(p))


def _parse_aware_experience_toml_raw(
    raw: dict[str, object], *, path_label: str
) -> AwareExperienceTomlSpec:
    _expect_keys(
        raw,
        required={"aware_experience", "experience", "build"},
        optional={"dependencies", "targets"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_experience", ctx="root")
    if spec_version != 1:
        raise AwareExperienceTomlError(
            f"Unsupported aware.experience.toml version {spec_version}; expected 1"
        )

    experience_tbl = _expect_table(raw, "experience", ctx="root")
    _expect_keys(
        experience_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[experience]",
    )
    package_name = _expect_str(experience_tbl, "package_name", ctx="[experience]")
    fqn_prefix = _expect_str(experience_tbl, "fqn_prefix", ctx="[experience]")
    version_number = (
        _expect_opt_int(experience_tbl, "version_number", ctx="[experience]") or 1
    )
    title = _expect_opt_str(experience_tbl, "title", ctx="[experience]")
    description = _expect_opt_str(experience_tbl, "description", ctx="[experience]")

    _validate_package_name(package_name, ctx="[experience].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[experience].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required={"environment_handle"},
        optional={"sources_dir", "include_paths", "exclude_paths", "force_fresh_scan"},
        ctx="[build]",
    )
    environment_handle = _expect_str(build_tbl, "environment_handle", ctx="[build]")
    sources_dir = (
        _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "experiences"
    )
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
    for i, path in enumerate(include_paths):
        _validate_rel_path(path, ctx=f"[build].include_paths[{i}]")
    for i, path in enumerate(exclude_paths):
        _validate_rel_path(path, ctx=f"[build].exclude_paths[{i}]")

    deps_tbl = _as_table_list(raw.get("dependencies", []), ctx="[[dependencies]]")
    dependencies: list[AwareExperienceTomlDependencySpec] = []
    seen_deps: set[str] = set()
    for i, dep_tbl in enumerate(deps_tbl):
        _expect_keys(
            dep_tbl,
            required={"package_name", "kind"},
            optional={"version_number"},
            ctx=f"[[dependencies]] (index={i})",
        )
        dep_package_name = _expect_str(
            dep_tbl, "package_name", ctx=f"dependencies[{i}]"
        )
        dep_kind_token = _expect_str(dep_tbl, "kind", ctx=f"dependencies[{i}]")
        dep_version_number = _expect_opt_int(
            dep_tbl, "version_number", ctx=f"dependencies[{i}]"
        )

        try:
            dep_kind = AwareExperienceDependencyKind(dep_kind_token)
        except ValueError as exc:
            raise AwareExperienceTomlError(
                f"dependencies[{i}].kind must be one of "
                + f"{[item.value for item in AwareExperienceDependencyKind]}; "
                + f"got {dep_kind_token!r}"
            ) from exc

        _validate_package_name(dep_package_name, ctx=f"dependencies[{i}].package_name")
        if dep_package_name in seen_deps:
            raise AwareExperienceTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at dependencies[{i}] in {path_label}"
            )
        seen_deps.add(dep_package_name)
        dependencies.append(
            AwareExperienceTomlDependencySpec(
                package_name=dep_package_name,
                kind=dep_kind,
                version_number=dep_version_number,
            )
        )

    targets_tbl = _expect_opt_table(raw, "targets", ctx="root") or {}
    targets: dict[str, AwareExperienceTomlLanguageTargetSpec] = {}
    for language, target_tbl_obj in sorted(targets_tbl.items()):
        target_tbl = _as_table(target_tbl_obj, ctx=f"[targets.{language}]")
        _expect_keys(
            target_tbl,
            required=set(),
            optional={"root_dir", "package_dir"},
            ctx=f"[targets.{language}]",
        )
        normalized_language = _validate_language_target(language, ctx="[targets]")
        if normalized_language in targets:
            raise AwareExperienceTomlError(
                f"Duplicate target language={normalized_language!r} in {path_label}"
            )
        target_root_dir = (
            _expect_opt_str(target_tbl, "root_dir", ctx=f"[targets.{language}]")
            or f"languages/{normalized_language}"
        )
        target_package_dir = (
            _expect_opt_str(target_tbl, "package_dir", ctx=f"[targets.{language}]")
            or fqn_prefix
        )
        _validate_rel_path(target_root_dir, ctx=f"[targets.{language}].root_dir")
        _validate_rel_path(target_package_dir, ctx=f"[targets.{language}].package_dir")
        targets[normalized_language] = AwareExperienceTomlLanguageTargetSpec(
            language=normalized_language,
            root_dir=target_root_dir,
            package_dir=target_package_dir,
        )

    return AwareExperienceTomlSpec(
        aware_experience=spec_version,
        experience=AwareExperienceTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareExperienceTomlBuildSpec(
            environment_handle=environment_handle,
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
        ),
        dependencies=dependencies,
        targets=targets,
    )


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareExperienceTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareExperienceTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    items = cast(list[object], value)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AwareExperienceTomlError(f"Expected {ctx}[{i}] to be a table/object")
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
        raise AwareExperienceTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareExperienceTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareExperienceTomlError(
            f"Expected {ctx}.{key} to be a table; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_opt_table(
    root: dict[str, object], key: str, *, ctx: str
) -> dict[str, object] | None:
    val = root.get(key)
    if val is None:
        return None
    if not isinstance(val, dict):
        raise AwareExperienceTomlError(
            f"Expected {ctx}.{key} to be a table; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareExperienceTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareExperienceTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareExperienceTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareExperienceTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareExperienceTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(
    root: dict[str, object], key: str, *, ctx: str
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareExperienceTomlError(
            f"Expected {ctx}.{key} to be a list[str] or null"
        )
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareExperienceTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareExperienceTomlError(
            f"{ctx} must not contain '.' (single-segment namespace); got {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise AwareExperienceTomlError(
            f"{ctx} must not contain whitespace; got {value!r}"
        )
    if "-" in value:
        raise AwareExperienceTomlError(
            f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}"
        )


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareExperienceTomlError(
            f"{ctx} must not contain whitespace; got {value!r}"
        )


def _validate_language_target(value: str, *, ctx: str) -> str:
    normalized = (value or "").strip().casefold()
    if normalized not in {"dart", "python"}:
        raise AwareExperienceTomlError(
            f"{ctx} supports only 'dart' and 'python' targets; got {value!r}"
        )
    return normalized


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareExperienceTomlError(
            f"{ctx} must be repo-relative (not absolute): {value!r}"
        )
    if ".." in p.parts:
        raise AwareExperienceTomlError(f"{ctx} must not contain '..': {value!r}")


__all__ = [
    "AwareExperienceTomlError",
    "load_aware_experience_toml_spec",
    "load_aware_experience_toml_spec_from_text",
]
