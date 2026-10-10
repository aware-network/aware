"""Portable dependency scopes; all membership and entitlement remain contextual."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import ContentDigest, ContractViolation, _token
from .retained_scope_interfaces import CodeRetainedScopeProjection, _digest
from .semantic_candidates import _path

CONTRACT = "aware.code.retained-dependency-scope-closure.v1"
MAX_SCOPES = 32
MAX_EDGES = 256
MAX_MODULES = 4096
MAX_PACKAGES = 16384
MAX_PATHS = 65536
MAX_BODY_BYTES = 64 * 1024 * 1024
MAX_CANONICAL_BYTES = 128 * 1024 * 1024


def _fail(message):
    raise ContractViolation(message)


def _text(value):
    if type(value) is not str or not value or len(value.encode("utf-8")) > 4096:
        _fail("bounded exact edge text required")


def _rows(value, kind, limit):
    if type(value) is not tuple or len(value) > limit:
        _fail("closure tuple bound/type differs")
    for row in value:
        if type(row) is not kind:
            _fail("exact closure row required")
        row.__post_init__()


@dataclass(frozen=True, slots=True)
class DependencyScopeRestriction:
    state: str
    value: str | tuple[str, ...] | None = None

    def __post_init__(self):
        if type(self.state) is not str or self.state not in ("unavailable", "absent", "present"):
            _fail("invalid restriction state")
        if self.state != "present":
            if self.value is not None:
                _fail("nonpresent restriction has value")
        elif type(self.value) is str:
            _text(self.value)
        elif type(self.value) is tuple:
            if len(self.value) > 256:
                _fail("provider restriction bound")
            for key in self.value:
                _text(key)
                _token(key, "provider key")
            if list(self.value) != sorted(set(self.value), key=lambda k: k.encode("utf-8")):
                _fail("provider restrictions must be unique and ordered")
        else:
            _fail("present restriction requires exact value")


@dataclass(frozen=True, slots=True)
class DependencyScopeDeclaration:
    manifest_relative_path: str
    manifest_content_digest: ContentDigest
    dependency_index: int
    profile_package_index: int

    def __post_init__(self):
        _path(self.manifest_relative_path)
        _digest(self.manifest_content_digest)
        for index in (self.dependency_index, self.profile_package_index):
            if type(index) is not int or index < 0:
                _fail("nonnegative exact declaration index required")


@dataclass(frozen=True, slots=True)
class DependencyScopeEntry:
    scope_key: str
    workspace_handle: str
    projection: CodeRetainedScopeProjection

    def __post_init__(self):
        _path(self.scope_key)
        if type(self.workspace_handle) is not str or re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_-]{0,127}", self.workspace_handle, flags=re.ASCII
        ) is None:
            _fail("canonical qualified Workspace handle required")
        if type(self.projection) is not CodeRetainedScopeProjection:
            _fail("exact original scope projection required")
        self.projection.__post_init__()


@dataclass(frozen=True, slots=True)
class DependencyScopeEdge:
    declaring_scope_key: str
    target_scope_key: str
    declaration: DependencyScopeDeclaration
    dependency_id: str
    dependency_kind: str
    dependency_source: str
    channel: DependencyScopeRestriction
    revision: DependencyScopeRestriction
    profile_package_ref: str
    profile_key: DependencyScopeRestriction
    semantic_contract_provider_keys: DependencyScopeRestriction

    def __post_init__(self):
        _path(self.declaring_scope_key)
        _path(self.target_scope_key)
        if self.declaring_scope_key == self.target_scope_key:
            _fail("self dependency edge")
        if type(self.declaration) is not DependencyScopeDeclaration:
            _fail("exact declaration witness required")
        self.declaration.__post_init__()
        for text in (self.dependency_id, self.dependency_kind, self.dependency_source, self.profile_package_ref):
            _text(text)
        for name in ("channel", "revision", "profile_key", "semantic_contract_provider_keys"):
            tag = getattr(self, name)
            if type(tag) is not DependencyScopeRestriction:
                _fail("exact restriction required")
            tag.__post_init__()
            kind = tuple if name == "semantic_contract_provider_keys" else str
            if tag.state == "present" and type(tag.value) is not kind:
                _fail("restriction role value type differs")

    @property
    def ordering_key(self):
        return (self.declaring_scope_key.encode(), self.declaration.dependency_index,
                self.declaration.profile_package_index, self.target_scope_key.encode())


@dataclass(frozen=True, slots=True)
class CodeRetainedDependencyScopeClosure:
    consumer_scope_key: str
    scopes: tuple[DependencyScopeEntry, ...]
    edges: tuple[DependencyScopeEdge, ...]

    def __post_init__(self):
        _path(self.consumer_scope_key)
        _rows(self.scopes, DependencyScopeEntry, MAX_SCOPES)
        _rows(self.edges, DependencyScopeEdge, MAX_EDGES)
        keys = [s.scope_key for s in self.scopes]
        if not keys or keys != sorted(set(keys), key=lambda k: k.encode()):
            _fail("scopes must be nonempty unique and ordered")
        if self.consumer_scope_key not in keys:
            _fail("consumer scope absent")
        by_key = {s.scope_key: s for s in self.scopes}
        modules = sum(len(s.projection.modules) for s in self.scopes)
        packages = sum(len(s.projection.packages) for s in self.scopes)
        if modules > MAX_MODULES or packages > MAX_PACKAGES or len(keys) + modules + packages > MAX_PATHS:
            _fail("aggregate closure count bound")
        size = sum(len(body.body) for s in self.scopes for body in (
            s.projection.workspace_manifest,
            *(m.manifest for m in s.projection.modules),
            *(p.manifest for p in s.projection.packages),
        ))
        if size > MAX_BODY_BYTES:
            _fail("aggregate closure body bound")
        order = [e.ordering_key for e in self.edges]
        if order != sorted(set(order)) or len({k[:3] for k in order}) != len(order):
            _fail("duplicate or unordered declaration occurrences")
        for edge in self.edges:
            if edge.declaring_scope_key not in by_key or edge.target_scope_key not in by_key:
                _fail("edge endpoint absent")
            body = by_key[edge.declaring_scope_key].projection.workspace_manifest
            if (edge.declaration.manifest_relative_path, edge.declaration.manifest_content_digest) != (
                body.relative_path, body.content_digest
            ):
                _fail("edge declaration manifest differs")
        # Reachability/cycles and grants are policy, not portable authority.

    @property
    def closure_digest(self) -> ContentDigest:
        from .dependency_scope_closure_codec import closure_payload_bytes
        return ContentDigest.of_bytes(closure_payload_bytes(self))
