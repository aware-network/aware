"""Portable declaration scope and selected-source interfaces, never authority.

Workspace owns the original handles, readers and validators. Code consumes these
values only through a host that retains their authenticated callable origins.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol, TypeVar

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes
from .dependency_scope_closure import (
    MAX_BODY_BYTES,
    MAX_EDGES,
    MAX_MODULES,
    MAX_PACKAGES,
    MAX_PATHS,
    MAX_SCOPES,
    DependencyScopeEdge,
)
from .dependency_scope_closure_v2 import DependencyScopeProfileAssociation
from .retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
    _digest,
    _rows,
)
from .semantic_candidates import CodeSemanticCandidateListing, _path

DECLARATION_SCOPE_CONTRACT = "aware.code.retained-declaration-scope.v2"
DEPENDENCY_CLOSURE_CONTRACT_V3 = "aware.code.retained-dependency-scope-closure.v3"
SELECTED_SOURCE_BINDING_CONTRACT = "aware.code.selected-package-source-binding.v1"


def _text(value: str) -> None:
    if type(value) is not str or not value or len(value.encode("utf-8")) > 4096:
        raise ContractViolation("bounded exact text required")


def _profile_key(value: str) -> None:
    _path(value)
    if "/" in value:
        raise ContractViolation("local profile key must be one path component")


def _profile_path(workspace_manifest_path: str, key: str) -> str:
    _profile_key(key)
    _path(workspace_manifest_path)
    directory, separator, filename = workspace_manifest_path.rpartition("/")
    if filename != "aware.workspace.toml":
        raise ContractViolation("owning Workspace manifest path differs")
    prefix = directory + separator if directory else ""
    return f"{prefix}semantic_contract/profiles/{key}/aware.semantic_contract_profile.toml"


@dataclass(frozen=True, slots=True)
class CodeRetainedDeclarationPackage:
    """Complete declared occurrence; no candidate or source-identity claim."""

    module_id: str
    package_id: str
    package_kind: str
    module_manifest_path: str
    package_root: str
    manifest_relative_path: str
    manifest: CodeRetainedScopeBody

    def __post_init__(self) -> None:
        for value in (self.module_id, self.package_id, self.package_kind):
            _text(value)
        _path(self.module_manifest_path)
        if self.package_root != ".":
            _path(self.package_root)
        _path(self.manifest_relative_path)
        if type(self.manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact retained package manifest required")
        self.manifest.__post_init__()
        prefix = "" if self.package_root == "." else self.package_root + "/"
        if self.manifest.relative_path != prefix + self.manifest_relative_path:
            raise ContractViolation("declared package manifest location differs")

    def to_wire(self) -> dict[str, object]:
        return {
            "module_id": self.module_id,
            "package_id": self.package_id,
            "package_kind": self.package_kind,
            "module_manifest_path": self.module_manifest_path,
            "package_root": self.package_root,
            "manifest_relative_path": self.manifest_relative_path,
            "manifest": self.manifest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeRetainedDeclarationScopeProjection:
    repository_binding_ref: str
    observation_digest: ContentDigest
    workspace_manifest: CodeRetainedScopeBody
    modules: tuple[CodeRetainedScopeModule, ...]
    packages: tuple[CodeRetainedDeclarationPackage, ...]

    def __post_init__(self) -> None:
        _text(self.repository_binding_ref)
        _digest(self.observation_digest)
        if type(self.workspace_manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact Workspace declaration body required")
        self.workspace_manifest.__post_init__()
        _rows(self.modules, CodeRetainedScopeModule)
        _rows(self.packages, CodeRetainedDeclarationPackage)
        module_paths: dict[str, str] = {}
        module_keys = []
        bodies = [self.workspace_manifest]
        for module in self.modules:
            module.__post_init__()
            module_keys.append(module.module_id)
            module_paths[module.module_id] = module.manifest.relative_path
            bodies.append(module.manifest)
        if module_keys != sorted(set(module_keys), key=str.encode):
            raise ContractViolation("declaration modules unordered or duplicate")
        if len(set(module_paths.values())) != len(module_paths):
            raise ContractViolation("declaration module paths duplicate")
        keys = []
        for package in self.packages:
            package.__post_init__()
            key = (package.module_id, package.package_id)
            keys.append(key)
            if module_paths.get(package.module_id) != package.module_manifest_path:
                raise ContractViolation("declaration package module differs")
            bodies.append(package.manifest)
        if keys != sorted(set(keys), key=lambda key: (key[0].encode(), key[1].encode())):
            raise ContractViolation("declaration packages unordered or duplicate")
        if sum(len(body.body) for body in bodies) > MAX_BODY_BYTES:
            raise ContractViolation("declaration scope raw body bound")
        by_path: dict[str, CodeRetainedScopeBody] = {}
        by_ref: dict[str, tuple[ContentDigest, bytes]] = {}
        for body in bodies:
            if body.relative_path in by_path and by_path[body.relative_path] != body:
                raise ContractViolation("declaration path substitution")
            content = (body.content_digest, body.body)
            if body.body_ref in by_ref and by_ref[body.body_ref] != content:
                raise ContractViolation("declaration body-ref substitution")
            by_path[body.relative_path] = body
            by_ref[body.body_ref] = content

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": DECLARATION_SCOPE_CONTRACT,
            "repository_binding_ref": self.repository_binding_ref,
            "observation_digest": self.observation_digest.to_wire(),
            "workspace_manifest": self.workspace_manifest.to_wire(),
            "modules": [module.to_wire() for module in self.modules],
            "packages": [package.to_wire() for package in self.packages],
        }


@dataclass(frozen=True, slots=True)
class CodeRetainedDeclarationScopeEntry:
    scope_key: str
    workspace_handle: str
    projection: CodeRetainedDeclarationScopeProjection

    def __post_init__(self) -> None:
        _path(self.scope_key)
        if type(self.workspace_handle) is not str or re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_-]{0,127}", self.workspace_handle, flags=re.ASCII
        ) is None:
            raise ContractViolation("canonical Workspace handle required")
        if type(self.projection) is not CodeRetainedDeclarationScopeProjection:
            raise ContractViolation("exact declaration projection required")
        self.projection.__post_init__()

    def to_wire(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key,
            "workspace_handle": self.workspace_handle,
            "projection": self.projection.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeRetainedLocalProfilePublication:
    owning_scope_key: str
    profile_key: str
    manifest: CodeRetainedScopeBody

    def __post_init__(self) -> None:
        _path(self.owning_scope_key)
        _profile_key(self.profile_key)
        if type(self.manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact local profile body required")
        self.manifest.__post_init__()

    def to_wire(self) -> dict[str, object]:
        return {
            "owning_scope_key": self.owning_scope_key,
            "profile_key": self.profile_key,
            "manifest": self.manifest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeRetainedDependencyScopeClosureV3:
    """Repository plus local publication and imported-edge declaration closure."""

    consumer_scope_key: str
    repository_binding_ref: str
    repository_manifest: CodeRetainedScopeBody
    scopes: tuple[CodeRetainedDeclarationScopeEntry, ...]
    edges: tuple[DependencyScopeEdge, ...]
    local_profiles: tuple[CodeRetainedLocalProfilePublication, ...]
    profile_associations: tuple[DependencyScopeProfileAssociation, ...]

    def __post_init__(self) -> None:
        _path(self.consumer_scope_key)
        _text(self.repository_binding_ref)
        if type(self.repository_manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact repository manifest required")
        self.repository_manifest.__post_init__()
        if self.repository_manifest.relative_path != "aware.repo.toml":
            raise ContractViolation("repository declaration path differs")
        _rows(self.scopes, CodeRetainedDeclarationScopeEntry)
        _rows(self.edges, DependencyScopeEdge)
        _rows(self.local_profiles, CodeRetainedLocalProfilePublication)
        _rows(self.profile_associations, DependencyScopeProfileAssociation)
        if not 0 < len(self.scopes) <= MAX_SCOPES or len(self.edges) > MAX_EDGES:
            raise ContractViolation("declaration closure scope or edge bound")
        scope_keys = [scope.scope_key for scope in self.scopes]
        if scope_keys != sorted(set(scope_keys), key=str.encode):
            raise ContractViolation("declaration scopes unordered or duplicate")
        if self.consumer_scope_key not in scope_keys:
            raise ContractViolation("consumer declaration scope unavailable")
        if len({scope.workspace_handle for scope in self.scopes}) != len(self.scopes):
            raise ContractViolation("Workspace handles duplicate")
        scopes = {scope.scope_key: scope for scope in self.scopes}
        for scope in self.scopes:
            scope.__post_init__()
            if scope.projection.repository_binding_ref != self.repository_binding_ref:
                raise ContractViolation("repository binding differs across scopes")
        if sum(len(scope.projection.modules) for scope in self.scopes) > MAX_MODULES:
            raise ContractViolation("aggregate declaration modules bound")
        if sum(len(scope.projection.packages) for scope in self.scopes) > MAX_PACKAGES:
            raise ContractViolation("aggregate declaration packages bound")
        edge_keys = []
        for edge in self.edges:
            edge.__post_init__()
            edge_keys.append(edge.ordering_key)
            declaring = scopes.get(edge.declaring_scope_key)
            if declaring is None or edge.target_scope_key not in scopes:
                raise ContractViolation("declaration edge scope unavailable")
            manifest = declaring.projection.workspace_manifest
            if (edge.declaration.manifest_relative_path, edge.declaration.manifest_content_digest) != (
                manifest.relative_path, manifest.content_digest
            ):
                raise ContractViolation("edge declaration source differs")
        if edge_keys != sorted(set(edge_keys)) or len({key[:3] for key in edge_keys}) != len(edge_keys):
            raise ContractViolation("declaration edges unordered or duplicate")
        local_keys = []
        for profile in self.local_profiles:
            profile.__post_init__()
            owner = scopes.get(profile.owning_scope_key)
            if owner is None:
                raise ContractViolation("local profile owner unavailable")
            expected_path = _profile_path(
                owner.projection.workspace_manifest.relative_path, profile.profile_key
            )
            if profile.manifest.relative_path != expected_path:
                raise ContractViolation("local profile path differs from owning Workspace")
            local_keys.append((profile.owning_scope_key, profile.profile_key))
        if local_keys != sorted(set(local_keys), key=lambda key: (key[0].encode(), key[1].encode())):
            raise ContractViolation("local profiles unordered or duplicate")
        if len(self.profile_associations) != len(self.edges):
            raise ContractViolation("one imported profile association per edge required")
        local = {key: profile for key, profile in zip(local_keys, self.local_profiles, strict=True)}
        for edge, association in zip(self.edges, self.profile_associations, strict=True):
            association.__post_init__()
            if (
                association.ordering_key != edge.ordering_key
                or association.declaration != edge.declaration
                or edge.profile_key.state != "present"
                or type(edge.profile_key.value) is not str
            ):
                raise ContractViolation("imported profile occurrence differs")
            owner = local.get((edge.target_scope_key, edge.profile_key.value))
            if owner is None or association.manifest != owner.manifest:
                raise ContractViolation("imported profile lacks exact local publication")
        bodies = [self.repository_manifest]
        for scope in self.scopes:
            p = scope.projection
            bodies.extend((p.workspace_manifest, *(m.manifest for m in p.modules), *(q.manifest for q in p.packages)))
        bodies.extend(p.manifest for p in self.local_profiles)
        bodies.extend(p.manifest for p in self.profile_associations)
        if len(bodies) > MAX_PATHS or sum(len(body.body) for body in bodies) > MAX_BODY_BYTES:
            raise ContractViolation("declaration closure body bound")
        by_ref: dict[str, tuple[ContentDigest, bytes]] = {}
        for body in bodies:
            content = (body.content_digest, body.body)
            if body.body_ref in by_ref and by_ref[body.body_ref] != content:
                raise ContractViolation("declaration closure body-ref substitution")
            by_ref[body.body_ref] = content
        for scope in self.scopes:
            projection = scope.projection
            scoped_bodies = (
                projection.workspace_manifest,
                *(module.manifest for module in projection.modules),
                *(package.manifest for package in projection.packages),
                *(profile.manifest for profile in self.local_profiles if profile.owning_scope_key == scope.scope_key),
                *(association.manifest for association in self.profile_associations if association.target_scope_key == scope.scope_key),
            )
            by_path: dict[str, CodeRetainedScopeBody] = {}
            for body in scoped_bodies:
                if body.relative_path in by_path and by_path[body.relative_path] != body:
                    raise ContractViolation("scoped declaration path substitution")
                by_path[body.relative_path] = body

    def to_wire(self) -> dict[str, object]:
        from .dependency_scope_closure_codec import _wire

        return {
            "contract": DEPENDENCY_CLOSURE_CONTRACT_V3,
            "consumer_scope_key": self.consumer_scope_key,
            "repository_binding_ref": self.repository_binding_ref,
            "repository_manifest": self.repository_manifest.to_wire(),
            "scopes": [scope.to_wire() for scope in self.scopes],
            "edges": _wire(self.edges),
            "local_profiles": [profile.to_wire() for profile in self.local_profiles],
            "profile_associations": [
                {
                    "declaring_scope_key": a.declaring_scope_key,
                    "declaration": _wire(a.declaration),
                    "target_scope_key": a.target_scope_key,
                    "manifest": a.manifest.to_wire(),
                }
                for a in self.profile_associations
            ],
        }

    @property
    def closure_digest(self) -> ContentDigest:
        from .retained_declaration_scope_codec import declaration_closure_payload_bytes

        return ContentDigest.of_bytes(declaration_closure_payload_bytes(self))


@dataclass(frozen=True, slots=True)
class CodeDeclarationScopeExpectation:
    repository_binding_ref: str
    parent_identity: str
    process_id: int
    operation_identity: str
    epoch_identity: str

    def __post_init__(self) -> None:
        for value in (
            self.repository_binding_ref,
            self.parent_identity,
            self.operation_identity,
            self.epoch_identity,
        ):
            _text(value)
        if type(self.process_id) is not int or self.process_id <= 0:
            raise ContractViolation("exact positive process identity required")

    def to_wire(self) -> dict[str, object]:
        return {
            "repository_binding_ref": self.repository_binding_ref,
            "parent_identity": self.parent_identity,
            "process_id": self.process_id,
            "operation_identity": self.operation_identity,
            "epoch_identity": self.epoch_identity,
        }


@dataclass(frozen=True, slots=True)
class CodeSelectedPackageSourceExpectation:
    declaration: CodeDeclarationScopeExpectation
    closure_digest: ContentDigest
    scope_key: str
    module_id: str
    package_id: str
    manifest_relative_path: str
    manifest_content_digest: ContentDigest
    source_identity_digest: ContentDigest

    def __post_init__(self) -> None:
        if type(self.declaration) is not CodeDeclarationScopeExpectation:
            raise ContractViolation("exact declaration context required")
        self.declaration.__post_init__()
        for value in (self.closure_digest, self.manifest_content_digest, self.source_identity_digest):
            _digest(value)
        _path(self.scope_key)
        for value in (self.module_id, self.package_id):
            _text(value)
        _path(self.manifest_relative_path)

    def to_wire(self) -> dict[str, object]:
        return {
            "declaration": self.declaration.to_wire(),
            "closure_digest": self.closure_digest.to_wire(),
            "scope_key": self.scope_key,
            "module_id": self.module_id,
            "package_id": self.package_id,
            "manifest_relative_path": self.manifest_relative_path,
            "manifest_content_digest": self.manifest_content_digest.to_wire(),
            "source_identity_digest": self.source_identity_digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeSelectedPackageSourceBinding:
    expectation: CodeSelectedPackageSourceExpectation
    candidates: CodeSemanticCandidateListing

    def __post_init__(self) -> None:
        if type(self.expectation) is not CodeSelectedPackageSourceExpectation:
            raise ContractViolation("exact selected source expectation required")
        self.expectation.__post_init__()
        if type(self.candidates) is not CodeSemanticCandidateListing:
            raise ContractViolation("exact selected candidates required")
        self.candidates.__post_init__()
        if self.candidates.source_identity_digest != self.expectation.source_identity_digest:
            raise ContractViolation("selected candidate source identity differs")
        matches = [
            candidate for candidate in self.candidates.candidates
            if candidate.relative_path == self.expectation.manifest_relative_path
        ]
        if len(matches) != 1 or matches[0].content_digest != self.expectation.manifest_content_digest:
            raise ContractViolation("selected manifest candidate differs")

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": SELECTED_SOURCE_BINDING_CONTRACT,
            "expectation": self.expectation.to_wire(),
            "candidates": self.candidates.to_wire(),
        }

    @property
    def binding_digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self.to_wire()))


_Snapshot = TypeVar("_Snapshot", contravariant=True)


class RetainedDeclarationScopeReader(Protocol[_Snapshot]):
    def read_declaration_scope(self, handle: _Snapshot) -> CodeRetainedDependencyScopeClosureV3: ...


class RetainedDeclarationScopeValidator(Protocol[_Snapshot]):
    def validate_declaration_scope(
        self,
        handle: _Snapshot,
        *,
        expectation: CodeDeclarationScopeExpectation,
        closure_digest: ContentDigest | None = None,
    ) -> None: ...


class SelectedPackageSourceReader(Protocol[_Snapshot]):
    def read_selected_package_source(self, handle: _Snapshot) -> CodeSelectedPackageSourceBinding: ...


class SelectedPackageSourceValidator(Protocol[_Snapshot]):
    def validate_selected_package_source(
        self,
        handle: _Snapshot,
        *,
        expectation: CodeSelectedPackageSourceExpectation,
        binding_digest: ContentDigest | None = None,
    ) -> None: ...


__all__ = [
    "CodeDeclarationScopeExpectation",
    "CodeRetainedDeclarationPackage",
    "CodeRetainedDeclarationScopeEntry",
    "CodeRetainedDeclarationScopeProjection",
    "CodeRetainedDependencyScopeClosureV3",
    "CodeRetainedLocalProfilePublication",
    "CodeSelectedPackageSourceBinding",
    "CodeSelectedPackageSourceExpectation",
    "RetainedDeclarationScopeReader",
    "RetainedDeclarationScopeValidator",
    "SelectedPackageSourceReader",
    "SelectedPackageSourceValidator",
]
