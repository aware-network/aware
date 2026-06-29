"""Semantic-contract-backed package discovery.

Authored semantic package manifests are Code package truth, not Aware grammar
truth. This resolver derives supported manifest filenames, loaders, package
metadata, and package surfaces from registered ModuleSemanticContract entries.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from typing_extensions import override

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
)
from aware_code.package.discovery import (
    CodePackageDiscovery,
    CodePackagePathResolution,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_utils.logging import logger
from aware_workspace.registry import (
    AwareWorkspaceRegistrySource,
    ResolvedAwareWorkspaceRegistry,
    load_aware_workspace_registry,
)


_AWARE_SOURCE_EXTENSION = ".aware"
_IGNORED_SEGMENTS = frozenset(
    {".aware", ".git", "__pycache__", "node_modules", ".venv", "venv"}
)


@dataclass(frozen=True, slots=True)
class _ResolvedSemanticContractPackage:
    manifest_kind: str
    manifest_path_key: str
    package_name: str
    manifest_path: str
    package_root: str
    package_kind: str | None
    fqn_prefix: str | None
    source_root: str
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    owned_file_paths: tuple[str, ...]
    language: CodeLanguage
    extra_metadata: dict[str, object]

    def to_metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {
            "manifest_kind": self.manifest_kind,
            "authored_manifest_kind": self.manifest_kind,
            "package_root": self.package_root,
            "source_root": self.source_root,
            "include_paths": list(self.include_paths),
            "exclude_paths": list(self.exclude_paths),
            "owned_file_paths": list(self.owned_file_paths),
            "language": self.language.value,
        }
        metadata[self.manifest_path_key] = self.manifest_path
        if self.package_kind is not None:
            metadata["package_kind"] = self.package_kind
        if self.fqn_prefix is not None:
            metadata["fqn_prefix"] = self.fqn_prefix
        metadata.update(self.extra_metadata)
        return metadata


class SemanticContractCodePackageDiscovery(CodePackageDiscovery):
    """Resolve package manifests from registered semantic contracts."""

    def __init__(self, *, require_workspace_membership: bool = True) -> None:
        self._require_workspace_membership = require_workspace_membership
        self._cache: dict[tuple[str, str], _ResolvedSemanticContractPackage] = {}
        self._workspace_registry_by_root: dict[
            Path, ResolvedAwareWorkspaceRegistry | None
        ] = {}

    def clear_cache(self) -> None:
        self._cache.clear()
        self._workspace_registry_by_root.clear()

    @override
    def resolve_package_for_path(
        self,
        *,
        path: Path,
        workspace_root: Path,
    ) -> CodePackagePathResolution:
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
        declared_workspace_root = self._resolve_nearest_declared_workspace_root(
            start=resolved_path
        )
        authoritative_workspace_root = (
            self._relative_to_workspace_root_or_absolute(
                path=declared_workspace_root,
                workspace_root=resolved_workspace_root,
            )
            if declared_workspace_root is not None
            else None
        )
        authoritative_workspace_manifest_path = (
            self._relative_to_workspace_root_or_absolute(
                path=(declared_workspace_root / "aware.workspace.toml").resolve(),
                workspace_root=resolved_workspace_root,
            )
            if declared_workspace_root is not None
            else None
        )
        registry = (
            self._load_workspace_registry_for_root(
                workspace_root=declared_workspace_root
            )
            if declared_workspace_root is not None
            else None
        )
        nearest_package_root: Path | None = None
        nearest_manifest_path: Path | None = None
        nearest_manifest_declared_in_workspace: bool | None = None
        owning_package_root: Path | None = None
        owning_manifest_path: Path | None = None

        for candidate in [candidate_root, *candidate_root.parents]:
            if (
                declared_workspace_root is not None
                and candidate != declared_workspace_root
                and declared_workspace_root not in candidate.parents
            ):
                break
            try:
                rel_candidate = candidate.relative_to(resolved_workspace_root)
            except Exception:
                if candidate == resolved_workspace_root:
                    rel_candidate = Path(".")
                else:
                    continue

            try:
                package_root = (resolved_workspace_root / rel_candidate).resolve()
                _contract, descriptor, manifest_path, _manifest_spec = (
                    self._resolve_manifest_descriptor(package_root=package_root)
                )
            except Exception as exc:
                logger.debug(
                    "Skipping invalid semantic package root candidate %s: %s",
                    candidate,
                    exc,
                )
                continue

            rel_manifest_path = Path(
                self._relative_to_workspace(
                    path=manifest_path,
                    workspace_root=resolved_workspace_root,
                )
            )
            manifest_declared_in_workspace = (
                self._manifest_is_declared_in_workspace_registry(
                    manifest_path=manifest_path,
                    registry=registry,
                )
            )
            if nearest_package_root is None:
                nearest_package_root = rel_candidate
                nearest_manifest_path = rel_manifest_path
                nearest_manifest_declared_in_workspace = (
                    manifest_declared_in_workspace
                    if declared_workspace_root is not None
                    else None
                )
            if (
                declared_workspace_root is not None
                and not manifest_declared_in_workspace
            ):
                continue
            owning_package_root = rel_candidate
            owning_manifest_path = rel_manifest_path
            break

        return CodePackagePathResolution(
            document_path=document_path,
            nearest_package_root=nearest_package_root,
            nearest_manifest_path=nearest_manifest_path,
            nearest_manifest_declared_in_workspace=nearest_manifest_declared_in_workspace,
            owning_package_root=owning_package_root,
            owning_manifest_path=owning_manifest_path,
            authoritative_workspace_root=authoritative_workspace_root,
            authoritative_workspace_manifest_path=authoritative_workspace_manifest_path,
            workspace_membership_required=declared_workspace_root is not None,
        )

    @override
    def is_package_root(self, path: Path, workspace_root: Path) -> bool:
        try:
            _ = self._resolve_package(path=path, workspace_root=workspace_root)
        except (FileNotFoundError, ValueError) as exc:
            logger.debug("Skipping invalid semantic package root %s: %s", path, exc)
            return False
        return True

    @override
    def get_package_name(self, package_path: Path, workspace_root: Path) -> str:
        return self._resolve_package(
            path=package_path,
            workspace_root=workspace_root,
        ).package_name

    @override
    def get_manifest_path(self, package_path: Path, workspace_root: Path) -> Path:
        resolved = self._resolve_package(
            path=package_path, workspace_root=workspace_root
        )
        return Path(resolved.manifest_path)

    @override
    def get_metadata(
        self, package_path: Path, workspace_root: Path
    ) -> dict[str, object]:
        return self._resolve_package(
            path=package_path,
            workspace_root=workspace_root,
        ).to_metadata()

    def get_language(self, package_path: Path, workspace_root: Path) -> CodeLanguage:
        return self._resolve_package(
            path=package_path,
            workspace_root=workspace_root,
        ).language

    def manifest_filenames(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    descriptor.filename
                    for _contract, descriptor in self._manifest_resolution_entries()
                }
            )
        )

    def _resolve_package(
        self,
        *,
        path: Path,
        workspace_root: Path,
    ) -> _ResolvedSemanticContractPackage:
        workspace_root = workspace_root.resolve()
        package_path = path
        cache_key = (workspace_root.as_posix(), package_path.as_posix())
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        package_root = (workspace_root / package_path).resolve()
        if not package_root.is_dir():
            raise ValueError(f"Package root is not a directory: {package_root}")

        contract, descriptor, manifest_path, manifest_spec = (
            self._resolve_manifest_descriptor(package_root=package_root)
        )
        _ = contract
        self._ensure_manifest_is_workspace_declared(manifest_path=manifest_path)
        source_root = (
            package_root / _manifest_build_sources_dir(manifest_spec)
        ).resolve()
        include_paths = _manifest_build_path_tuple(
            manifest_spec,
            attribute_name="include_paths",
        )
        exclude_paths = _manifest_build_path_tuple(
            manifest_spec,
            attribute_name="exclude_paths",
        )
        owned_file_paths = self._scan_source_files(
            workspace_root=workspace_root,
            sources_root=source_root,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
        )

        package_section = _manifest_package_section(
            manifest_spec=manifest_spec,
            descriptor=descriptor,
        )
        package_kind = _manifest_package_kind(
            manifest_spec=manifest_spec,
            descriptor=descriptor,
            package_section=package_section,
        )
        extra_metadata = _manifest_extra_metadata(
            workspace_root=workspace_root,
            package_root=package_root,
            manifest_path=manifest_path,
            manifest_spec=manifest_spec,
            descriptor=descriptor,
            package_section=package_section,
            package_kind=package_kind,
        )
        resolved = _ResolvedSemanticContractPackage(
            manifest_kind=descriptor.manifest_kind,
            manifest_path_key=f"{descriptor.manifest_kind}_path",
            package_name=_manifest_package_name(
                manifest_spec=manifest_spec,
                descriptor=descriptor,
                package_section=package_section,
                package_root=package_root,
            ),
            manifest_path=self._relative_to_workspace(
                path=manifest_path,
                workspace_root=workspace_root,
            ),
            package_root=self._relative_to_workspace(
                path=package_root,
                workspace_root=workspace_root,
            ),
            package_kind=package_kind,
            fqn_prefix=_optional_text_attribute(package_section, "fqn_prefix"),
            source_root=self._relative_to_workspace(
                path=source_root,
                workspace_root=workspace_root,
            ),
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            owned_file_paths=owned_file_paths,
            language=_language_for_manifest_descriptor(descriptor),
            extra_metadata=extra_metadata,
        )
        self._cache[cache_key] = resolved
        return resolved

    def _resolve_manifest_descriptor(
        self,
        *,
        package_root: Path,
    ) -> tuple[
        ModuleSemanticContract,
        ModuleSemanticManifestResolutionDescriptor,
        Path,
        object,
    ]:
        for contract, descriptor in self._manifest_resolution_entries():
            manifest_path = package_root / descriptor.filename
            if not manifest_path.exists():
                continue
            manifest_spec = _load_manifest_descriptor(
                descriptor=descriptor,
                manifest_path=manifest_path,
            )
            return contract, descriptor, manifest_path, manifest_spec
        searched = ", ".join(self.manifest_filenames())
        raise FileNotFoundError(
            f"No semantic package manifest found under {package_root}: {searched}"
        )

    def _manifest_resolution_entries(
        self,
    ) -> tuple[
        tuple[ModuleSemanticContract, ModuleSemanticManifestResolutionDescriptor],
        ...,
    ]:
        AwareModulePluginRegistry.ensure_builtin_plugins_registered()
        entries: list[
            tuple[ModuleSemanticContract, ModuleSemanticManifestResolutionDescriptor]
        ] = []
        for contract in AwareModulePluginRegistry.get_module_semantic_contracts():
            for descriptor in contract.manifest_resolution:
                if not descriptor.filename.strip():
                    continue
                entries.append((contract, descriptor))
        return tuple(
            sorted(
                entries,
                key=lambda item: (
                    item[1].priority,
                    item[0].provider_key,
                    item[1].semantic_owner,
                    item[1].manifest_kind,
                    item[1].filename,
                ),
            )
        )

    def _resolve_nearest_declared_workspace_root(self, *, start: Path) -> Path | None:
        cursor = start.resolve()
        if cursor.is_file():
            cursor = cursor.parent
        for candidate in [cursor, *cursor.parents]:
            if (candidate / "aware.workspace.toml").is_file():
                return candidate.resolve()
        return None

    def _load_workspace_registry_for_root(
        self,
        *,
        workspace_root: Path,
    ) -> ResolvedAwareWorkspaceRegistry | None:
        resolved_root = workspace_root.resolve()
        cached = self._workspace_registry_by_root.get(resolved_root)
        registry = load_aware_workspace_registry(
            workspace_root=resolved_root,
            cached=cached,
        )
        self._workspace_registry_by_root[resolved_root] = registry
        return registry

    def _ensure_manifest_is_workspace_declared(self, *, manifest_path: Path) -> None:
        if not self._require_workspace_membership:
            return
        declared_workspace_root = self._resolve_nearest_declared_workspace_root(
            start=manifest_path
        )
        if declared_workspace_root is None:
            return

        registry = self._load_workspace_registry_for_root(
            workspace_root=declared_workspace_root
        )
        if (
            registry is None
            or registry.source != AwareWorkspaceRegistrySource.workspace_toml
        ):
            raise ValueError(
                f"Authoritative workspace registry missing for manifest {manifest_path}"
            )

        if not self._manifest_is_declared_in_workspace_registry(
            manifest_path=manifest_path.resolve(),
            registry=registry,
        ):
            raise ValueError(
                "Manifest is not declared in authoritative aware.workspace.toml: "
                f"{manifest_path}"
            )

    def _manifest_is_declared_in_workspace_registry(
        self,
        *,
        manifest_path: Path,
        registry: ResolvedAwareWorkspaceRegistry | None,
    ) -> bool:
        if (
            registry is None
            or registry.source != AwareWorkspaceRegistrySource.workspace_toml
        ):
            return True
        resolved_manifest_path = manifest_path.resolve()
        return any(
            entry.resolved_path == resolved_manifest_path for entry in registry.entries
        ) or any(
            path == resolved_manifest_path
            for path in registry.module_package_manifest_paths
        )

    def _scan_source_files(
        self,
        *,
        workspace_root: Path,
        sources_root: Path,
        include_paths: tuple[str, ...],
        exclude_paths: tuple[str, ...],
    ) -> tuple[str, ...]:
        if not sources_root.exists() or not sources_root.is_dir():
            return ()

        included: set[Path] = set()
        for pattern in include_paths:
            raw_pattern = pattern.strip()
            if not raw_pattern:
                continue
            try:
                matches = sources_root.glob(raw_pattern)
            except Exception as exc:
                logger.debug(
                    "Failed to glob %r under %s: %s",
                    raw_pattern,
                    sources_root,
                    exc,
                )
                continue
            for candidate in matches:
                if (
                    not candidate.is_file()
                    or candidate.suffix != _AWARE_SOURCE_EXTENSION
                ):
                    continue
                resolved = candidate.resolve()
                if not self._is_within(candidate=resolved, root=sources_root):
                    continue
                if self._has_ignored_segment(resolved.relative_to(sources_root).parts):
                    continue
                included.add(resolved)

        for pattern in exclude_paths:
            raw_pattern = pattern.strip()
            if not raw_pattern:
                continue
            try:
                matches = sources_root.glob(raw_pattern)
            except Exception as exc:
                logger.debug(
                    "Failed to glob exclude %r under %s: %s",
                    raw_pattern,
                    sources_root,
                    exc,
                )
                continue
            for candidate in matches:
                if candidate.is_file():
                    included.discard(candidate.resolve())

        owned_paths: list[str] = []
        for candidate in sorted(included):
            try:
                owned_paths.append(
                    self._relative_to_workspace(
                        path=candidate,
                        workspace_root=workspace_root,
                    )
                )
            except ValueError:
                logger.debug("Skipping source outside workspace root: %s", candidate)
                continue
        return tuple(owned_paths)

    def _relative_to_workspace(self, *, path: Path, workspace_root: Path) -> str:
        return path.resolve().relative_to(workspace_root).as_posix()

    def _is_within(self, *, candidate: Path, root: Path) -> bool:
        try:
            _ = candidate.resolve().relative_to(root.resolve())
        except Exception:
            return False
        return True

    def _has_ignored_segment(self, parts: tuple[str, ...]) -> bool:
        return any(part in _IGNORED_SEGMENTS for part in parts)


def _load_manifest_descriptor(
    *,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    manifest_path: Path,
) -> object:
    module = import_module(descriptor.loader_module)
    loader = getattr(module, descriptor.loader_name)
    return loader(toml_path=manifest_path)


def _manifest_package_name(
    *,
    manifest_spec: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    package_section: object | None,
    package_root: Path,
) -> str:
    direct = _optional_text_attribute(manifest_spec, "package_name")
    if direct is not None:
        return direct
    section_name = _optional_text_attribute(package_section, "package_name")
    if section_name is not None:
        return section_name
    return package_root.name


def _manifest_package_kind(
    *,
    manifest_spec: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    package_section: object | None,
) -> str | None:
    section_kind = _optional_text_attribute(package_section, "kind")
    if section_kind is not None:
        return section_kind
    direct = _optional_text_attribute(manifest_spec, "package_kind")
    if direct is not None:
        return direct
    workspace_kind = _optional_text(descriptor.workspace_manifest_kind)
    if workspace_kind is not None and workspace_kind != "module_package":
        return workspace_kind
    contract = _optional_text(descriptor.contract)
    if contract is not None and contract.startswith("aware."):
        return contract.removeprefix("aware.").replace(".", "_")
    return _optional_text(descriptor.semantic_package_kind)


def _manifest_build_sources_dir(manifest_spec: object) -> str:
    build = getattr(manifest_spec, "build", None)
    sources_dir = _optional_text_attribute(build, "sources_dir")
    return sources_dir or "."


def _manifest_build_path_tuple(
    manifest_spec: object,
    *,
    attribute_name: str,
) -> tuple[str, ...]:
    build = getattr(manifest_spec, "build", None)
    raw = getattr(build, attribute_name, ())
    if raw is None:
        return ()
    if isinstance(raw, str):
        normalized = raw.strip()
        return (normalized,) if normalized else ()
    try:
        return tuple(text for item in raw if (text := _optional_text(item)) is not None)
    except TypeError:
        return ()


def _manifest_package_section(
    *,
    manifest_spec: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> object | None:
    for name in _manifest_package_section_candidates(descriptor):
        section = getattr(manifest_spec, name, None)
        if section is not None:
            return section
    return None


def _manifest_package_section_candidates(
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> tuple[str, ...]:
    candidates: list[str] = []
    workspace_kind = _optional_text(descriptor.workspace_manifest_kind)
    if workspace_kind is not None:
        candidates.append(
            "package" if workspace_kind == "module_package" else workspace_kind
        )
    contract = _optional_text(descriptor.contract)
    if contract is not None and contract.startswith("aware."):
        candidates.append(contract.removeprefix("aware.").replace(".", "_"))
    candidates.extend(
        candidate
        for candidate in (
            descriptor.semantic_root_kind,
            descriptor.semantic_package_kind,
            "package",
        )
        if _optional_text(candidate) is not None
    )
    seen: set[str] = set()
    deduped: list[str] = []
    for candidate in candidates:
        normalized = candidate.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return tuple(deduped)


def _manifest_extra_metadata(
    *,
    workspace_root: Path,
    package_root: Path,
    manifest_path: Path,
    manifest_spec: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    package_section: object | None,
    package_kind: str | None,
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    if package_kind is not None:
        metadata["package_kind"] = package_kind
    descriptor_metadata = _descriptor_semantic_package_metadata(descriptor)
    metadata.update(
        {
            key: value
            for key, value in descriptor_metadata.items()
            if key
            not in {
                "metadata_resolver_module",
                "metadata_resolver_name",
            }
        }
    )
    for key in descriptor.copy_code_package_metadata_keys:
        value = _attribute_from_manifest(
            manifest_spec=manifest_spec,
            package_section=package_section,
            key=key,
        )
        if value is not None:
            metadata[key] = value
    metadata.update(
        _dynamic_manifest_extra_metadata(
            workspace_root=workspace_root,
            package_root=package_root,
            manifest_path=manifest_path,
            manifest_spec=manifest_spec,
            descriptor=descriptor,
            metadata=metadata,
        )
    )
    return metadata


def _descriptor_semantic_package_metadata(
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> dict[str, object]:
    raw_metadata = descriptor.semantic_package_metadata
    if not isinstance(raw_metadata, Mapping):
        return {}
    return {
        str(key): value
        for key, value in raw_metadata.items()
        if isinstance(key, str) and key.strip()
    }


def _dynamic_manifest_extra_metadata(
    *,
    workspace_root: Path,
    package_root: Path,
    manifest_path: Path,
    manifest_spec: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    metadata: Mapping[str, object],
) -> dict[str, object]:
    descriptor_metadata = _descriptor_semantic_package_metadata(descriptor)
    resolver_module = _optional_text(
        descriptor_metadata.get("metadata_resolver_module")
    )
    resolver_name = _optional_text(descriptor_metadata.get("metadata_resolver_name"))
    if resolver_module is None and resolver_name is None:
        return {}
    if resolver_module is None or resolver_name is None:
        raise ValueError(
            "Semantic manifest metadata resolver requires both "
            "metadata_resolver_module and metadata_resolver_name: "
            f"manifest_kind={descriptor.manifest_kind!r}"
        )
    module = import_module(resolver_module)
    resolver = getattr(module, resolver_name)
    result = resolver(
        workspace_root=workspace_root,
        package_root=package_root,
        manifest_path=manifest_path,
        manifest_spec=manifest_spec,
        descriptor=descriptor,
        metadata=dict(metadata),
    )
    if result is None:
        return {}
    if not isinstance(result, Mapping):
        raise ValueError(
            "Semantic manifest metadata resolver must return a mapping: "
            f"{resolver_module}.{resolver_name}"
        )
    return {
        str(key): value
        for key, value in result.items()
        if isinstance(key, str) and key.strip()
    }


def _attribute_from_manifest(
    *,
    manifest_spec: object,
    package_section: object | None,
    key: str,
) -> object | None:
    for target in (
        package_section,
        getattr(manifest_spec, "build", None),
        manifest_spec,
    ):
        if target is None:
            continue
        value = getattr(target, key, None)
        if value is None:
            continue
        normalized = _enum_value(value)
        if normalized is not None:
            return normalized
        return value
    return None


def _language_for_manifest_descriptor(
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> CodeLanguage:
    filename = descriptor.filename
    if filename == "pubspec.yaml":
        return CodeLanguage.dart
    if filename in {"pyproject.toml", "setup.py"}:
        return CodeLanguage.python
    return CodeLanguage.aware


def _optional_text_attribute(target: object | None, attribute_name: str) -> str | None:
    if target is None:
        return None
    return _optional_text(getattr(target, attribute_name, None))


def _optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    enum_value = _enum_value(value)
    if enum_value is not None:
        return enum_value
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    normalized = str(value).strip()
    return normalized or None


def _enum_value(value: object) -> str | None:
    raw = getattr(value, "value", None)
    if not isinstance(raw, str):
        return None
    normalized = raw.strip()
    return normalized or None


__all__ = ["SemanticContractCodePackageDiscovery"]
