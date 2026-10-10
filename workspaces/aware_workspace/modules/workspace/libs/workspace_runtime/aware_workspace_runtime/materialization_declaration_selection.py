"""Detached root preselection from one retained v3 declaration closure.

These candidates are not source, Code, catalog, or execution admissions. The
original Workspace issuer must validate the closure and bind selected sources
before a caller can use an occurrence for semantic execution.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import PurePosixPath

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV3,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDeclarationPackage,
    CodeRetainedDependencyScopeClosureV3,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeModule,
)

from .materialization_selection import WorkspaceMaterializationSelectionProposal
from .source_observation_io import SourceObservationUnavailable


@dataclass(frozen=True, slots=True)
class WorkspaceDeclaredMaterializationRoot:
    """A declared occurrence address; no executable package authority."""

    workspace_manifest_path: str
    module_id: str
    package_id: str
    semantic_package_name: str
    semantic_version: str

    @property
    def ordering_key(self) -> tuple[bytes, bytes, bytes]:
        return (
            self.workspace_manifest_path.encode(),
            self.module_id.encode(),
            self.package_id.encode(),
        )


def _module_roots(
    *,
    scope_key: str,
    module: CodeRetainedScopeModule,
    packages: tuple[CodeRetainedDeclarationPackage, ...],
) -> tuple[WorkspaceDeclaredMaterializationRoot, ...]:
    """Interpret one retained module identically for broad and exact selection."""
    meaning = parse_module_manifest(module.manifest.body)
    if type(meaning) is not AwareModuleSpecV3:
        raise SourceObservationUnavailable("materialization_module_v3_required")
    declarations = {row.package_id: row for row in meaning.package_declarations}
    authored = {package.id: package for package in meaning.packages}
    package_ids = {package.package_id for package in packages}
    if set(declarations) != package_ids or set(authored) != package_ids:
        raise SourceObservationUnavailable("materialization_package_set_changed")
    roots: list[WorkspaceDeclaredMaterializationRoot] = []
    for package in packages:
        authored_package = authored[package.package_id]
        if (
            authored_package.kind != package.package_kind
            or package.module_manifest_path != module.manifest.relative_path
            or package.manifest.relative_path != str(
                PurePosixPath(module.manifest.relative_path).parent
                / authored_package.manifest
            )
        ):
            raise SourceObservationUnavailable(
                "materialization_package_correspondence_changed"
            )
        declared = declarations[package.package_id]
        name = declared.occurrence.semantic_package_name
        version = declared.occurrence.semantic_version
        if name.state != "present":
            continue
        if (
            not declared.occurrence_declared
            or version.state != "present"
            or type(name.value) is not str
            or type(version.value) is not str
        ):
            raise SourceObservationUnavailable("materialization_occurrence_incomplete")
        roots.append(
            WorkspaceDeclaredMaterializationRoot(
                scope_key, module.module_id, package.package_id,
                name.value, version.value,
            )
        )
    return tuple(roots)


def select_declared_materialization_roots(
    *,
    closure: CodeRetainedDependencyScopeClosureV3,
    repository_handle: str,
    selection: WorkspaceMaterializationSelectionProposal,
) -> tuple[WorkspaceDeclaredMaterializationRoot, ...]:
    """Expand four human-facing scopes without issuing membership authority."""

    if type(closure) is not CodeRetainedDependencyScopeClosureV3:
        raise TypeError("exact retained v3 declaration closure required")
    if type(selection) is not WorkspaceMaterializationSelectionProposal:
        raise TypeError("exact materialization selection required")
    closure.__post_init__()
    selection.__post_init__()
    if type(repository_handle) is not str or not repository_handle:
        raise TypeError("authenticated repository handle required")

    scopes = {scope.scope_key: scope for scope in closure.scopes}
    selected: dict[
        tuple[str, str, str], WorkspaceDeclaredMaterializationRoot
    ] = {}
    cache: dict[str, tuple[WorkspaceDeclaredMaterializationRoot, ...]] = {}

    def roots_for(scope_key: str) -> tuple[WorkspaceDeclaredMaterializationRoot, ...]:
        cached = cache.get(scope_key)
        if cached is not None:
            return cached
        scope = scopes[scope_key]
        projection = scope.projection
        roots: list[WorkspaceDeclaredMaterializationRoot] = []
        for module in projection.modules:
            roots.extend(_module_roots(
                scope_key=scope_key,
                module=module,
                packages=tuple(
                    package for package in projection.packages
                    if package.module_id == module.module_id
                ),
            ))
        result = tuple(sorted(roots, key=lambda root: root.ordering_key))
        cache[scope_key] = result
        return result

    for selector in selection.selectors:
        kind = selector.selector_kind
        ref = selector.selector_ref
        if kind == "package":
            matches = tuple(
                root
                for root in roots_for(closure.consumer_scope_key)
                if root.semantic_package_name == ref
            )
            if len(matches) > 1:
                raise SourceObservationUnavailable("materialization_package_ambiguous")
        elif kind == "module":
            matches = tuple(
                root
                for root in roots_for(closure.consumer_scope_key)
                if root.module_id == ref
            )
        elif kind == "workspace":
            matches = tuple(
                root
                for scope in closure.scopes
                if scope.workspace_handle == ref
                for root in roots_for(scope.scope_key)
            )
        elif kind == "repository":
            # A Code declaration closure includes only the consumer's reachable
            # provider imports. Repository selection must not silently treat
            # that subset as the complete repository.
            try:
                repository = tomllib.loads(
                    closure.repository_manifest.body.decode("utf-8")
                )
                declared = repository["workspaces"]
            except (KeyError, TypeError, UnicodeError, ValueError) as error:
                raise SourceObservationUnavailable(
                    "materialization_repository_declaration_invalid"
                ) from error
            if type(declared) is not list or len(declared) != len(closure.scopes):
                raise SourceObservationUnavailable(
                    "materialization_repository_scope_incomplete"
                )
            matches = (
                tuple(
                    root
                    for scope in closure.scopes
                    for root in roots_for(scope.scope_key)
                )
                if ref == repository_handle
                else ()
            )
        else:
            raise SourceObservationUnavailable("materialization_selector_unsupported")
        if not matches:
            raise SourceObservationUnavailable("materialization_selector_unavailable")
        for root in matches:
            selected[
                root.workspace_manifest_path, root.module_id, root.package_id
            ] = root

    roots = tuple(sorted(selected.values(), key=lambda root: root.ordering_key))
    names: set[tuple[str, str]] = set()
    for root in roots:
        identity = (root.semantic_package_name, root.semantic_version)
        if identity in names:
            raise SourceObservationUnavailable(
                "materialization_package_coordinate_ambiguous"
            )
        names.add(identity)
    return roots


def select_exact_declared_materialization_root(
    *,
    closure: CodeRetainedDependencyScopeClosureV3,
    workspace_handle: str,
    module_id: str,
    package_id: str,
) -> WorkspaceDeclaredMaterializationRoot:
    """Inspect one retained address without parsing unrelated module meaning.

    This is a declaration candidate only. The original Workspace issuer must
    revalidate the observation and bind the selected source separately.
    """
    if type(closure) is not CodeRetainedDependencyScopeClosureV3:
        raise TypeError("exact retained v3 declaration closure required")
    closure.__post_init__()
    for value in (workspace_handle, module_id, package_id):
        if type(value) is not str or not value:
            raise TypeError("exact nonempty package address fields required")

    scopes = tuple(
        scope for scope in closure.scopes
        if scope.workspace_handle == workspace_handle
    )
    if len(scopes) != 1:
        raise SourceObservationUnavailable("materialization_workspace_unavailable")
    scope = scopes[0]
    projection = scope.projection
    modules = tuple(
        module for module in projection.modules if module.module_id == module_id
    )
    packages = tuple(
        package for package in projection.packages
        if package.module_id == module_id
    )
    selected = tuple(
        package for package in packages if package.package_id == package_id
    )
    if len(modules) != 1 or len(selected) != 1:
        raise SourceObservationUnavailable("materialization_package_unavailable")

    roots = _module_roots(
        scope_key=scope.scope_key,
        module=modules[0],
        packages=packages,
    )
    matches = tuple(root for root in roots if root.package_id == package_id)
    if len(matches) != 1:
        raise SourceObservationUnavailable("materialization_occurrence_unavailable")
    return matches[0]
