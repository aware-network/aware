"""CodePackage test inventory read-model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.language.test_discovery import (
    CodeTestDiscoveryCode,
    CodeTestDiscoveryContext,
    CodeTestDiscoveryResult,
    CodeTestDiscoverySection,
    CodeTestFrameworkDiscoveryDescriptor,
)
from aware_code.package.code_access import normalize_package_relative_path
from aware_code.package.schemas import CodePackageInfo
from aware_code.parse.sections import collect_top_level_section_identity_descriptors
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_id,
    stable_code_package_code_id,
    stable_code_package_config_id,
    stable_code_package_id,
    stable_code_package_test_framework_id,
    stable_code_package_test_id,
    stable_code_section_id,
    stable_code_test_framework_id,
    stable_code_test_id,
    stable_code_test_unit_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_utils.logging import logger


_IGNORED_PACKAGE_SCAN_PARTS: frozenset[str] = frozenset(
    {
        ".dart_tool",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "node_modules",
    }
)


@dataclass(frozen=True, slots=True)
class CodePackageTestFrameworkInventory:
    """One framework declared or inferred for a package."""

    code_test_framework_id: UUID
    code_package_test_framework_id: UUID
    name: str
    title: str | None
    declaration_kind: str
    declaration_ref: str | None


@dataclass(frozen=True, slots=True)
class CodePackageTestUnitInventory:
    """One runnable unit resolved through CodePackage -> Code -> CodeSection."""

    code_package_code_id: UUID
    code_id: UUID
    code_section_id: UUID
    code_test_framework_id: UUID
    code_test_id: UUID
    code_package_test_id: UUID
    code_test_unit_id: UUID
    framework_name: str
    relative_path: str
    unit_key: str
    selector: str
    kind: str
    name: str | None


@dataclass(frozen=True, slots=True)
class CodePackageTestInventory:
    """Deterministic test inventory for one CodePackage."""

    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    sources_root: str | None
    frameworks: tuple[CodePackageTestFrameworkInventory, ...] = ()
    units: tuple[CodePackageTestUnitInventory, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.frameworks and not self.units


@dataclass(frozen=True, slots=True)
class _CodeIdentity:
    code_package_code_id: UUID
    code_id: UUID


def build_code_package_test_inventory_from_files(
    *,
    code_package_id: UUID | None = None,
    package_name: str,
    language: CodeLanguage,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    manifest_text: str | None,
    files: Mapping[str, str],
) -> CodePackageTestInventory:
    """Build a canonical package test inventory from package-relative file text."""

    setup_code_plugins()
    resolved_code_package_id = code_package_id or stable_code_package_id(
        code_package_config_id=stable_code_package_config_id(
            config_key=code_package_source_config_key(
                manifest_kind=manifest_kind,
                surface="runtime",
            ),
        ),
        package_name=package_name,
        language=language,
    )
    normalized_manifest_relative_path = _normalize_optional_path(
        manifest_relative_path,
        fallback=_manifest_name_for_kind(manifest_kind),
    )
    normalized_package_root = _normalize_optional_path(package_root, fallback=".")
    normalized_sources_root = _normalize_nullable_path(sources_root)

    try:
        plugin = CodeLanguagePluginRegistry.get(language)
    except KeyError:
        return CodePackageTestInventory(
            code_package_id=resolved_code_package_id,
            package_name=package_name,
            language=language,
            manifest_kind=manifest_kind,
            manifest_relative_path=normalized_manifest_relative_path,
            package_root=normalized_package_root,
            sources_root=normalized_sources_root,
        )

    if plugin.test_discovery is None:
        return CodePackageTestInventory(
            code_package_id=resolved_code_package_id,
            package_name=package_name,
            language=language,
            manifest_kind=manifest_kind,
            manifest_relative_path=normalized_manifest_relative_path,
            package_root=normalized_package_root,
            sources_root=normalized_sources_root,
        )

    code_identity_by_relative_path: dict[str, _CodeIdentity] = {}
    discovery_codes: list[CodeTestDiscoveryCode] = []
    for relative_path, content_text in sorted(
        _normalize_file_mapping(files).items(),
        key=lambda item: item[0],
    ):
        if not _has_plugin_extension(
            relative_path=relative_path, extensions=plugin.extensions
        ):
            continue
        package_code_id = stable_code_package_code_id(
            code_package_id=resolved_code_package_id,
            relative_path=relative_path,
        )
        code_id = stable_code_id(
            code_package_code_id=package_code_id,
            relative_path=relative_path,
        )
        code_identity_by_relative_path[relative_path] = _CodeIdentity(
            code_package_code_id=package_code_id,
            code_id=code_id,
        )
        sections = _discover_sections(
            code_id=code_id,
            relative_path=relative_path,
            content_text=content_text,
            language=language,
        )
        discovery_codes.append(
            CodeTestDiscoveryCode(
                relative_path=relative_path,
                content_text=content_text,
                sections=sections,
            )
        )

    discovery_result = plugin.discover_tests(
        CodeTestDiscoveryContext(
            package_name=package_name,
            language=language,
            manifest_kind=manifest_kind,
            manifest_relative_path=normalized_manifest_relative_path,
            package_root=normalized_package_root,
            sources_root=normalized_sources_root,
            manifest_text=manifest_text,
            codes=tuple(discovery_codes),
        )
    )
    return _inventory_from_discovery_result(
        code_package_id=resolved_code_package_id,
        package_name=package_name,
        language=language,
        manifest_kind=manifest_kind,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
        code_identity_by_relative_path=code_identity_by_relative_path,
        discovery_result=discovery_result,
    )


def build_code_package_test_inventory_for_package_info(
    *,
    code_package: CodePackageInfo,
    workspace_root: Path,
    max_files: int = 1000,
) -> CodePackageTestInventory:
    """Build test inventory for a discovered CodePackageInfo from the filesystem."""

    setup_code_plugins()
    package_root_abs = _resolve_workspace_path(
        workspace_root=workspace_root,
        path=code_package.root_path,
    )
    manifest_abs = _resolve_workspace_path(
        workspace_root=workspace_root,
        path=code_package.manifest_path,
    )
    manifest_kind = infer_code_package_manifest_kind(code_package.manifest_path)
    manifest_relative_path = _manifest_path_relative_to_package(
        package_root_abs=package_root_abs,
        manifest_abs=manifest_abs,
        fallback=code_package.manifest_path.as_posix(),
    )
    manifest_text = _read_text_if_exists(manifest_abs)
    sources_root = _metadata_string(
        code_package.metadata,
        "sources_root",
        "sourcesRoot",
    )

    files: dict[str, str] = {}
    try:
        plugin = CodeLanguagePluginRegistry.get(code_package.language)
    except KeyError:
        plugin = None

    if (
        plugin is not None
        and plugin.test_discovery is not None
        and package_root_abs.is_dir()
    ):
        for relative_path, content_text in _iter_package_language_files(
            package_root_abs=package_root_abs,
            extensions=tuple(plugin.extensions),
            max_files=max_files,
        ):
            files[relative_path] = content_text

    return build_code_package_test_inventory_from_files(
        package_name=code_package.name,
        language=code_package.language,
        manifest_kind=manifest_kind,
        manifest_relative_path=manifest_relative_path,
        package_root=code_package.root_path.as_posix(),
        sources_root=sources_root,
        manifest_text=manifest_text,
        files=files,
    )


def infer_code_package_manifest_kind(manifest_path: Path) -> str:
    """Infer the ontology manifest kind from a manifest path."""

    name = manifest_path.name.casefold()
    if name == "pyproject.toml":
        return "pyproject_toml"
    if name == "setup.py":
        return "setup_py"
    if name == "pubspec.yaml":
        return "pubspec_yaml"
    if name == "aware.environment.toml":
        return "aware_environment_toml"
    if name == "aware.ontology.toml":
        return "aware_ontology_toml"
    if name == "aware.api.toml":
        return "aware_api_toml"
    if name == "aware.economy.toml":
        return "aware_economy_toml"
    if name == "aware.service.toml":
        return "aware_service_toml"
    if name == "aware.attention.toml":
        return "aware_attention_toml"
    if name == "aware.pane.toml":
        return "aware_pane_toml"
    if name == "aware.interface.toml":
        return "aware_interface_toml"
    if name == "aware.experience.toml":
        return "aware_experience_toml"
    if name == "aware.node.toml":
        return "aware_node_toml"
    if name == "aware.inference.toml":
        return "aware_inference_toml"
    return "aware_toml"


def _inventory_from_discovery_result(
    *,
    code_package_id: UUID,
    package_name: str,
    language: CodeLanguage,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    code_identity_by_relative_path: Mapping[str, _CodeIdentity],
    discovery_result: CodeTestDiscoveryResult,
) -> CodePackageTestInventory:
    framework_descriptors = _framework_descriptors_by_name(discovery_result)
    frameworks_by_name: dict[str, CodePackageTestFrameworkInventory] = {}
    for framework_name, descriptor in sorted(framework_descriptors.items()):
        framework_id = stable_code_test_framework_id(name=framework_name)
        frameworks_by_name[framework_name] = CodePackageTestFrameworkInventory(
            code_test_framework_id=framework_id,
            code_package_test_framework_id=stable_code_package_test_framework_id(
                code_package_id=code_package_id,
                code_test_framework_id=framework_id,
            ),
            name=framework_name,
            title=descriptor.title,
            declaration_kind=descriptor.declaration_kind,
            declaration_ref=descriptor.declaration_ref,
        )

    units: list[CodePackageTestUnitInventory] = []
    for unit in sorted(
        discovery_result.units,
        key=lambda item: (
            normalize_package_relative_path(item.relative_path),
            item.framework_name,
            item.selector,
            item.unit_key,
        ),
    ):
        relative_path = normalize_package_relative_path(unit.relative_path)
        code_identity = code_identity_by_relative_path.get(relative_path)
        if code_identity is None:
            logger.warning(
                "Skipping discovered test unit for unknown CodePackage file: %s",
                relative_path,
            )
            continue

        framework_name = (unit.framework_name or "").strip()
        framework = frameworks_by_name.get(framework_name)
        if framework is None:
            framework_id = stable_code_test_framework_id(name=framework_name)
            framework = CodePackageTestFrameworkInventory(
                code_test_framework_id=framework_id,
                code_package_test_framework_id=stable_code_package_test_framework_id(
                    code_package_id=code_package_id,
                    code_test_framework_id=framework_id,
                ),
                name=framework_name,
                title=framework_name,
                declaration_kind="unit_reference",
                declaration_ref=relative_path,
            )
            frameworks_by_name[framework_name] = framework

        code_test_id = stable_code_test_id(
            code_id=code_identity.code_id,
            framework_id=framework.code_test_framework_id,
        )
        units.append(
            CodePackageTestUnitInventory(
                code_package_code_id=code_identity.code_package_code_id,
                code_id=code_identity.code_id,
                code_section_id=unit.code_section_id,
                code_test_framework_id=framework.code_test_framework_id,
                code_test_id=code_test_id,
                code_package_test_id=stable_code_package_test_id(
                    code_package_id=code_package_id,
                    code_test_id=code_test_id,
                    relative_path=relative_path,
                ),
                code_test_unit_id=stable_code_test_unit_id(
                    code_test_id=code_test_id,
                    code_section_id=unit.code_section_id,
                    unit_key=unit.unit_key,
                ),
                framework_name=framework_name,
                relative_path=relative_path,
                unit_key=unit.unit_key,
                selector=unit.selector,
                kind=unit.kind,
                name=unit.name,
            )
        )

    return CodePackageTestInventory(
        code_package_id=code_package_id,
        package_name=package_name,
        language=language,
        manifest_kind=manifest_kind,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        frameworks=tuple(
            sorted(
                frameworks_by_name.values(),
                key=lambda item: item.name,
            )
        ),
        units=tuple(units),
    )


def _framework_descriptors_by_name(
    discovery_result: CodeTestDiscoveryResult,
) -> dict[str, CodeTestFrameworkDiscoveryDescriptor]:
    frameworks: dict[str, CodeTestFrameworkDiscoveryDescriptor] = {}
    for descriptor in discovery_result.frameworks:
        name = (descriptor.name or "").strip()
        if not name:
            continue
        _ = frameworks.setdefault(name, descriptor)

    for unit in discovery_result.units:
        name = (unit.framework_name or "").strip()
        if not name:
            continue
        _ = frameworks.setdefault(
            name,
            CodeTestFrameworkDiscoveryDescriptor(
                name=name,
                title=name,
                declaration_kind="unit_reference",
                declaration_ref=normalize_package_relative_path(unit.relative_path),
            ),
        )
    return frameworks


def _discover_sections(
    *,
    code_id: UUID,
    relative_path: str,
    content_text: str,
    language: CodeLanguage,
) -> tuple[CodeTestDiscoverySection, ...]:
    try:
        descriptors = collect_top_level_section_identity_descriptors(
            content=content_text,
            language=language,
        )
    except Exception as exc:
        logger.warning(
            "Skipping test section discovery for %s: %s",
            relative_path,
            exc,
        )
        return ()

    return tuple(
        CodeTestDiscoverySection(
            code_section_id=stable_code_section_id(
                code_id=code_id,
                section_key=descriptor.section_key,
                type=descriptor.section_type.value,
            ),
            section_key=descriptor.section_key,
            qualname=descriptor.qualname,
            section_type=descriptor.section_type,
        )
        for descriptor in descriptors
    )


def _iter_package_language_files(
    *,
    package_root_abs: Path,
    extensions: tuple[str, ...],
    max_files: int,
) -> tuple[tuple[str, str], ...]:
    if max_files <= 0:
        return ()

    files: list[tuple[str, str]] = []
    for path in sorted(package_root_abs.rglob("*"), key=lambda item: item.as_posix()):
        if len(files) >= max_files:
            break
        if not path.is_file():
            continue
        try:
            relative_path = path.relative_to(package_root_abs).as_posix()
        except ValueError:
            continue
        if any(
            part in _IGNORED_PACKAGE_SCAN_PARTS
            for part in Path(relative_path).parts[:-1]
        ):
            continue
        if not _has_plugin_extension(
            relative_path=relative_path, extensions=extensions
        ):
            continue
        text = _read_text_if_exists(path)
        if text is None:
            continue
        files.append((relative_path, text))
    return tuple(files)


def _normalize_file_mapping(files: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for relative_path, content_text in files.items():
        normalized[
            normalize_package_relative_path(relative_path).replace("\\", "/")
        ] = content_text
    return normalized


def _has_plugin_extension(
    *, relative_path: str, extensions: tuple[str, ...] | list[str]
) -> bool:
    path = Path(relative_path)
    return path.suffix in extensions


def _resolve_workspace_path(*, workspace_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (workspace_root / path).resolve()


def _manifest_path_relative_to_package(
    *,
    package_root_abs: Path,
    manifest_abs: Path,
    fallback: str,
) -> str:
    try:
        return manifest_abs.relative_to(package_root_abs).as_posix()
    except ValueError:
        return fallback


def _read_text_if_exists(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _metadata_string(metadata: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, Path):
            return value.as_posix()
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_optional_path(value: str, *, fallback: str) -> str:
    normalized = value.strip().replace("\\", "/")
    return normalized or fallback


def _normalize_nullable_path(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().replace("\\", "/")
    return normalized or None


def _manifest_name_for_kind(manifest_kind: str) -> str:
    return {
        "pyproject_toml": "pyproject.toml",
        "setup_py": "setup.py",
        "pubspec_yaml": "pubspec.yaml",
        "aware_environment_toml": "aware.environment.toml",
        "aware_ontology_toml": "aware.ontology.toml",
        "aware_api_toml": "aware.api.toml",
        "aware_economy_toml": "aware.economy.toml",
        "aware_service_toml": "aware.service.toml",
        "aware_attention_toml": "aware.attention.toml",
        "aware_pane_toml": "aware.pane.toml",
        "aware_interface_toml": "aware.interface.toml",
        "aware_experience_toml": "aware.experience.toml",
        "aware_node_toml": "aware.node.toml",
        "aware_inference_toml": "aware.inference.toml",
    }.get(manifest_kind, "aware.toml")


__all__ = [
    "CodePackageTestFrameworkInventory",
    "CodePackageTestInventory",
    "CodePackageTestUnitInventory",
    "build_code_package_test_inventory_for_package_info",
    "build_code_package_test_inventory_from_files",
    "infer_code_package_manifest_kind",
]
