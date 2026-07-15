from __future__ import annotations

from pathlib import Path
import tomllib

from aware_code.package.manifest_loader import load_pyproject_toml_package_manifest
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.module_semantic_contract import WorkspaceSemanticPackageLayoutRequest
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_sdk import (
    CodePackageConfigBindingContract,
    CodePackageLayoutContract,
    CodePackageManifestContract,
)
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec


def resolve_service_python_package_layout(
    *,
    request: WorkspaceSemanticPackageLayoutRequest,
) -> CodePackageLayoutContract | None:
    if request.manifest_kind != "aware_service_toml":
        return None
    try:
        service_spec = load_aware_service_toml_spec(toml_path=request.manifest_path)
    except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError):
        return None
    implementation_package = next(
        (
            package
            for package in service_spec.implementation.packages
            if _language_value(package.language) == CodeLanguage.python.value
        ),
        None,
    )
    if implementation_package is None:
        return None

    package_root_path = (
        request.manifest_path.parent / implementation_package.package_root
    ).resolve()
    package_manifest_path = (
        package_root_path / implementation_package.manifest_path
    ).resolve()
    package_name = implementation_package.package_name
    package_manager_name_key = package_name
    dependency_names: list[str] = []
    dependency_keys: list[str] = []
    if package_manifest_path.is_file():
        try:
            package_manifest = load_pyproject_toml_package_manifest(
                toml_path=package_manifest_path,
            )
        except (OSError, tomllib.TOMLDecodeError, ValueError):
            package_manifest = None
        if package_manifest is not None:
            package_name = package_manifest.package_name
            package_manager_name_key = package_manifest.package_manager_name_key
            dependency_names = list(package_manifest.package_dependency_names)
            dependency_keys = list(package_manifest.package_dependency_keys)

    package_root = _workspace_relative_path(
        workspace_root=request.workspace_root,
        path=package_root_path,
    )
    manifest_relative_path = _workspace_relative_path(
        workspace_root=request.workspace_root,
        path=package_manifest_path,
    )
    service_manifest_relative_path = _workspace_relative_path(
        workspace_root=request.workspace_root,
        path=request.manifest_path,
    )
    config_ref = source_code_package_config_ref(
        manifest_kind="pyproject_toml",
        surface="service",
    )
    return CodePackageLayoutContract(
        package_name=package_name,
        package_fqn=package_name,
        fqn_prefix=request.fqn_prefix,
        package_root=package_root,
        sources_root=package_root,
        surface="service",
        generated_roots=[
            f"{package_root.rstrip('/')}/.aware",
            f"{package_root.rstrip('/')}/__pycache__",
        ],
        owned_file_paths=[
            service_manifest_relative_path,
            manifest_relative_path,
        ],
        manifest_relative_path=manifest_relative_path,
        manifest=CodePackageManifestContract(
            manifest_kind="pyproject_toml",
            manifest_relative_path=manifest_relative_path,
            language=CodeLanguage.python.value,
            package_manager_name=package_name,
            package_manager_name_key=package_manager_name_key,
            dependency_names=dependency_names,
            dependency_keys=dependency_keys,
        ),
        semantic_binding=request.semantic_binding,
        config_binding=CodePackageConfigBindingContract(
            code_package_config_id=config_ref.config_id,
            code_package_config_key=config_ref.config_key,
            manifest_kind=config_ref.manifest_kind,
            surface=config_ref.surface,
        ),
        metadata={
            "source": "aware_service_runtime.semantic_package_layout",
            "package_name": package_name,
            "fqn_prefix": request.fqn_prefix,
            "package_manager_name_key": package_manager_name_key,
            "package_dependency_names": dependency_names,
            "package_dependency_keys": dependency_keys,
            "manifest_kind": "pyproject_toml",
            "language": CodeLanguage.python.value,
            "service_manifest_path": service_manifest_relative_path,
        },
    )


def _language_value(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str) and enum_value.strip():
        return enum_value.strip()
    return None


def _workspace_relative_path(*, workspace_root: Path, path: Path) -> str:
    resolved_root = workspace_root.expanduser().resolve()
    resolved_path = path.expanduser().resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


__all__ = ["resolve_service_python_package_layout"]
