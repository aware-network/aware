"""Aware-specific module discovery backed by `aware.module.toml` contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from typing_extensions import override

from aware_code.module.discovery import CodeModuleDiscovery
from aware_grammar.module.loader import AwareModuleTomlError, load_aware_module_spec
from aware_meta.manifest.loader import AwareTomlError, load_aware_toml_spec
from aware_utils.logging import logger


_AWARE_MODULE_TOML = "aware.module.toml"
_AWARE_PACKAGE_TOML = "aware.toml"
_AWARE_SOURCE_EXTENSION = ".aware"
_IGNORED_SEGMENTS = frozenset({".aware", ".git", "__pycache__", "node_modules", ".venv", "venv"})


@dataclass(frozen=True, slots=True)
class _ResolvedAwarePackage:
    module_package_id: str
    module_package_kind: str
    module_package_manifest: str
    module_package_visibility: str
    aware_toml_path: str
    package_name: str
    package_kind: str
    package_root: str
    source_root: str
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    semantic_contract: "_ResolvedAwarePackageSemanticContract | None"
    semantic_bindings: tuple["_ResolvedAwarePackageSemanticBinding", ...]
    mirrors_ontology: bool
    source_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ResolvedAwarePackageSemanticContractBinding:
    capability: str
    module: str
    callable: str


@dataclass(frozen=True, slots=True)
class _ResolvedAwarePackageSemanticContract:
    role: str
    contract: str
    provider_key: str
    module: str
    bindings: tuple[_ResolvedAwarePackageSemanticContractBinding, ...]


@dataclass(frozen=True, slots=True)
class _ResolvedAwarePackageSemanticBinding:
    role: str
    contract: str
    binding_module: str | None
    capabilities: tuple[str, ...]
    callable_name: str | None


@dataclass(frozen=True, slots=True)
class _ResolvedAwareModule:
    module_id: str
    module_toml_path: str
    structure_root: str
    runtime_root: str
    representation_root: str
    source_roots: tuple[str, ...]
    owned_file_paths: tuple[str, ...]
    packages: tuple[_ResolvedAwarePackage, ...]

    def to_metadata(self) -> dict[str, object]:
        return {
            "module_id": self.module_id,
            "aware_module_toml_path": self.module_toml_path,
            "structure_root": self.structure_root,
            "runtime_root": self.runtime_root,
            "representation_root": self.representation_root,
            "source_roots": list(self.source_roots),
            "owned_file_paths": list(self.owned_file_paths),
            "packages": [
                {
                    "module_package_id": package.module_package_id,
                    "module_package_kind": package.module_package_kind,
                    "module_package_manifest": package.module_package_manifest,
                    "module_package_visibility": package.module_package_visibility,
                    "aware_toml_path": package.aware_toml_path,
                    "package_name": package.package_name,
                    "package_kind": package.package_kind,
                    "package_root": package.package_root,
                    "source_root": package.source_root,
                    "include_paths": list(package.include_paths),
                    "exclude_paths": list(package.exclude_paths),
                    "semantic_contract": (
                        {
                            "role": package.semantic_contract.role,
                            "contract": package.semantic_contract.contract,
                            "provider_key": package.semantic_contract.provider_key,
                            "module": package.semantic_contract.module,
                            "bindings": [
                                {
                                    "capability": binding.capability,
                                    "module": binding.module,
                                    "callable": binding.callable,
                                }
                                for binding in package.semantic_contract.bindings
                            ],
                        }
                        if package.semantic_contract is not None
                        else None
                    ),
                    "semantic_bindings": [
                        {
                            "role": binding.role,
                            "contract": binding.contract,
                            "binding_module": binding.binding_module,
                            "capabilities": list(binding.capabilities),
                            "callable": binding.callable_name,
                        }
                        for binding in package.semantic_bindings
                    ],
                    "mirrors_ontology": package.mirrors_ontology,
                    "source_files": list(package.source_files),
                }
                for package in self.packages
            ],
        }


class AwareCodeModuleDiscovery(CodeModuleDiscovery):
    """Discover Aware modules from `aware.module.toml`, not `.aware` path heuristics."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], _ResolvedAwareModule] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    @override
    def is_module_root(self, path: Path, workspace_root: Path) -> bool:
        try:
            _ = self._resolve_module(path=path, workspace_root=workspace_root)
        except (AwareModuleTomlError, AwareTomlError, FileNotFoundError, ValueError) as exc:
            logger.debug(f"Skipping invalid Aware module root {path}: {exc}")
            return False
        return True

    @override
    def get_module_name(self, module_path: Path, workspace_root: Path) -> str:
        return self._resolve_module(path=module_path, workspace_root=workspace_root).module_id

    @override
    def get_entry_points(self, module_path: Path, workspace_root: Path) -> list[Path]:
        _ = self._resolve_module(path=module_path, workspace_root=workspace_root)
        return []

    @override
    def get_metadata(self, module_path: Path, workspace_root: Path) -> dict[str, object]:
        return self._resolve_module(path=module_path, workspace_root=workspace_root).to_metadata()

    def _resolve_module(self, *, path: Path, workspace_root: Path) -> _ResolvedAwareModule:
        workspace_root = workspace_root.resolve()
        module_path = path
        cache_key = (workspace_root.as_posix(), module_path.as_posix())
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        module_root = (workspace_root / module_path).resolve()
        if not module_root.is_dir():
            raise ValueError(f"Module root is not a directory: {module_root}")

        module_toml_path = module_root / _AWARE_MODULE_TOML
        module_spec = load_aware_module_spec(toml_path=module_toml_path)

        packages: list[_ResolvedAwarePackage] = []
        source_roots: list[str] = []
        owned_file_paths: list[str] = []

        for package_spec in module_spec.packages:
            aware_toml_abs = (module_root / package_spec.manifest).resolve()
            if aware_toml_abs.name != _AWARE_PACKAGE_TOML:
                continue
            if not aware_toml_abs.exists():
                raise FileNotFoundError(f"aware.toml not found for package: {aware_toml_abs}")

            aware_toml_spec = load_aware_toml_spec(toml_path=aware_toml_abs)
            package_root = aware_toml_abs.parent.resolve()
            source_root = (package_root / aware_toml_spec.build.sources_dir).resolve()

            source_files = self._scan_source_files(
                workspace_root=workspace_root,
                sources_root=source_root,
                include_paths=tuple(aware_toml_spec.build.include_paths),
                exclude_paths=tuple(aware_toml_spec.build.exclude_paths),
            )
            source_root_rel = self._relative_to_workspace(path=source_root, workspace_root=workspace_root)

            packages.append(
                _ResolvedAwarePackage(
                    module_package_id=package_spec.id,
                    module_package_kind=package_spec.kind,
                    module_package_manifest=package_spec.manifest,
                    module_package_visibility=package_spec.visibility,
                    aware_toml_path=self._relative_to_workspace(path=aware_toml_abs, workspace_root=workspace_root),
                    package_name=aware_toml_spec.package.package_name,
                    package_kind=aware_toml_spec.package.kind.value,
                    package_root=self._relative_to_workspace(path=package_root, workspace_root=workspace_root),
                    source_root=source_root_rel,
                    include_paths=tuple(aware_toml_spec.build.include_paths),
                    exclude_paths=tuple(aware_toml_spec.build.exclude_paths),
                    semantic_contract=(
                        _ResolvedAwarePackageSemanticContract(
                            role=package_spec.semantic_contract.role,
                            contract=package_spec.semantic_contract.contract,
                            provider_key=package_spec.semantic_contract.provider_key,
                            module=package_spec.semantic_contract.module,
                            bindings=tuple(
                                _ResolvedAwarePackageSemanticContractBinding(
                                    capability=binding.capability,
                                    module=binding.module,
                                    callable=binding.callable,
                                )
                                for binding in package_spec.semantic_contract.bindings
                            ),
                        )
                        if package_spec.semantic_contract is not None
                        else None
                    ),
                    semantic_bindings=tuple(
                        _ResolvedAwarePackageSemanticBinding(
                            role=binding.role,
                            contract=binding.contract,
                            binding_module=binding.binding_module,
                            capabilities=binding.capabilities,
                            callable_name=binding.callable_name,
                        )
                        for binding in package_spec.semantic_bindings
                    ),
                    mirrors_ontology=package_spec.mirrors_ontology,
                    source_files=source_files,
                )
            )
            source_roots.append(source_root_rel)
            owned_file_paths.extend(source_files)

        resolved = _ResolvedAwareModule(
            module_id=module_path.name,
            module_toml_path=self._relative_to_workspace(path=module_toml_path, workspace_root=workspace_root),
            structure_root=self._relative_to_workspace(
                path=(module_root / module_spec.structure_root).resolve(),
                workspace_root=workspace_root,
            ),
            runtime_root=self._relative_to_workspace(
                path=(module_root / module_spec.runtime_root).resolve(),
                workspace_root=workspace_root,
            ),
            representation_root=self._relative_to_workspace(
                path=(module_root / module_spec.representation_root).resolve(),
                workspace_root=workspace_root,
            ),
            source_roots=self._dedupe(source_roots),
            owned_file_paths=self._dedupe(owned_file_paths),
            packages=tuple(packages),
        )
        self._cache[cache_key] = resolved
        return resolved

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
                logger.debug(f"Failed to glob {raw_pattern!r} under {sources_root}: {exc}")
                continue
            for candidate in matches:
                if not candidate.is_file() or candidate.suffix != _AWARE_SOURCE_EXTENSION:
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
                logger.debug(f"Failed to glob exclude {raw_pattern!r} under {sources_root}: {exc}")
                continue
            for candidate in matches:
                if candidate.is_file():
                    included.discard(candidate.resolve())

        owned_paths: list[str] = []
        for candidate in sorted(included):
            try:
                owned_paths.append(self._relative_to_workspace(path=candidate, workspace_root=workspace_root))
            except ValueError:
                logger.debug(f"Skipping Aware source outside workspace root: {candidate}")
                continue
        return tuple(owned_paths)

    def _relative_to_workspace(self, *, path: Path, workspace_root: Path) -> str:
        return path.resolve().relative_to(workspace_root).as_posix()

    def _is_within(self, *, candidate: Path, root: Path) -> bool:
        try:
            candidate.resolve().relative_to(root.resolve())
        except Exception:
            return False
        return True

    def _has_ignored_segment(self, parts: tuple[str, ...]) -> bool:
        return any(part in _IGNORED_SEGMENTS for part in parts)

    def _dedupe(self, items: list[str]) -> tuple[str, ...]:
        ordered: list[str] = []
        seen: set[str] = set()
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        return tuple(ordered)


__all__ = ["AwareCodeModuleDiscovery"]
