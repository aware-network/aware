from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import sys

from aware_code.module_manifest.loader import (
    AwareModuleTomlError,
    load_aware_module_spec,
)
from aware_code.module_plugin import AwareModulePlugin
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.semantic_contract_profile_manifest import (
    CodeSemanticContractProfileProviderSpec,
    load_code_semantic_contract_profile_manifest,
)

_CODE_MODULE_PLUGIN_KIND = "code.module_plugin"
_SEMANTIC_PROVIDER_CONTRACT = "aware.semantic_provider"
_SEMANTIC_CONTRACT_IMPORT_ROLE = "semantic_contract"
_PROFILE_MANIFEST_NAME = "aware.semantic_contract_profile.toml"


class CodeSemanticContractProfilePackageResolutionError(ValueError):
    """Raised when a Code semantic contract profile package cannot resolve."""


@dataclass(frozen=True, slots=True)
class CodeSemanticContractRuntimeImportRecord:
    profile_package_ref: str
    profile_key: str
    provider_key: str
    semantic_contract_module: str
    import_role: str = _SEMANTIC_CONTRACT_IMPORT_ROLE
    owned_manifest_kinds: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    required: bool = True
    status: str = "active"
    runtime_root: Path | None = None
    source_module_root: Path | None = None


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfileModuleSource:
    module_id: str
    module_root: Path


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfilePackageResolution:
    profile_package_ref: str
    profile_key: str
    runtime_import_mode: str
    runtime_import_required: bool
    runtime_imports: tuple[CodeSemanticContractRuntimeImportRecord, ...]


def resolve_code_semantic_contract_profile_package_runtime_imports(
    *,
    profile_package_ref: str,
    profile_key: str,
    module_roots: Iterable[Path],
    module_sources: Iterable[CodeSemanticContractProfileModuleSource] = (),
    profile_manifest_roots: Iterable[Path] = (),
    semantic_contract_provider_keys: Iterable[str] = (),
    runtime_import_mode: str = "dynamic_contract_module",
    runtime_import_required: bool = True,
) -> CodeSemanticContractProfilePackageResolution:
    """Resolve provider-authored runtime imports for one profile package.

    This local-source resolver intentionally knows only the Code module manifest
    semantic-contract shape. Provider keys and module paths come from module
    manifests, not from Workspace-owned package/provider lookup tables.
    """

    normalized_profile_package_ref = profile_package_ref.strip()
    normalized_profile_key = profile_key.strip()
    if not normalized_profile_package_ref:
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_package_unresolved: "
            "profile_package_ref is empty"
        )
    if not normalized_profile_key:
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_package_unresolved: profile_key is empty"
        )

    requested_provider_keys = tuple(
        dict.fromkeys(
            provider_key.strip()
            for provider_key in semantic_contract_provider_keys
            if provider_key.strip()
        )
    )
    sources = _resolved_module_sources(
        module_roots=module_roots,
        module_sources=module_sources,
    )
    profile_manifest_paths = _profile_manifest_paths(
        profile_key=normalized_profile_key,
        profile_manifest_roots=profile_manifest_roots,
    )
    runtime_imports = _runtime_imports_from_profile_manifests(
        profile_package_ref=normalized_profile_package_ref,
        profile_key=normalized_profile_key,
        module_sources=sources,
        profile_manifest_paths=profile_manifest_paths,
        requested_provider_keys=requested_provider_keys,
        runtime_import_required=runtime_import_required,
    )
    if requested_provider_keys:
        resolved_provider_keys = {
            runtime_import.provider_key for runtime_import in runtime_imports
        }
        missing_provider_keys = tuple(
            provider_key
            for provider_key in requested_provider_keys
            if provider_key not in resolved_provider_keys
        )
        if missing_provider_keys:
            raise CodeSemanticContractProfilePackageResolutionError(
                "semantic_contract_profile_missing_provider: "
                f"profile_package_ref={normalized_profile_package_ref!r} "
                f"profile_key={normalized_profile_key!r} missing "
                f"providers={missing_provider_keys!r}"
            )
    if not runtime_imports and runtime_import_required:
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_package_unresolved: "
            f"profile_package_ref={normalized_profile_package_ref!r} "
            f"profile_key={normalized_profile_key!r} has no runtime imports"
        )
    return CodeSemanticContractProfilePackageResolution(
        profile_package_ref=normalized_profile_package_ref,
        profile_key=normalized_profile_key,
        runtime_import_mode=runtime_import_mode,
        runtime_import_required=runtime_import_required,
        runtime_imports=runtime_imports,
    )


def register_code_semantic_contract_runtime_imports(
    runtime_imports: Iterable[CodeSemanticContractRuntimeImportRecord],
    *,
    replace_existing: bool = False,
) -> None:
    """Register explicit Code semantic contract runtime imports."""

    for runtime_import in runtime_imports:
        if runtime_import.status != "active":
            continue
        if runtime_import.import_role != _SEMANTIC_CONTRACT_IMPORT_ROLE:
            continue
        provider_key = runtime_import.provider_key.strip()
        semantic_contract_module = runtime_import.semantic_contract_module.strip()
        if not provider_key or not semantic_contract_module:
            continue
        _ensure_runtime_root_on_sys_path(runtime_import.runtime_root)
        AwareModulePluginRegistry.register(
            AwareModulePlugin(
                provider_key=provider_key,
                semantic_contract_module=semantic_contract_module,
            ),
            replace_existing=replace_existing,
        )


def _runtime_imports_from_profile_manifests(
    *,
    profile_package_ref: str,
    profile_key: str,
    module_sources: tuple[CodeSemanticContractProfileModuleSource, ...],
    profile_manifest_paths: tuple[Path, ...],
    requested_provider_keys: tuple[str, ...],
    runtime_import_required: bool,
) -> tuple[CodeSemanticContractRuntimeImportRecord, ...]:
    module_specs = {
        source.module_id: _load_module_spec(module_source=source)
        for source in module_sources
    }
    source_by_module_id = {source.module_id: source for source in module_sources}
    matched_profile_count = 0
    records_by_provider: dict[str, CodeSemanticContractRuntimeImportRecord] = {}
    existing_manifest_paths = tuple(path for path in profile_manifest_paths if path.is_file())
    if not existing_manifest_paths:
        expected_paths = tuple(path.as_posix() for path in profile_manifest_paths)
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_package_unresolved: workspace profile "
            f"manifest not found for profile_key={profile_key!r}; expected "
            f"paths={expected_paths!r}"
        )
    for manifest_path in existing_manifest_paths:
        try:
            profile_manifest = load_code_semantic_contract_profile_manifest(
                toml_path=manifest_path,
            )
        except AwareModuleTomlError as exc:
            raise CodeSemanticContractProfilePackageResolutionError(
                "semantic_contract_profile_package_unresolved: invalid "
                f"profile manifest {manifest_path}: {exc}"
            ) from exc
        if profile_manifest.profile.key != profile_key:
            raise CodeSemanticContractProfilePackageResolutionError(
                "semantic_contract_profile_package_unresolved: profile "
                f"manifest {manifest_path} declares key "
                f"{profile_manifest.profile.key!r}, expected {profile_key!r}"
            )
        if profile_manifest.profile.status != "active":
            continue
        matched_profile_count += 1
        if matched_profile_count > 1:
            raise CodeSemanticContractProfilePackageResolutionError(
                "semantic_contract_profile_package_conflict: profile "
                f"{profile_key!r} is declared by multiple workspace profile "
                "manifests"
            )
        for provider in profile_manifest.providers:
            if provider.status != "active":
                continue
            if requested_provider_keys and provider.provider_key not in requested_provider_keys:
                continue
            record = _runtime_import_from_profile_provider(
                profile_package_ref=profile_package_ref,
                profile_key=profile_key,
                provider=provider,
                module_specs=module_specs,
                source_by_module_id=source_by_module_id,
                runtime_import_required=(
                    runtime_import_required
                    and profile_manifest.profile.runtime_import_required
                    and provider.required
                ),
            )
            if record is None:
                continue
            _append_runtime_import(
                records_by_provider=records_by_provider,
                record=record,
            )
    if matched_profile_count == 0:
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_package_unresolved: workspace profile "
            f"manifest for profile_key={profile_key!r} is not active"
        )
    return tuple(records_by_provider.values())


def _profile_manifest_paths(
    *,
    profile_key: str,
    profile_manifest_roots: Iterable[Path],
) -> tuple[Path, ...]:
    paths: list[Path] = []
    seen: set[str] = set()
    for root in profile_manifest_roots:
        resolved_root = root.expanduser().resolve()
        if resolved_root.name == _PROFILE_MANIFEST_NAME:
            candidate = resolved_root
        elif resolved_root.name == profile_key:
            candidate = (resolved_root / _PROFILE_MANIFEST_NAME).resolve()
        else:
            candidate = (
                resolved_root / profile_key / _PROFILE_MANIFEST_NAME
            ).resolve()
        key = candidate.as_posix()
        if key in seen:
            continue
        seen.add(key)
        paths.append(candidate)
    return tuple(paths)


def _runtime_import_from_profile_provider(
    *,
    profile_package_ref: str,
    profile_key: str,
    provider: CodeSemanticContractProfileProviderSpec,
    module_specs: dict[str, object],
    source_by_module_id: dict[str, CodeSemanticContractProfileModuleSource],
    runtime_import_required: bool,
) -> CodeSemanticContractRuntimeImportRecord | None:
    module_source = source_by_module_id.get(provider.module_id)
    module_spec = module_specs.get(provider.module_id)
    if module_source is None or module_spec is None:
        if provider.required:
            raise CodeSemanticContractProfilePackageResolutionError(
                "semantic_contract_profile_missing_module: provider "
                f"{provider.provider_key!r} targets missing module "
                f"{provider.module_id!r}"
            )
        return None
    plugin_modules = _plugin_semantic_contract_modules(module_spec)
    record = _runtime_import_from_module_source_provider(
        profile_package_ref=profile_package_ref,
        profile_key=profile_key,
        module_source=module_source,
        module_spec=module_spec,
        plugin_modules=plugin_modules,
        provider_key=provider.provider_key,
        runtime_import_required=runtime_import_required,
    )
    if record is None and provider.required:
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_missing_provider: module "
            f"{provider.module_id!r} does not declare provider "
            f"{provider.provider_key!r}"
        )
    return record


def _runtime_import_from_module_source_provider(
    *,
    profile_package_ref: str,
    profile_key: str,
    module_source: CodeSemanticContractProfileModuleSource,
    module_spec: object,
    plugin_modules: dict[str, str | None],
    provider_key: str,
    runtime_import_required: bool,
) -> CodeSemanticContractRuntimeImportRecord | None:
    semantic_contract = _module_spec_semantic_provider_contract(
        module_spec=module_spec,
        provider_key=provider_key,
    )
    semantic_contract_module = (
        getattr(semantic_contract, "module", "") if semantic_contract is not None else ""
    ).strip() or plugin_modules.get(provider_key) or ""
    if not semantic_contract_module:
        return None
    return CodeSemanticContractRuntimeImportRecord(
        profile_package_ref=profile_package_ref,
        profile_key=profile_key,
        provider_key=provider_key,
        semantic_contract_module=semantic_contract_module,
        owned_manifest_kinds=(
            tuple(getattr(semantic_contract, "owns_manifest_kinds", ()))
            if semantic_contract is not None
            else ()
        ),
        capabilities=(
            tuple(getattr(semantic_contract, "capabilities", ()))
            if semantic_contract is not None
            else ()
        ),
        required=runtime_import_required,
        runtime_root=(module_source.module_root / getattr(module_spec, "runtime_root")).resolve(),
        source_module_root=module_source.module_root,
    )


def _resolved_module_sources(
    *,
    module_roots: Iterable[Path],
    module_sources: Iterable[CodeSemanticContractProfileModuleSource],
) -> tuple[CodeSemanticContractProfileModuleSource, ...]:
    resolved: list[CodeSemanticContractProfileModuleSource] = []
    seen_module_ids: set[str] = set()
    for source in module_sources:
        module_id = source.module_id.strip()
        if not module_id or module_id in seen_module_ids:
            continue
        seen_module_ids.add(module_id)
        resolved.append(
            CodeSemanticContractProfileModuleSource(
                module_id=module_id,
                module_root=source.module_root.expanduser().resolve(),
            )
        )
    for module_root in module_roots:
        resolved_module_root = module_root.expanduser().resolve()
        module_id = resolved_module_root.name.strip()
        if not module_id or module_id in seen_module_ids:
            continue
        seen_module_ids.add(module_id)
        resolved.append(
            CodeSemanticContractProfileModuleSource(
                module_id=module_id,
                module_root=resolved_module_root,
            )
        )
    return tuple(resolved)


def _load_module_spec(*, module_source: CodeSemanticContractProfileModuleSource) -> object:
    module_toml_path = module_source.module_root / "aware.module.toml"
    if not module_toml_path.is_file():
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_package_unresolved: module "
            f"{module_source.module_id!r} does not expose {module_toml_path}"
        )
    try:
        return load_aware_module_spec(toml_path=module_toml_path)
    except AwareModuleTomlError as exc:
        raise CodeSemanticContractProfilePackageResolutionError(
            "semantic_contract_profile_package_unresolved: invalid "
            f"module manifest {module_toml_path}: {exc}"
        ) from exc


def _plugin_semantic_contract_modules(module_spec: object) -> dict[str, str | None]:
    return {
        (plugin.provider_key or "").strip(): (
            (plugin.semantic_contract_module or "").strip() or None
        )
        for plugin in getattr(module_spec, "plugins", ())
        if plugin.kind == _CODE_MODULE_PLUGIN_KIND
        and plugin.required
        and (plugin.provider_key or "").strip()
    }


def _module_spec_semantic_provider_keys(*, module_spec: object) -> tuple[str, ...]:
    provider_keys: list[str] = []
    for package in getattr(module_spec, "packages", ()):
        semantic_contract = getattr(package, "semantic_contract", None)
        if semantic_contract is None:
            continue
        if semantic_contract.contract != _SEMANTIC_PROVIDER_CONTRACT:
            continue
        provider_key = semantic_contract.provider_key.strip()
        if provider_key:
            provider_keys.append(provider_key)
    provider_keys.extend(_plugin_semantic_contract_modules(module_spec))
    return tuple(dict.fromkeys(provider_keys))


def _module_spec_semantic_provider_contract(
    *,
    module_spec: object,
    provider_key: str,
) -> object | None:
    for package in getattr(module_spec, "packages", ()):
        semantic_contract = getattr(package, "semantic_contract", None)
        if semantic_contract is None:
            continue
        if semantic_contract.contract != _SEMANTIC_PROVIDER_CONTRACT:
            continue
        if semantic_contract.provider_key == provider_key:
            return semantic_contract
    return None


def _append_runtime_import(
    *,
    records_by_provider: dict[str, CodeSemanticContractRuntimeImportRecord],
    record: CodeSemanticContractRuntimeImportRecord,
) -> None:
    existing = records_by_provider.get(record.provider_key)
    if existing is None:
        records_by_provider[record.provider_key] = record
        return
    if existing.semantic_contract_module == record.semantic_contract_module:
        return
    raise CodeSemanticContractProfilePackageResolutionError(
        "semantic_contract_profile_provider_conflict: "
        f"provider {record.provider_key!r} resolves multiple semantic "
        "contract modules "
        f"{existing.semantic_contract_module!r} and "
        f"{record.semantic_contract_module!r}"
    )


def _ensure_runtime_root_on_sys_path(runtime_root: Path | None) -> None:
    if runtime_root is None or not runtime_root.is_dir():
        return
    runtime_root_text = runtime_root.as_posix()
    if runtime_root_text not in sys.path:
        sys.path.insert(0, runtime_root_text)


__all__ = [
    "CodeSemanticContractProfileModuleSource",
    "CodeSemanticContractProfilePackageResolution",
    "CodeSemanticContractProfilePackageResolutionError",
    "CodeSemanticContractRuntimeImportRecord",
    "register_code_semantic_contract_runtime_imports",
    "resolve_code_semantic_contract_profile_package_runtime_imports",
]
