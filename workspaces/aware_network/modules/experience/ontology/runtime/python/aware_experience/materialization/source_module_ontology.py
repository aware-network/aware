from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys
import tomllib

from aware_code.semantic_materialization import (
    SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY,
)


@dataclass(frozen=True, slots=True)
class SourceModuleOntologyPackageRef:
    module_id: str
    package_name: str
    fqn_prefix: str
    manifest_path: Path
    dependency_package_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceModuleOntologyDtoStableIdsImportTargets:
    roots_by_module_id: Mapping[str, tuple[str, ...]]
    import_paths: tuple[Path, ...] = ()


def source_module_ontology_manifest_paths_for_manifest(
    manifest_path: Path,
) -> tuple[Path, ...]:
    module_toml_path = nearest_module_toml_path(manifest_path)
    if module_toml_path is None:
        return ()
    payload = _toml_payload(module_toml_path)
    raw_packages = payload.get("packages")
    if not isinstance(raw_packages, list):
        return ()
    module_root = module_toml_path.parent
    target_manifest = manifest_path.expanduser().resolve()
    target_declared = False
    ontology_manifest_paths: list[Path] = []
    for raw_package in raw_packages:
        if not isinstance(raw_package, Mapping):
            continue
        package_manifest = _module_package_manifest_path(
            module_root=module_root,
            raw_package=raw_package,
        )
        if package_manifest is None:
            continue
        if package_manifest == target_manifest:
            target_declared = True
        if str(raw_package.get("kind") or "").strip() == "ontology":
            ontology_manifest_paths.append(
                _ontology_source_manifest_path(package_manifest) or package_manifest
            )
    if not target_declared:
        return ()
    return tuple(dict.fromkeys(ontology_manifest_paths))


def source_module_ontology_package_names_for_manifest(
    manifest_path: Path,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            package_name
            for manifest in source_module_ontology_manifest_paths_for_manifest(
                manifest_path
            )
            for package_name in (_ontology_package_name_from_manifest(manifest),)
            if package_name
        )
    )


def source_module_ontology_package_ref_from_manifest(
    manifest_path: Path,
) -> SourceModuleOntologyPackageRef | None:
    package_name = _ontology_package_name_from_manifest(manifest_path)
    fqn_prefix = ontology_fqn_prefix_from_manifest(manifest_path)
    if package_name is None or fqn_prefix is None:
        return None
    module_toml_path = nearest_module_toml_path(manifest_path)
    module_id = (
        module_toml_path.parent.name
        if module_toml_path is not None
        else manifest_path.parent.name
    )
    return SourceModuleOntologyPackageRef(
        module_id=module_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path.expanduser().resolve(),
        dependency_package_names=ontology_dependency_package_names_from_manifest(
            manifest_path
        ),
    )


def source_module_ontology_dto_stable_ids_import_targets(
    *,
    context: Mapping[str, object] | None,
    source_experience_toml_path: Path | None,
) -> SourceModuleOntologyDtoStableIdsImportTargets:
    roots_by_module_id = {
        module_id: list(import_roots)
        for module_id, import_roots in (
            dto_stable_ids_import_roots_by_module_id_from_context(
                context=context,
            )
        ).items()
    }
    import_paths: list[Path] = []
    for target in source_module_ontology_dto_import_targets_for_manifest(
        source_experience_toml_path=source_experience_toml_path,
    ):
        module_roots = roots_by_module_id.setdefault(target.module_id, [])
        if target.import_root not in module_roots:
            module_roots.append(target.import_root)
        import_paths.append(target.import_path)
    return SourceModuleOntologyDtoStableIdsImportTargets(
        roots_by_module_id={
            module_id: tuple(dict.fromkeys(import_roots))
            for module_id, import_roots in roots_by_module_id.items()
        },
        import_paths=tuple(dict.fromkeys(path.resolve() for path in import_paths)),
    )


@dataclass(frozen=True, slots=True)
class SourceModuleOntologyDtoStableIdsImportTarget:
    module_id: str
    import_root: str
    import_path: Path


def source_module_ontology_dto_import_targets_for_manifest(
    *,
    source_experience_toml_path: Path | None,
) -> tuple[SourceModuleOntologyDtoStableIdsImportTarget, ...]:
    if source_experience_toml_path is None:
        return ()
    targets: list[SourceModuleOntologyDtoStableIdsImportTarget] = []
    for manifest_path in source_module_ontology_manifest_paths_for_manifest(
        source_experience_toml_path
    ):
        fqn_prefix = ontology_fqn_prefix_from_manifest(manifest_path)
        if fqn_prefix is None:
            continue
        import_root = f"{fqn_prefix}_ontology_dto"
        module_id = module_id_from_dto_stable_ids_import_root(
            import_root=import_root,
        )
        if module_id is None:
            continue
        targets.append(
            SourceModuleOntologyDtoStableIdsImportTarget(
                module_id=module_id,
                import_root=import_root,
                import_path=manifest_path.parent / "python" / "dto",
            )
        )
    return tuple(targets)


def dto_stable_ids_import_roots_by_module_id_from_context(
    *,
    context: Mapping[str, object] | None,
) -> dict[str, tuple[str, ...]]:
    if context is None:
        return {}
    raw_targets = context.get(SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY)
    if not isinstance(raw_targets, Sequence) or isinstance(raw_targets, (str, bytes)):
        return {}
    roots_by_module_id: dict[str, list[str]] = {}
    for raw_target in raw_targets:
        if not isinstance(raw_target, Mapping):
            continue
        if str(raw_target.get("target_language_plugin_id") or "").strip() != "python":
            continue
        if (
            str(raw_target.get("materialization_source") or "").strip()
            != "ontology_dto"
        ):
            continue
        stable_ids_import_root = str(
            raw_target.get("stable_ids_import_root") or ""
        ).strip()
        if not valid_import_root(stable_ids_import_root):
            continue
        module_id = module_id_from_dto_stable_ids_import_root(
            import_root=stable_ids_import_root,
        )
        if module_id is None:
            continue
        roots_by_module_id.setdefault(module_id, []).append(stable_ids_import_root)
    return {
        module_id: tuple(dict.fromkeys(import_roots))
        for module_id, import_roots in roots_by_module_id.items()
    }


@contextmanager
def temporary_python_import_paths(paths: Sequence[Path]) -> Iterator[None]:
    added_paths: list[str] = []
    for path in reversed(tuple(dict.fromkeys(path.resolve() for path in paths))):
        if not path.is_dir():
            continue
        path_text = str(path)
        if path_text in sys.path:
            continue
        sys.path.insert(0, path_text)
        added_paths.append(path_text)
    try:
        yield
    finally:
        for path_text in added_paths:
            try:
                sys.path.remove(path_text)
            except ValueError:
                continue


def nearest_module_toml_path(manifest_path: Path) -> Path | None:
    for candidate in (manifest_path.parent, *manifest_path.parents):
        module_toml_path = candidate / "aware.module.toml"
        if module_toml_path.is_file():
            return module_toml_path.resolve()
    return None


def ontology_fqn_prefix_from_manifest(manifest_path: Path) -> str | None:
    payload = _toml_payload(manifest_path)
    for section_name in ("ontology", "package"):
        section = payload.get(section_name)
        if not isinstance(section, Mapping):
            continue
        fqn_prefix = section.get("fqn_prefix")
        if isinstance(fqn_prefix, str) and fqn_prefix.strip():
            return fqn_prefix.strip()
    return None


def ontology_dependency_package_names_from_manifest(
    manifest_path: Path,
) -> tuple[str, ...]:
    raw_dependencies = _toml_payload(manifest_path).get("dependencies")
    if not isinstance(raw_dependencies, list):
        return ()
    package_names: list[str] = []
    for raw_dependency in raw_dependencies:
        if not isinstance(raw_dependency, Mapping):
            continue
        package_name = raw_dependency.get("package_name")
        if isinstance(package_name, str) and package_name.strip():
            package_names.append(package_name.strip())
    return tuple(dict.fromkeys(package_names))


def module_id_from_dto_stable_ids_import_root(*, import_root: str) -> str | None:
    token = import_root.strip()
    if not token.startswith("aware_") or not token.endswith("_ontology_dto"):
        return None
    module_id = token.removeprefix("aware_").removesuffix("_ontology_dto").strip()
    if not module_id or not all(ch.isalnum() or ch == "_" for ch in module_id):
        return None
    return module_id


def valid_import_root(value: str) -> bool:
    parts = value.strip().split(".")
    return bool(parts) and all(part.isidentifier() for part in parts)


def _ontology_package_name_from_manifest(manifest_path: Path) -> str | None:
    payload = _toml_payload(manifest_path)
    for section_name in ("ontology", "package"):
        section = payload.get(section_name)
        if not isinstance(section, Mapping):
            continue
        package_name = section.get("package_name")
        if isinstance(package_name, str) and package_name.strip():
            return package_name.strip()
    return None


def _ontology_source_manifest_path(manifest_path: Path) -> Path | None:
    if manifest_path.name != "aware.ontology.toml":
        return None
    section = _toml_payload(manifest_path).get("ontology")
    if not isinstance(section, Mapping):
        return None
    raw_source_manifest = section.get("source_manifest")
    if not isinstance(raw_source_manifest, str) or not raw_source_manifest.strip():
        return None
    source_manifest_path = Path(raw_source_manifest.strip()).expanduser()
    if not source_manifest_path.is_absolute():
        source_manifest_path = manifest_path.parent / source_manifest_path
    return source_manifest_path.resolve()


def _module_package_manifest_path(
    *,
    module_root: Path,
    raw_package: Mapping[str, object],
) -> Path | None:
    raw_manifest = raw_package.get("manifest")
    if not isinstance(raw_manifest, str) or not raw_manifest.strip():
        return None
    manifest_path = Path(raw_manifest.strip()).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = module_root / manifest_path
    return manifest_path.resolve()


def _toml_payload(path: Path) -> Mapping[str, object]:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8") or "")
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


__all__ = [
    "SourceModuleOntologyDtoStableIdsImportTarget",
    "SourceModuleOntologyDtoStableIdsImportTargets",
    "SourceModuleOntologyPackageRef",
    "dto_stable_ids_import_roots_by_module_id_from_context",
    "module_id_from_dto_stable_ids_import_root",
    "nearest_module_toml_path",
    "ontology_dependency_package_names_from_manifest",
    "ontology_fqn_prefix_from_manifest",
    "source_module_ontology_dto_import_targets_for_manifest",
    "source_module_ontology_dto_stable_ids_import_targets",
    "source_module_ontology_manifest_paths_for_manifest",
    "source_module_ontology_package_names_for_manifest",
    "source_module_ontology_package_ref_from_manifest",
    "temporary_python_import_paths",
    "valid_import_root",
]
