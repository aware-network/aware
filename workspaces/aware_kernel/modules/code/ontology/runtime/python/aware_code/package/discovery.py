"""Code package discovery system for manifest-backed packages."""

from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from aware_code.language.schemas import CodeDiscoveryFile
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package.registry import SemanticPackageRegistry

from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class CodePackagePathResolution:
    """Structured package-resolution truth for one focused workspace path."""

    document_path: Path
    nearest_package_root: Path | None = None
    nearest_manifest_path: Path | None = None
    nearest_manifest_declared_in_workspace: bool | None = None
    owning_package_root: Path | None = None
    owning_manifest_path: Path | None = None
    authoritative_workspace_root: Path | None = None
    authoritative_workspace_manifest_path: Path | None = None
    workspace_membership_required: bool = False


class CodePackageDiscovery(ABC):
    """Base implementation of code package discovery."""

    @abstractmethod
    def is_package_root(self, path: Path, workspace_root: Path) -> bool:
        """Check if a directory is a package root."""
        pass

    @abstractmethod
    def get_package_name(self, package_path: Path, workspace_root: Path) -> str:
        """Get the canonical package name from a root directory."""
        pass

    @abstractmethod
    def get_manifest_path(self, package_path: Path, workspace_root: Path) -> Path:
        """Get the package manifest path relative to the workspace root."""
        pass

    def get_metadata(
        self, package_path: Path, workspace_root: Path
    ) -> dict[str, object]:
        """Default implementation returns empty dict. Override in subclasses."""
        _ = (package_path, workspace_root)
        return {}

    def resolve_package_root_for_path(
        self,
        *,
        path: Path,
        workspace_root: Path,
    ) -> Path | None:
        return self.resolve_package_for_path(
            path=path,
            workspace_root=workspace_root,
        ).owning_package_root

    def resolve_package_for_path(
        self,
        *,
        path: Path,
        workspace_root: Path,
    ) -> CodePackagePathResolution:
        """Resolve the nearest package root that owns `path`.

        Languages with stronger ownership boundaries can override this to stop
        at workspace or package scope edges before climbing to repository
        parents, and to expose extra provenance such as authoritative workspace
        membership requirements.
        """
        resolved_workspace_root = workspace_root.resolve()
        resolved_path = (
            path.resolve()
            if path.is_absolute()
            else (resolved_workspace_root / path).resolve()
        )
        document_path = self._relative_to_workspace_root_or_absolute(
            path=resolved_path,
            workspace_root=resolved_workspace_root,
        )
        candidate_root = (
            resolved_path if resolved_path.is_dir() else resolved_path.parent
        )

        for candidate in [candidate_root, *candidate_root.parents]:
            try:
                rel_candidate = candidate.relative_to(resolved_workspace_root)
            except Exception:
                if candidate == resolved_workspace_root:
                    rel_candidate = Path(".")
                else:
                    continue

            try:
                if self.is_package_root(rel_candidate, resolved_workspace_root):
                    manifest_path = self.get_manifest_path(
                        rel_candidate, resolved_workspace_root
                    )
                    return CodePackagePathResolution(
                        document_path=document_path,
                        nearest_package_root=rel_candidate,
                        nearest_manifest_path=manifest_path,
                        owning_package_root=rel_candidate,
                        owning_manifest_path=manifest_path,
                    )
            except Exception as exc:
                logger.debug(
                    "Skipping invalid package root candidate %s: %s",
                    candidate,
                    exc,
                )
                continue

        return CodePackagePathResolution(document_path=document_path)

    def _relative_to_workspace_root_or_absolute(
        self,
        *,
        path: Path,
        workspace_root: Path,
    ) -> Path:
        try:
            return path.resolve().relative_to(workspace_root.resolve())
        except Exception:
            return path.resolve()


def discover_packages(
    *, workspace_root: Path, files: Iterable[CodeDiscoveryFile]
) -> list[CodePackageInfo]:
    """Discover code packages from a neutral repository file snapshot."""
    from aware_code.language.registry import CodeLanguagePluginRegistry

    SemanticPackageRegistry.ensure_builtin_providers_registered()
    full_file_tree = {
        file_info.relative_path: file_info.file_content for file_info in files
    }
    discovered_languages = CodeLanguagePluginRegistry.get_supported_languages()
    candidate_directories = _candidate_directories_from_file_tree(full_file_tree)

    return _discover_packages_from_candidate_directories(
        workspace_root=workspace_root,
        candidate_directories=candidate_directories,
        discovered_languages=discovered_languages,
    )


def discover_packages_from_manifest_paths(
    *,
    workspace_root: Path,
    manifest_paths: Iterable[str | Path],
) -> list[CodePackageInfo]:
    """Discover code packages from explicit manifest paths only.

    Explicit authored manifests are semantic-contract package entrypoints. They
    resolve through Code's semantic contract registry rather than through the
    language grammar plugins.
    """
    from aware_code.package.semantic_contract_discovery import (
        SemanticContractCodePackageDiscovery,
    )

    SemanticPackageRegistry.ensure_builtin_providers_registered()
    package_discovery = SemanticContractCodePackageDiscovery(
        require_workspace_membership=False,
    )
    discovered_packages: list[CodePackageInfo] = []
    for manifest_path in manifest_paths:
        manifest_path_obj = Path(str(manifest_path))
        package_root = manifest_path_obj.parent
        try:
            if not package_discovery.is_package_root(package_root, workspace_root):
                continue
            package_name = package_discovery.get_package_name(
                package_root,
                workspace_root,
            )
            resolved_manifest_path = package_discovery.get_manifest_path(
                package_root,
                workspace_root,
            )
            metadata = package_discovery.get_metadata(package_root, workspace_root)
            language = package_discovery.get_language(package_root, workspace_root)
        except Exception as exc:
            logger.warning(
                f"Failed to process potential semantic package at {package_root}: {exc}"
            )
            continue
        package = CodePackageInfo(
            name=package_name,
            root_path=package_root,
            manifest_path=resolved_manifest_path,
            language=language,
            metadata=metadata,
        )
        discovered_packages.append(SemanticPackageRegistry.enrich_code_package(package))

    discovered_packages = _dedupe_discovered_packages_by_manifest_path(
        discovered_packages
    )
    discovered_packages.sort(
        key=lambda package: (
            str(package.root_path),
            package.name,
            package.language.value,
        )
    )
    logger.info("✅ Discovered %s packages", len(discovered_packages))
    return discovered_packages


def _discover_packages_from_candidate_directories(
    *,
    workspace_root: Path,
    candidate_directories: Iterable[Path],
    discovered_languages: list[Any],
) -> list[CodePackageInfo]:
    from aware_code.language.registry import CodeLanguagePluginRegistry

    discovered_packages: list[CodePackageInfo] = []

    for language in discovered_languages:
        try:
            plugin = CodeLanguagePluginRegistry.get(language)
            if not plugin.package_discovery:
                continue

            packages: list[CodePackageInfo] = []
            for directory_path in candidate_directories:
                try:
                    if not plugin.package_discovery.is_package_root(
                        directory_path, workspace_root
                    ):
                        continue
                    package_name = plugin.package_discovery.get_package_name(
                        directory_path, workspace_root
                    )
                    manifest_path = plugin.package_discovery.get_manifest_path(
                        directory_path, workspace_root
                    )
                    metadata = plugin.package_discovery.get_metadata(
                        directory_path, workspace_root
                    )
                except Exception as exc:
                    logger.warning(
                        f"Failed to process potential package at {directory_path}: {exc}"
                    )
                    continue
                package = CodePackageInfo(
                    name=package_name,
                    root_path=directory_path,
                    manifest_path=manifest_path,
                    language=language,
                    metadata=metadata,
                )
                package = SemanticPackageRegistry.enrich_code_package(package)
                packages.append(package)
                logger.debug(
                    "Discovered %s package: %s at %s",
                    package.language.value,
                    package.name,
                    package.root_path,
                )

            discovered_packages.extend(packages)
        except Exception as exc:
            logger.warning(f"Failed to discover packages for {language.value}: {exc}")
            continue

    discovered_packages = _dedupe_discovered_packages_by_manifest_path(
        discovered_packages
    )
    discovered_packages.sort(
        key=lambda package: (
            str(package.root_path),
            package.name,
            package.language.value,
        )
    )
    logger.info(
        "✅ Discovered %s packages across %s languages",
        len(discovered_packages),
        len(discovered_languages),
    )
    return discovered_packages


def _dedupe_discovered_packages_by_manifest_path(
    packages: Iterable[CodePackageInfo],
) -> list[CodePackageInfo]:
    packages_by_manifest_path: dict[str, CodePackageInfo] = {}
    manifest_path_order: list[str] = []
    for package in packages:
        manifest_path = package.manifest_path.as_posix()
        current = packages_by_manifest_path.get(manifest_path)
        if current is None:
            packages_by_manifest_path[manifest_path] = package
            manifest_path_order.append(manifest_path)
            continue
        if _package_discovery_metadata_score(package) > (
            _package_discovery_metadata_score(current)
        ):
            packages_by_manifest_path[manifest_path] = package
    return [
        packages_by_manifest_path[manifest_path]
        for manifest_path in manifest_path_order
        if manifest_path in packages_by_manifest_path
    ]


def _package_discovery_metadata_score(package: CodePackageInfo) -> int:
    metadata = package.metadata or {}
    score = 0
    if _metadata_text(metadata, "manifest_kind") is not None:
        score += 10
    if _metadata_text(metadata, "source_root") is not None:
        score += 5
    if _metadata_text(metadata, "sources_root") is not None:
        score += 5
    if _metadata_text(metadata, "package_manager_name_key") is not None:
        score += 50
    if _metadata_text_tuple(metadata, "package_dependency_keys"):
        score += 25
    score += len(metadata)
    return score


def _metadata_text(metadata: Mapping[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _metadata_text_tuple(metadata: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = metadata.get(key)
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _candidate_directories_from_file_tree(
    file_tree: dict[str, str],
) -> list[Path]:
    if not file_tree:
        return []

    directories: set[Path] = {Path(".")}
    for file_path in file_tree.keys():
        path_obj = Path(file_path)
        directories.add(path_obj.parent)
        directories.update(path_obj.parents)

    return sorted(directories, key=lambda p: len(p.parts))
