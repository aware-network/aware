"""V2 portable profile associations; original source authority remains external."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ContentDigest, ContractViolation
from .dependency_scope_closure import (
    MAX_BODY_BYTES,
    MAX_EDGES,
    MAX_PATHS,
    CodeRetainedDependencyScopeClosure,
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeEntry,
)
from .retained_scope_interfaces import CodeRetainedScopeBody
from .semantic_candidates import _path

CONTRACT_V2 = "aware.code.retained-dependency-scope-closure.v2"


@dataclass(frozen=True, slots=True)
class DependencyScopeProfileAssociation:
    declaring_scope_key: str
    declaration: DependencyScopeDeclaration
    target_scope_key: str
    manifest: CodeRetainedScopeBody

    def __post_init__(self):
        _path(self.declaring_scope_key)
        _path(self.target_scope_key)
        if type(self.declaration) is not DependencyScopeDeclaration:
            raise ContractViolation("exact profile declaration witness required")
        self.declaration.__post_init__()
        if type(self.manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact retained profile body required")
        self.manifest.__post_init__()

    @property
    def ordering_key(self):
        return (
            self.declaring_scope_key.encode(),
            self.declaration.dependency_index,
            self.declaration.profile_package_index,
            self.target_scope_key.encode(),
        )


def scope_bodies(scope):
    yield scope.projection.workspace_manifest
    yield from (m.manifest for m in scope.projection.modules)
    yield from (p.manifest for p in scope.projection.packages)


@dataclass(frozen=True, slots=True)
class CodeRetainedDependencyScopeClosureV2:
    consumer_scope_key: str
    scopes: tuple[DependencyScopeEntry, ...]
    edges: tuple[DependencyScopeEdge, ...]
    profile_associations: tuple[DependencyScopeProfileAssociation, ...]

    def __post_init__(self):
        # Reuse v1 structural laws without converting or restamping v1 evidence.
        CodeRetainedDependencyScopeClosure(
            self.consumer_scope_key, self.scopes, self.edges
        )
        rows = self.profile_associations
        if (
            type(rows) is not tuple
            or len(rows) != len(self.edges)
            or len(rows) > MAX_EDGES
        ):
            raise ContractViolation("one bounded profile association per edge required")
        for row, edge in zip(rows, self.edges, strict=True):
            if type(row) is not DependencyScopeProfileAssociation:
                raise ContractViolation("exact profile association required")
            row.__post_init__()
            if (
                row.ordering_key != edge.ordering_key
                or row.declaration != edge.declaration
            ):
                raise ContractViolation(
                    "profile association differs from original edge witness"
                )
        size = 0
        count = 0
        for scope in self.scopes:
            refs = {}
            paths = {}
            bodies = (
                *scope_bodies(scope),
                *(a.manifest for a in rows if a.target_scope_key == scope.scope_key),
            )
            for body in bodies:
                size += len(body.body)
                count += 1
                if size > MAX_BODY_BYTES or count > MAX_PATHS:
                    raise ContractViolation("aggregate profile closure bound")
                content = (body.content_digest, body.body)
                identity = (body.body_ref, *content)
                if body.body_ref in refs and refs[body.body_ref] != content:
                    raise ContractViolation("scope body reference content differs")
                if (
                    body.relative_path in paths
                    and paths[body.relative_path] != identity
                ):
                    raise ContractViolation("scope path body identity differs")
                refs[body.body_ref] = content
                paths[body.relative_path] = identity

    @property
    def closure_digest(self) -> ContentDigest:
        from .dependency_scope_closure_codec_v2 import closure_payload_bytes_v2

        return ContentDigest.of_bytes(closure_payload_bytes_v2(self))
