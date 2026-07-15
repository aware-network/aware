from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import (
    SemanticScopeMaterializationDependency,
    SemanticScopeProvider,
    SemanticScopeRegistry,
    SemanticScopeResolution,
)
from aware_code.semantic_scope.schemas import (
    SemanticScopePayloadObject,
    SemanticScopePayloadValue,
)
from aware_interface.pane_consumer_scope import (
    InterfaceDependencyScope,
    PaneConsumerScope,
    WorkspacePaneCatalogEntry,
    WorkspacePaneCatalogResolution,
    load_interface_dependency_scope,
    load_workspace_pane_catalog,
    load_workspace_pane_consumer_scopes,
)


PackageKind = Literal["interface", "pane"]
INTERFACE_SEMANTIC_SCOPE_KEY = "aware_interface.semantic_scope"


@dataclass(frozen=True, slots=True)
class InterfaceSemanticScope:
    manifest_path: Path
    package_kind: PackageKind
    interface_dependency_scope: InterfaceDependencyScope | None = None
    pane_catalog_resolution: WorkspacePaneCatalogResolution | None = None
    pane_consumer_scopes_by_pane: dict[str, tuple[PaneConsumerScope, ...]] = field(default_factory=dict)

    def pane_catalog_entry(self, *, pane_name: str) -> WorkspacePaneCatalogEntry | None:
        if self.pane_catalog_resolution is None:
            return None
        return self.pane_catalog_resolution.pane_catalog.get(pane_name.casefold())

    def pane_consumer_scopes(self, *, pane_name: str) -> tuple[PaneConsumerScope, ...]:
        return self.pane_consumer_scopes_by_pane.get(pane_name.casefold(), ())


def _workspace_relative_path_or_abs(*, path: Path, workspace_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(workspace_root.resolve()).as_posix()
    except Exception:
        return resolved.as_posix()


def _interface_dependency_scope_payload(
    *,
    dependency_scope: InterfaceDependencyScope | None,
    workspace_root: Path,
) -> SemanticScopePayloadObject | None:
    if dependency_scope is None:
        return None
    return {
        "interfacePackageName": dependency_scope.interface_package_name,
        "interfaceManifestRelativePath": _workspace_relative_path_or_abs(
            path=dependency_scope.manifest_path,
            workspace_root=workspace_root,
        ),
        "declaredExperiencePackageNames": list(
            dependency_scope.declared_experience_package_names
        ),
        "resolvedExperienceNames": list(sorted(dependency_scope.experience_catalog)),
    }


def _pane_catalog_resolution_payload(
    *,
    pane_catalog_resolution: WorkspacePaneCatalogResolution | None,
) -> SemanticScopePayloadObject | None:
    if pane_catalog_resolution is None:
        return None
    return {
        "declaredWorkspace": pane_catalog_resolution.declared_workspace,
        "paneCatalog": {
            pane_name: {
                "viewRefs": list(entry.view_refs),
            }
            for pane_name, entry in sorted(pane_catalog_resolution.pane_catalog.items())
        },
    }


def _pane_consumer_scope_payload(
    *,
    pane_name: str,
    scopes: tuple[PaneConsumerScope, ...],
    workspace_root: Path,
) -> SemanticScopePayloadObject:
    return {
        "paneName": pane_name,
        "consumerCount": len(scopes),
        "consumerScopes": [
            {
                "paneName": pane_name,
                "interfaceName": scope.interface_name,
                "interfacePackageName": scope.interface_package_name,
                "interfaceManifestRelativePath": _workspace_relative_path_or_abs(
                    path=scope.manifest_path,
                    workspace_root=workspace_root,
                ),
                "declaredExperiencePackageNames": list(
                    scope.declared_experience_package_names
                ),
            }
            for scope in scopes
        ],
    }


def _interface_semantic_scope_payload(
    *,
    scope: InterfaceSemanticScope,
    code_package: CodePackageInfo,
    workspace_root: Path,
) -> SemanticScopePayloadObject:
    payload: dict[str, SemanticScopePayloadValue] = {
        "packageKind": scope.package_kind,
        "manifestRelativePath": _workspace_relative_path_or_abs(
            path=scope.manifest_path,
            workspace_root=workspace_root,
        ),
        "interfaceDependency": _interface_dependency_scope_payload(
            dependency_scope=scope.interface_dependency_scope,
            workspace_root=workspace_root,
        ),
        "paneCatalog": _pane_catalog_resolution_payload(
            pane_catalog_resolution=scope.pane_catalog_resolution,
        ),
    }
    pane_name = str(code_package.metadata.get("pane_name") or "").strip()
    if scope.package_kind == "pane" and pane_name:
        payload["paneConsumers"] = _pane_consumer_scope_payload(
            pane_name=pane_name,
            scopes=scope.pane_consumer_scopes(pane_name=pane_name),
            workspace_root=workspace_root,
        )
    else:
        payload["paneConsumers"] = None
    return payload


def _interface_materialization_dependencies(
    *,
    scope: InterfaceSemanticScope,
    code_package: CodePackageInfo,
    workspace_root: Path,
) -> tuple[SemanticScopeMaterializationDependency, ...]:
    source_ref = _workspace_relative_path_or_abs(
        path=scope.manifest_path,
        workspace_root=workspace_root,
    )
    dependencies: list[SemanticScopeMaterializationDependency] = []

    def add_experience(package_name: str) -> None:
        dependencies.append(
            SemanticScopeMaterializationDependency(
                package_name=package_name,
                provider_key="aware_experience",
                semantic_owner="aware_experience.provider",
                manifest_kind="aware_experience_toml",
                dependency_kind="projection_experience",
                semantic_package_family="experience",
                semantic_package_kind="experience_package",
                semantic_package_name=package_name,
                source_refs=(source_ref,),
                reason=(
                    "Interface semantic materialization requires declared "
                    "Experience packages before view refs can resolve."
                ),
            )
        )

    if scope.interface_dependency_scope is not None:
        for package_name in (
            scope.interface_dependency_scope.declared_experience_package_names
        ):
            add_experience(package_name)

    pane_name = str(code_package.metadata.get("pane_name") or "").strip()
    if scope.package_kind == "pane" and pane_name:
        for consumer_scope in scope.pane_consumer_scopes(pane_name=pane_name):
            for package_name in consumer_scope.declared_experience_package_names:
                add_experience(package_name)

    deduped: list[SemanticScopeMaterializationDependency] = []
    seen: set[tuple[str | None, str, str]] = set()
    for dependency in dependencies:
        key = (
            dependency.provider_key,
            dependency.dependency_kind,
            dependency.package_name,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(dependency)
    return tuple(deduped)


def _empty_interface_dependency_scope(*, manifest_path: Path) -> InterfaceDependencyScope:
    return InterfaceDependencyScope(
        interface_package_name="",
        manifest_path=manifest_path.resolve(),
        declared_experience_package_names=(),
        experience_catalog={},
    )


def load_interface_semantic_scope(*, manifest_path: Path) -> InterfaceSemanticScope:
    resolved_manifest_path = manifest_path.resolve()
    if resolved_manifest_path.name == "aware.interface.toml":
        try:
            dependency_scope = load_interface_dependency_scope(manifest_path=resolved_manifest_path)
        except Exception:
            dependency_scope = _empty_interface_dependency_scope(manifest_path=resolved_manifest_path)
        pane_catalog_resolution = load_workspace_pane_catalog(start=resolved_manifest_path.parent)
        return InterfaceSemanticScope(
            manifest_path=resolved_manifest_path,
            package_kind="interface",
            interface_dependency_scope=dependency_scope,
            pane_catalog_resolution=pane_catalog_resolution,
        )

    if resolved_manifest_path.name == "aware.pane.toml":
        return InterfaceSemanticScope(
            manifest_path=resolved_manifest_path,
            package_kind="pane",
            pane_consumer_scopes_by_pane=load_workspace_pane_consumer_scopes(
                start=resolved_manifest_path.parent
            ),
        )

    raise ValueError(f"Unsupported interface semantic scope manifest: {resolved_manifest_path}")


class _InterfaceSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "aware_interface"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return (INTERFACE_SEMANTIC_SCOPE_KEY,)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        manifest_kind = str(code_package.metadata.get("manifest_kind") or "").strip()
        if manifest_kind not in {"aware_interface_toml", "aware_pane_toml"}:
            return ()

        manifest_path = (workspace_root / code_package.manifest_path).resolve()
        try:
            scope = load_interface_semantic_scope(manifest_path=manifest_path)
        except Exception:
            return ()

        return (
            SemanticScopeResolution(
                scope_key=INTERFACE_SEMANTIC_SCOPE_KEY,
                provider_key=self.provider_key,
                payload=_interface_semantic_scope_payload(
                    scope=scope,
                    code_package=code_package,
                    workspace_root=workspace_root,
                ),
                materialization_dependencies=_interface_materialization_dependencies(
                    scope=scope,
                    code_package=code_package,
                    workspace_root=workspace_root,
                ),
                runtime_value=scope,
            ),
        )


_PROVIDER = _InterfaceSemanticScopeProvider()


def register_semantic_scope_providers() -> None:
    SemanticScopeRegistry.register(_PROVIDER)


__all__ = [
    "InterfaceSemanticScope",
    "INTERFACE_SEMANTIC_SCOPE_KEY",
    "PackageKind",
    "load_interface_semantic_scope",
    "register_semantic_scope_providers",
]
