"""Strict loader for `aware.ontology.toml`."""

from __future__ import annotations

from pathlib import Path
import re
from typing import cast

import tomllib

from aware_ontology.manifest.spec import (
    AwareOntologyDependencySpec,
    AwareOntologyDescriptorSpec,
    AwareOntologyLanguageMaterializationTargetSpec,
    AwareOntologyLayoutSpec,
    AwareOntologyRuntimeSpec,
    AwareOntologySemanticContractSpec,
    AwareOntologyTomlSpec,
)


class AwareOntologyTomlError(ValueError):
    """Raised when `aware.ontology.toml` fails strict validation."""


RawTomlTable = dict[str, object]

_PACKAGE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_FQN_PREFIX_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PROVIDER_KEY_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_SEMANTIC_ROLE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_PYTHON_IMPORT_RE = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")
_LAYOUT_OUTPUT_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_POLICY_STABLE_IDS_OWNERSHIP = frozenset(("authored", "compiler"))
_POLICY_STABLE_IDS_PARITY = frozenset(("off", "warn", "error"))
_POLICY_STABLE_IDS_RESOLUTION = frozenset(("class_strict",))
_POLICY_FUNCTION_IMPL_OWNERSHIP = frozenset(("authored", "compiler"))
_POLICY_FUNCTION_IMPL_PARITY = frozenset(("off", "warn", "error"))
_LAYOUT_PROFILES = frozenset(
    (
        "module_structure_ontology_v1",
        "ontology_structure_v1",
    )
)


def load_aware_ontology_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareOntologyTomlSpec:
    path_label = str(toml_path) if toml_path is not None else "<aware.ontology.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareOntologyTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_ontology_toml_raw(raw, path_label=path_label)


def load_aware_ontology_toml_spec(
    *,
    toml_path: str | Path,
) -> AwareOntologyTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareOntologyTomlError(f"aware.ontology.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        raise AwareOntologyTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_ontology_toml_raw(raw, path_label=str(p))


def _parse_aware_ontology_toml_raw(
    raw: RawTomlTable,
    *,
    path_label: str,
) -> AwareOntologyTomlSpec:
    _expect_keys(
        raw,
        required={"aware_ontology", "ontology"},
        optional={"runtime", "semantic_contract", "layout", "dependencies"},
        ctx="root",
    )
    aware_ontology = _expect_int(raw, "aware_ontology", ctx="root")
    if aware_ontology != 1:
        raise AwareOntologyTomlError(
            f"Unsupported aware.ontology.toml version {aware_ontology}; expected 1"
        )

    ontology = _parse_ontology_descriptor(
        _expect_table(raw, "ontology", ctx="root"),
    )
    runtime = _parse_runtime(raw.get("runtime"))
    semantic_contract = _parse_semantic_contract(raw.get("semantic_contract"))
    layout = _parse_layout(raw.get("layout"))
    dependencies = _parse_dependencies(
        raw.get("dependencies", []),
        path_label=path_label,
    )
    return AwareOntologyTomlSpec(
        aware_ontology=aware_ontology,
        ontology=ontology,
        runtime=runtime,
        semantic_contract=semantic_contract,
        layout=layout,
        dependencies=dependencies,
        language_materialization_targets=_default_language_materialization_targets(
            ontology=ontology,
            runtime=runtime,
            layout=layout,
        ),
    )


def _parse_ontology_descriptor(tbl: RawTomlTable) -> AwareOntologyDescriptorSpec:
    _expect_keys(
        tbl,
        required={"package_name", "fqn_prefix", "source_manifest"},
        optional={
            "version_number",
            "title",
            "description",
            "package_root",
            "sources_root",
            "stable_ids_ownership",
            "stable_ids_parity_policy",
            "stable_ids_resolution_policy",
            "function_impl_ownership",
            "function_impl_parity_policy",
        },
        ctx="[ontology]",
    )
    package_name = _expect_str(tbl, "package_name", ctx="[ontology]").strip()
    fqn_prefix = _expect_str(tbl, "fqn_prefix", ctx="[ontology]").strip()
    source_manifest = _expect_str(tbl, "source_manifest", ctx="[ontology]").strip()
    package_root = _expect_opt_str(tbl, "package_root", ctx="[ontology]") or "."
    sources_root = _expect_opt_str(tbl, "sources_root", ctx="[ontology]")

    _validate_package_name(package_name, ctx="[ontology].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[ontology].fqn_prefix")
    _validate_rel_path(source_manifest, ctx="[ontology].source_manifest")
    if Path(source_manifest).name != "aware.toml":
        raise AwareOntologyTomlError(
            "[ontology].source_manifest must point to `aware.toml`, "
            f"found {source_manifest!r}"
        )
    default_sources_root = (Path(source_manifest).parent / "aware").as_posix()
    _validate_rel_path(package_root, ctx="[ontology].package_root")
    sources_root = sources_root or default_sources_root
    _validate_rel_path(sources_root, ctx="[ontology].sources_root")

    return AwareOntologyDescriptorSpec(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_manifest=source_manifest,
        version_number=_expect_opt_int(
            tbl,
            "version_number",
            ctx="[ontology]",
        )
        or 1,
        title=_normalized_optional_text(
            _expect_opt_str(tbl, "title", ctx="[ontology]")
        ),
        description=_normalized_optional_text(
            _expect_opt_str(tbl, "description", ctx="[ontology]")
        ),
        package_root=package_root.strip() or ".",
        sources_root=sources_root.strip(),
        stable_ids_ownership=_normalize_policy(
            _expect_opt_str(tbl, "stable_ids_ownership", ctx="[ontology]"),
            default="authored",
            allowed=_POLICY_STABLE_IDS_OWNERSHIP,
            ctx="[ontology].stable_ids_ownership",
        ),
        stable_ids_parity_policy=_normalize_policy(
            _expect_opt_str(tbl, "stable_ids_parity_policy", ctx="[ontology]"),
            default="warn",
            allowed=_POLICY_STABLE_IDS_PARITY,
            ctx="[ontology].stable_ids_parity_policy",
        ),
        stable_ids_resolution_policy=_normalize_policy(
            _expect_opt_str(tbl, "stable_ids_resolution_policy", ctx="[ontology]"),
            default="class_strict",
            allowed=_POLICY_STABLE_IDS_RESOLUTION,
            ctx="[ontology].stable_ids_resolution_policy",
        ),
        function_impl_ownership=_normalize_policy(
            _expect_opt_str(tbl, "function_impl_ownership", ctx="[ontology]"),
            default="authored",
            allowed=_POLICY_FUNCTION_IMPL_OWNERSHIP,
            ctx="[ontology].function_impl_ownership",
        ),
        function_impl_parity_policy=_normalize_policy(
            _expect_opt_str(tbl, "function_impl_parity_policy", ctx="[ontology]"),
            default="off",
            allowed=_POLICY_FUNCTION_IMPL_PARITY,
            ctx="[ontology].function_impl_parity_policy",
        ),
    )


def _parse_layout(value: object) -> AwareOntologyLayoutSpec | None:
    if value is None:
        return None
    tbl = _as_table(value, ctx="[layout]")
    _expect_keys(
        tbl,
        required={"profile"},
        optional={
            "source_dir",
            "generated_dir",
            "runtime_dir",
            "orm_models_dir",
            "outputs",
        },
        ctx="[layout]",
    )
    profile = _expect_str(tbl, "profile", ctx="[layout]").strip()
    if profile not in _LAYOUT_PROFILES:
        raise AwareOntologyTomlError(
            "[layout].profile must be one of "
            f"{sorted(_LAYOUT_PROFILES)}, found {profile!r}"
        )
    defaults = _layout_defaults(profile=profile)
    source_dir = _layout_path_value(
        tbl=tbl,
        key="source_dir",
        default=defaults.source_dir,
    )
    generated_dir = _layout_path_value(
        tbl=tbl,
        key="generated_dir",
        default=defaults.generated_dir,
    )
    runtime_dir = _layout_path_value(
        tbl=tbl,
        key="runtime_dir",
        default=defaults.runtime_dir,
    )
    orm_models_dir = _layout_path_value(
        tbl=tbl,
        key="orm_models_dir",
        default=defaults.orm_models_dir,
    )
    output_dirs = _layout_output_dirs(
        value=tbl.get("outputs"),
        defaults=defaults.output_dirs,
    )
    return AwareOntologyLayoutSpec(
        profile=profile,
        source_dir=source_dir,
        generated_dir=generated_dir,
        runtime_dir=runtime_dir,
        orm_models_dir=orm_models_dir,
        output_dirs=output_dirs,
    )


def _layout_defaults(*, profile: str) -> AwareOntologyLayoutSpec:
    if profile == "ontology_structure_v1":
        return AwareOntologyLayoutSpec(
            profile=profile,
            source_dir="structure/aware",
            generated_dir="structure",
            runtime_dir="runtime/python",
            orm_models_dir="structure/orm_models",
            output_dirs={
                "python": {
                    "ontology": "structure/python/orm_runtime",
                    "orm_models": "structure/python/orm_models",
                    "dto": "structure/python/dto",
                },
                "sql": {
                    "ontology": "structure/sql/schema",
                    "sqlite": "structure/sql/sqlite",
                },
            },
        )
    module_output_dirs = {
        "python": {
            "ontology": "structure/ontology/python",
            "orm_models": "structure/ontology_orm_models/python",
        },
        "sql": {
            "ontology": "structure/ontology/sql",
            "sqlite": "structure/ontology/sqlite",
        },
    }
    return AwareOntologyLayoutSpec(
        profile=profile,
        source_dir="structure/ontology/aware",
        generated_dir="structure/ontology",
        runtime_dir="runtime",
        orm_models_dir="structure/ontology_orm_models",
        output_dirs=module_output_dirs,
    )


def _default_language_materialization_targets(
    *,
    ontology: AwareOntologyDescriptorSpec,
    runtime: AwareOntologyRuntimeSpec | None,
    layout: AwareOntologyLayoutSpec | None,
) -> tuple[AwareOntologyLanguageMaterializationTargetSpec, ...]:
    layout_spec = layout or _layout_defaults(profile="module_structure_ontology_v1")
    output_dirs = layout_spec.output_dirs
    fqn_prefix = ontology.fqn_prefix
    ontology_import_root = f"{fqn_prefix}_ontology"
    targets: list[AwareOntologyLanguageMaterializationTargetSpec] = []

    python_outputs = output_dirs.get("python", {})
    python_ontology_dir = python_outputs.get("ontology")
    if python_ontology_dir:
        targets.append(
            AwareOntologyLanguageMaterializationTargetSpec(
                role="python_ontology",
                language="python",
                output_dir=python_ontology_dir,
                import_root=ontology_import_root,
                package_name=_python_distribution_package_name(ontology_import_root),
                materialization_source="ontology",
                renderer_profile="orm_runtime",
                stable_ids_import_root=ontology_import_root,
            )
        )
    python_orm_models_dir = python_outputs.get("orm_models")
    if python_orm_models_dir:
        orm_models_import_root = f"{ontology_import_root}_orm_models"
        targets.append(
            AwareOntologyLanguageMaterializationTargetSpec(
                role="python_orm_models",
                language="python",
                output_dir=python_orm_models_dir,
                import_root=orm_models_import_root,
                package_name=_python_distribution_package_name(
                    orm_models_import_root
                ),
                materialization_source="ontology_orm_models",
                renderer_profile="orm_models",
                stable_ids_import_root=orm_models_import_root,
            )
        )
    python_dto_dir = python_outputs.get("dto")
    if python_dto_dir:
        dto_import_root = f"{ontology_import_root}_dto"
        targets.append(
            AwareOntologyLanguageMaterializationTargetSpec(
                role="python_dto",
                language="python",
                output_dir=python_dto_dir,
                import_root=dto_import_root,
                package_name=_python_distribution_package_name(dto_import_root),
                materialization_source="ontology_dto",
                renderer_profile="ontology_dto",
                stable_ids_import_root=dto_import_root,
            )
        )

    dart_outputs = output_dirs.get("dart", {})
    dart_ontology_dir = dart_outputs.get("ontology")
    if dart_ontology_dir:
        targets.append(
            AwareOntologyLanguageMaterializationTargetSpec(
                role="dart_ontology",
                language="dart",
                output_dir=dart_ontology_dir,
                import_root=ontology_import_root,
                package_name=ontology.package_name,
                materialization_source="ontology",
                renderer_profile="orm_runtime",
                stable_ids_import_root=ontology_import_root,
            )
        )
    dart_dto_dir = dart_outputs.get("dto")
    if dart_dto_dir:
        dart_dto_import_root = f"{ontology_import_root}_dto"
        targets.append(
            AwareOntologyLanguageMaterializationTargetSpec(
                role="dart_dto",
                language="dart",
                output_dir=dart_dto_dir,
                import_root=dart_dto_import_root,
                package_name=f"{ontology.package_name}-dto",
                materialization_source="ontology_dto",
                renderer_profile="ontology_dto",
                stable_ids_import_root=dart_dto_import_root,
            )
        )

    sql_ontology_dir = output_dirs.get("sql", {}).get("ontology")
    if sql_ontology_dir:
        targets.append(
            AwareOntologyLanguageMaterializationTargetSpec(
                role="sql_ontology",
                language="sql",
                output_dir=sql_ontology_dir,
                import_root=f"{fqn_prefix}_sql",
                package_name=ontology.package_name,
                materialization_source="ontology",
                renderer_profile="orm_runtime",
                stable_ids_import_root=ontology_import_root,
            )
        )

    runtime_output_dir = _runtime_language_materialization_output_dir(
        ontology=ontology,
        runtime=runtime,
        layout=layout_spec,
    )
    runtime_import_root = runtime.import_root if runtime is not None else fqn_prefix
    runtime_package_name = (
        runtime.project_name if runtime is not None else runtime_import_root
    )
    if runtime_output_dir is not None:
        if ontology.function_impl_ownership != "compiler":
            targets.append(
                AwareOntologyLanguageMaterializationTargetSpec(
                    role="python_runtime_handlers_impl",
                    language="python",
                    output_dir=runtime_output_dir,
                    import_root=runtime_import_root,
                    package_name=runtime_package_name,
                    materialization_source="runtime_handlers",
                    code_package_surface="runtime",
                    source_is_runtime=True,
                    renderer_kind="runtime_handlers_impl",
                    stable_ids_import_root=ontology_import_root,
                )
            )
        targets.append(
            AwareOntologyLanguageMaterializationTargetSpec(
                role="python_runtime_handlers_meta",
                language="python",
                output_dir=runtime_output_dir,
                import_root=runtime_import_root,
                package_name=runtime_package_name,
                materialization_source="runtime_handlers",
                code_package_surface="runtime",
                source_is_runtime=True,
                renderer_kind="runtime_handlers_meta",
                stable_ids_import_root=ontology_import_root,
            )
        )
    return tuple(targets)


def _python_distribution_package_name(import_root: str) -> str:
    return import_root.strip().replace("_", "-")


def _runtime_language_materialization_output_dir(
    *,
    ontology: AwareOntologyDescriptorSpec,
    runtime: AwareOntologyRuntimeSpec | None,
    layout: AwareOntologyLayoutSpec,
) -> str | None:
    import_root = runtime.import_root if runtime is not None else ontology.fqn_prefix
    if not import_root:
        return None
    if runtime is not None:
        return (Path(runtime.manifest).parent / import_root).as_posix()
    return (Path(layout.runtime_dir) / import_root).as_posix()


def _layout_path_value(
    *,
    tbl: RawTomlTable,
    key: str,
    default: str,
) -> str:
    value = (_expect_opt_str(tbl, key, ctx="[layout]") or default).strip()
    if not value:
        raise AwareOntologyTomlError(f"Expected [layout].{key} to be non-empty")
    _validate_rel_path(value, ctx=f"[layout].{key}")
    return value


def _layout_output_dirs(
    *,
    value: object,
    defaults: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    output_dirs: dict[str, dict[str, str]] = {
        language: dict(targets) for language, targets in defaults.items()
    }
    if value is None:
        return output_dirs

    outputs_tbl = _as_table(value, ctx="[layout.outputs]")
    for language, raw_targets in outputs_tbl.items():
        language_key = language.strip()
        _validate_layout_output_key(language_key, ctx="[layout.outputs] key")
        target_tbl = _as_table(
            raw_targets,
            ctx=f"[layout.outputs.{language_key}]",
        )
        if not target_tbl:
            raise AwareOntologyTomlError(
                f"[layout.outputs.{language_key}] must not be empty"
            )
        language_outputs = dict(output_dirs.get(language_key, {}))
        for output_key, raw_path in target_tbl.items():
            target_key = output_key.strip()
            _validate_layout_output_key(
                target_key,
                ctx=f"[layout.outputs.{language_key}] key",
            )
            if not isinstance(raw_path, str):
                raise AwareOntologyTomlError(
                    f"Expected [layout.outputs.{language_key}].{target_key} "
                    "to be a string"
                )
            output_path = raw_path.strip()
            if not output_path:
                raise AwareOntologyTomlError(
                    f"Expected [layout.outputs.{language_key}].{target_key} "
                    "to be non-empty"
                )
            _validate_rel_path(
                output_path,
                ctx=f"[layout.outputs.{language_key}].{target_key}",
            )
            language_outputs[target_key] = output_path
        output_dirs[language_key] = language_outputs
    return output_dirs


def _validate_layout_output_key(value: str, *, ctx: str) -> None:
    if not _LAYOUT_OUTPUT_KEY_RE.match(value):
        raise AwareOntologyTomlError(
            f"Invalid {ctx}: {value!r}; expected lowercase identifier"
        )


def _parse_runtime(value: object) -> AwareOntologyRuntimeSpec | None:
    if value is None:
        return None
    tbl = _as_table(value, ctx="[runtime]")
    _expect_keys(
        tbl,
        required={"manifest", "project_name", "import_root"},
        optional=set(),
        ctx="[runtime]",
    )
    manifest = _expect_str(tbl, "manifest", ctx="[runtime]").strip()
    project_name = _expect_str(tbl, "project_name", ctx="[runtime]").strip()
    import_root = _expect_str(tbl, "import_root", ctx="[runtime]").strip()
    _validate_rel_path(manifest, ctx="[runtime].manifest")
    if Path(manifest).name != "pyproject.toml":
        raise AwareOntologyTomlError(
            f"[runtime].manifest must point to `pyproject.toml`, found {manifest!r}"
        )
    _validate_package_name(project_name, ctx="[runtime].project_name")
    _validate_python_import(import_root, ctx="[runtime].import_root")
    return AwareOntologyRuntimeSpec(
        manifest=manifest,
        project_name=project_name,
        import_root=import_root,
    )


def _parse_semantic_contract(
    value: object,
) -> AwareOntologySemanticContractSpec | None:
    if value is None:
        return None
    tbl = _as_table(value, ctx="[semantic_contract]")
    _expect_keys(
        tbl,
        required={"provider_key", "role", "module"},
        optional={"contract", "owns_manifest_kinds", "capabilities"},
        ctx="[semantic_contract]",
    )
    provider_key = _expect_str(
        tbl,
        "provider_key",
        ctx="[semantic_contract]",
    ).strip()
    role = _expect_str(tbl, "role", ctx="[semantic_contract]").strip()
    module = _expect_str(tbl, "module", ctx="[semantic_contract]").strip()
    contract = (
        _expect_opt_str(tbl, "contract", ctx="[semantic_contract]")
        or "aware.semantic_provider"
    ).strip()
    owns_manifest_kinds = tuple(
        item.strip()
        for item in (
            _expect_opt_str_list(
                tbl,
                "owns_manifest_kinds",
                ctx="[semantic_contract]",
            )
            or []
        )
    )
    capabilities = tuple(
        item.strip()
        for item in (
            _expect_opt_str_list(tbl, "capabilities", ctx="[semantic_contract]") or []
        )
    )
    _validate_provider_key(provider_key, ctx="[semantic_contract].provider_key")
    _validate_semantic_role(role, ctx="[semantic_contract].role")
    _validate_semantic_role(contract, ctx="[semantic_contract].contract")
    _validate_python_import(module, ctx="[semantic_contract].module")
    for index, item in enumerate(owns_manifest_kinds):
        _validate_provider_key(
            item,
            ctx=f"[semantic_contract].owns_manifest_kinds[{index}]",
        )
    for index, item in enumerate(capabilities):
        _validate_provider_key(
            item,
            ctx=f"[semantic_contract].capabilities[{index}]",
        )
    return AwareOntologySemanticContractSpec(
        provider_key=provider_key,
        role=role,
        contract=contract,
        module=module,
        owns_manifest_kinds=owns_manifest_kinds,
        capabilities=capabilities,
    )


def _parse_dependencies(
    value: object,
    *,
    path_label: str,
) -> tuple[AwareOntologyDependencySpec, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise AwareOntologyTomlError(
            f"Expected dependencies to be an array of tables at {path_label}"
        )
    dependencies: list[AwareOntologyDependencySpec] = []
    seen: set[str] = set()
    items = cast(list[object], value)
    for index, item in enumerate(items):
        tbl = _as_table(item, ctx=f"dependencies[{index}]")
        _expect_keys(
            tbl,
            required={"package_name"},
            optional={"version_number", "expected_hash_sha256"},
            ctx=f"[[dependencies]] (index={index})",
        )
        package_name = _expect_str(
            tbl,
            "package_name",
            ctx=f"dependencies[{index}]",
        ).strip()
        _validate_package_name(
            package_name,
            ctx=f"dependencies[{index}].package_name",
        )
        if package_name in seen:
            raise AwareOntologyTomlError(
                f"Duplicate dependency package_name={package_name!r} at "
                f"dependencies[{index}] in {path_label}"
            )
        seen.add(package_name)
        expected_hash = _normalized_optional_text(
            _expect_opt_str(
                tbl,
                "expected_hash_sha256",
                ctx=f"dependencies[{index}]",
            )
        )
        if expected_hash is not None:
            _validate_sha256(
                expected_hash,
                ctx=f"dependencies[{index}].expected_hash_sha256",
            )
        dependencies.append(
            AwareOntologyDependencySpec(
                package_name=package_name,
                version_number=_expect_opt_int(
                    tbl,
                    "version_number",
                    ctx=f"dependencies[{index}]",
                ),
                expected_hash_sha256=expected_hash,
            )
        )
    return tuple(dependencies)


def _as_table(value: object, *, ctx: str) -> RawTomlTable:
    if not isinstance(value, dict):
        raise AwareOntologyTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _expect_keys(
    tbl: RawTomlTable,
    *,
    required: set[str],
    optional: set[str],
    ctx: str,
) -> None:
    allowed = required | optional
    extra = set(tbl.keys()) - allowed
    missing = required - set(tbl.keys())
    if extra:
        raise AwareOntologyTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareOntologyTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: RawTomlTable, key: str, *, ctx: str) -> RawTomlTable:
    val = root.get(key)
    return _as_table(val, ctx=f"{ctx}.{key}")


def _expect_str(root: RawTomlTable, key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareOntologyTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: RawTomlTable, key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareOntologyTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: RawTomlTable, key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareOntologyTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: RawTomlTable, key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareOntologyTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_str_list(
    root: RawTomlTable,
    key: str,
    *,
    ctx: str,
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareOntologyTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for index, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareOntologyTomlError(
                f"Expected {ctx}.{key}[{index}] to be a string"
            )
        if not item.strip():
            raise AwareOntologyTomlError(
                f"Expected {ctx}.{key}[{index}] to be a non-empty string"
            )
        out.append(item)
    return out


def _normalize_policy(
    value: str | None,
    *,
    default: str,
    allowed: frozenset[str],
    ctx: str,
) -> str:
    normalized = str(value or default).strip().lower() or default
    if normalized not in allowed:
        raise AwareOntologyTomlError(
            f"{ctx} must be one of: {', '.join(sorted(allowed))}"
        )
    return normalized


def _normalized_optional_text(value: str | None) -> str | None:
    return value.strip() if value is not None and value.strip() else None


def _validate_package_name(value: str, *, ctx: str) -> None:
    if not _PACKAGE_NAME_RE.fullmatch(value):
        raise AwareOntologyTomlError(
            f"{ctx} must match {_PACKAGE_NAME_RE.pattern!r}; got {value!r}"
        )


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if not _FQN_PREFIX_RE.fullmatch(value):
        raise AwareOntologyTomlError(
            f"{ctx} must match {_FQN_PREFIX_RE.pattern!r}; got {value!r}"
        )


def _validate_provider_key(value: str, *, ctx: str) -> None:
    if not _PROVIDER_KEY_RE.fullmatch(value):
        raise AwareOntologyTomlError(
            f"{ctx} must match {_PROVIDER_KEY_RE.pattern!r}; got {value!r}"
        )


def _validate_semantic_role(value: str, *, ctx: str) -> None:
    if not _SEMANTIC_ROLE_RE.fullmatch(value):
        raise AwareOntologyTomlError(
            f"{ctx} must match {_SEMANTIC_ROLE_RE.pattern!r}; got {value!r}"
        )


def _validate_python_import(value: str, *, ctx: str) -> None:
    if not _PYTHON_IMPORT_RE.fullmatch(value):
        raise AwareOntologyTomlError(
            f"{ctx} must match {_PYTHON_IMPORT_RE.pattern!r}; got {value!r}"
        )


def _validate_sha256(value: str, *, ctx: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise AwareOntologyTomlError(
            f"{ctx} must be a lowercase 64-character SHA-256 hex digest"
        )


def _validate_rel_path(value: str, *, ctx: str) -> None:
    normalized = value.strip()
    if not normalized:
        raise AwareOntologyTomlError(f"{ctx} must be a non-empty path")
    path = Path(normalized)
    if path.is_absolute():
        raise AwareOntologyTomlError(f"{ctx} must be repo-relative: {value!r}")
    if ".." in path.parts:
        raise AwareOntologyTomlError(f"{ctx} must not contain '..': {value!r}")


__all__ = [
    "AwareOntologyTomlError",
    "load_aware_ontology_toml_spec",
    "load_aware_ontology_toml_spec_from_text",
]
