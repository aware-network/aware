"""Portable complete-scope data and consumer signatures, never authority.

Only the lifecycle-authenticated original reader/validator can bind these values
to an opaque owner snapshot. No Workspace imports or source parsing belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes
from .retained_input_projections import _text
from .semantic_candidates import _path

RETAINED_SCOPE_CONTRACT = "aware.code.retained-scope-projection.v1"
MAX_SCOPE_ITEMS = 16_384
MAX_SCOPE_BODY_BYTES = 16_777_216
MAX_SCOPE_TOTAL_BYTES = 67_108_864


def _digest(value: ContentDigest) -> None:
    if type(value) is not ContentDigest:
        raise ContractViolation("exact scope digest required")
    value.__post_init__()


def _rows(value: tuple, expected: type) -> None:
    if type(value) is not tuple or len(value) > MAX_SCOPE_ITEMS:
        raise ContractViolation("scope tuple type or count differs")
    if any(type(row) is not expected for row in value):
        raise ContractViolation("exact scope row type required")


@dataclass(frozen=True, slots=True)
class CodeRetainedScopeBody:
    """Observation-root-relative coordinate and exact raw bytes, not a semantic value."""

    relative_path: str
    body_ref: str
    content_digest: ContentDigest
    body: bytes

    def __post_init__(self) -> None:
        _path(self.relative_path)
        _text(self.body_ref)
        _digest(self.content_digest)
        if type(self.body) is not bytes or len(self.body) > MAX_SCOPE_BODY_BYTES:
            raise ContractViolation("scope body type or bound differs")
        if ContentDigest.of_bytes(self.body) != self.content_digest:
            raise ContractViolation("scope body digest differs")

    def to_wire(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "body_ref": self.body_ref,
            "content_digest": self.content_digest.to_wire(),
            "size_bytes": len(self.body),
            "body_hex": self.body.hex(),
        }


@dataclass(frozen=True, slots=True)
class CodeRetainedScopeModule:
    module_id: str
    manifest: CodeRetainedScopeBody

    def __post_init__(self) -> None:
        _text(self.module_id)
        if type(self.manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact module manifest required")
        self.manifest.__post_init__()

    def to_wire(self) -> dict[str, object]:
        return {"module_id": self.module_id, "manifest": self.manifest.to_wire()}


@dataclass(frozen=True, slots=True)
class CodeRetainedScopePackage:
    module_id: str
    package_id: str
    package_kind: str
    module_manifest_path: str
    package_root: str
    manifest_relative_path: str
    source_identity_digest: ContentDigest
    manifest: CodeRetainedScopeBody

    def __post_init__(self) -> None:
        for value in (self.module_id, self.package_id, self.package_kind):
            _text(value)
        _path(self.module_manifest_path)
        if self.package_root != ".":
            _path(self.package_root)
        _path(self.manifest_relative_path)
        _digest(self.source_identity_digest)
        if type(self.manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact package manifest required")
        self.manifest.__post_init__()
        prefix = "" if self.package_root == "." else self.package_root + "/"
        if self.manifest.relative_path != prefix + self.manifest_relative_path:
            raise ContractViolation("scope package manifest location differs")

    def to_wire(self) -> dict[str, object]:
        return {
            "module_id": self.module_id,
            "package_id": self.package_id,
            "package_kind": self.package_kind,
            "module_manifest_path": self.module_manifest_path,
            "package_root": self.package_root,
            "manifest_relative_path": self.manifest_relative_path,
            "source_identity_digest": self.source_identity_digest.to_wire(),
            "manifest": self.manifest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeRetainedScopeProjection:
    """Complete detached data, including nonparticipants; completeness is contextual."""

    repository_binding_ref: str
    observation_digest: ContentDigest
    workspace_manifest: CodeRetainedScopeBody
    modules: tuple[CodeRetainedScopeModule, ...]
    packages: tuple[CodeRetainedScopePackage, ...]

    def __post_init__(self) -> None:
        _text(self.repository_binding_ref)
        _digest(self.observation_digest)
        if type(self.workspace_manifest) is not CodeRetainedScopeBody:
            raise ContractViolation("exact workspace manifest required")
        self.workspace_manifest.__post_init__()
        _rows(self.modules, CodeRetainedScopeModule)
        _rows(self.packages, CodeRetainedScopePackage)
        module_paths = {}
        module_keys = []
        bodies = [self.workspace_manifest]
        for module in self.modules:
            module.__post_init__()
            module_keys.append(module.module_id.encode("utf-8"))
            module_paths[module.module_id] = module.manifest.relative_path
            bodies.append(module.manifest)
        if module_keys != sorted(set(module_keys)):
            raise ContractViolation("scope modules must be unique and UTF-8 ordered")
        if len(set(module_paths.values())) != len(module_paths):
            raise ContractViolation("scope module origins duplicate")
        package_keys = []
        for package in self.packages:
            package.__post_init__()
            package_keys.append(
                (package.module_id.encode(), package.package_id.encode())
            )
            if module_paths.get(package.module_id) != package.module_manifest_path:
                raise ContractViolation("scope package module correspondence differs")
            bodies.append(package.manifest)
        if package_keys != sorted(set(package_keys)):
            raise ContractViolation("scope packages must be unique and UTF-8 ordered")
        # Count repeated bodies too: a repeated-coordinate fanout cannot evade bounds.
        if sum(len(body.body) for body in bodies) > MAX_SCOPE_TOTAL_BYTES:
            raise ContractViolation("scope aggregate body bound exceeded")
        by_path = {}
        by_ref = {}
        for body in bodies:
            if body.relative_path in by_path and by_path[body.relative_path] != body:
                raise ContractViolation("scope retained path substitution")
            content = (body.content_digest, body.body)
            if body.body_ref in by_ref and by_ref[body.body_ref] != content:
                raise ContractViolation("scope retained reference substitution")
            by_path[body.relative_path] = body
            by_ref[body.body_ref] = content

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": RETAINED_SCOPE_CONTRACT,
            "repository_binding_ref": self.repository_binding_ref,
            "observation_digest": self.observation_digest.to_wire(),
            "workspace_manifest": self.workspace_manifest.to_wire(),
            "modules": [module.to_wire() for module in self.modules],
            "packages": [package.to_wire() for package in self.packages],
        }

    @property
    def projection_digest(self) -> ContentDigest:
        return ContentDigest.of_bytes(encode_retained_scope_projection(self))


# Hex bytes plus bounded metadata. This is a resource ceiling, not source authority.
MAX_SCOPE_CANONICAL_BYTES = 268_435_456


def encode_retained_scope_projection(value: CodeRetainedScopeProjection) -> bytes:
    if type(value) is not CodeRetainedScopeProjection:
        raise ContractViolation("exact retained scope projection required")
    value.__post_init__()
    body = canonical_json_bytes(value.to_wire())
    if len(body) > MAX_SCOPE_CANONICAL_BYTES:
        raise ContractViolation("scope canonical body bound exceeded")
    return body


_Snapshot_contra = TypeVar("_Snapshot_contra", contravariant=True)


class RetainedScopeReader(Protocol[_Snapshot_contra]):
    def read_complete_scope_projection(
        self, snapshot: _Snapshot_contra
    ) -> CodeRetainedScopeProjection:
        """Mechanically project original evidence; no filtering, parsing or grants."""
        ...


class RetainedScopeValidator(Protocol[_Snapshot_contra]):
    def validate_complete_scope_projection(
        self,
        snapshot: _Snapshot_contra,
        *,
        projection_digest: ContentDigest | None = None,
    ) -> None:
        """Revalidate original scope and, when supplied, exact projected digest.

        Before reading, omit the digest. After policy calculation, require the
        digest of the consumed projection. The original adapter recomputes it
        from retained evidence; it cannot accept a caller projection as evidence.
        Repeated validation is allowed and does not authorize execution.
        """
        ...
