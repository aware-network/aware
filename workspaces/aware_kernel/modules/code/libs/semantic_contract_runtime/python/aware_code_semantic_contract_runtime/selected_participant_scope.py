"""Portable selected participants over a complete retained declaration closure.

The view records interpreted relationships, never original observation,
membership, source currentness, policy, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes
from .semantic_candidates import _path

MAX_SELECTED_PARTICIPANTS = 256
MAX_SELECTED_RELATIONSHIPS = 1024


@dataclass(frozen=True, slots=True, order=True)
class CodeSelectedParticipant:
    scope_key: str
    module_id: str
    package_id: str

    def __post_init__(self) -> None:
        # The scope key is the closure's repository-relative Workspace manifest
        # path; module and package IDs remain single components.
        _path(self.scope_key)
        for value in (self.module_id, self.package_id):
            _path(value)
            if "/" in value:
                raise ContractViolation("participant module and package IDs must be one component")

    def to_wire(self) -> dict[str, str]:
        self.__post_init__()
        return {
            "scope_key": self.scope_key,
            "module_id": self.module_id,
            "package_id": self.package_id,
        }


@dataclass(frozen=True, slots=True)
class CodeSelectedParticipantRelationship:
    kind: str
    source: CodeSelectedParticipant
    target: CodeSelectedParticipant

    def __post_init__(self) -> None:
        if self.kind not in ("registration", "direct_dependency"):
            raise ContractViolation("selected relationship kind differs")
        for value in (self.source, self.target):
            if type(value) is not CodeSelectedParticipant:
                raise ContractViolation("exact selected participant required")
            value.__post_init__()

    @property
    def ordering_key(self) -> tuple[str, ...]:
        return (
            self.source.scope_key, self.source.module_id, self.source.package_id,
            self.kind, self.target.scope_key, self.target.module_id,
            self.target.package_id,
        )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"kind": self.kind, "source": self.source.to_wire(),
                "target": self.target.to_wire()}


@dataclass(frozen=True, slots=True)
class CodeSelectedProfileRelationship:
    declaring_scope_key: str
    dependency_index: int
    profile_package_index: int
    target_scope_key: str
    profile_key: str
    manifest_content_digest: ContentDigest

    def __post_init__(self) -> None:
        for value in (
            self.declaring_scope_key, self.target_scope_key, self.profile_key
        ):
            _path(value)
        for value in (self.dependency_index, self.profile_package_index):
            if type(value) is not int or value < 0:
                raise ContractViolation("profile occurrence index differs")
        if type(self.manifest_content_digest) is not ContentDigest:
            raise ContractViolation("exact profile body digest required")
        self.manifest_content_digest.__post_init__()

    @property
    def ordering_key(self) -> tuple[object, ...]:
        return (
            self.declaring_scope_key, self.dependency_index,
            self.profile_package_index, self.target_scope_key,
            self.profile_key,
        )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "declaring_scope_key": self.declaring_scope_key,
            "dependency_index": self.dependency_index,
            "profile_package_index": self.profile_package_index,
            "target_scope_key": self.target_scope_key,
            "profile_key": self.profile_key,
            "manifest_content_digest": self.manifest_content_digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeSelectedParticipantViewV1:
    declaration_closure_digest: ContentDigest
    root: CodeSelectedParticipant
    participants: tuple[CodeSelectedParticipant, ...]
    relationships: tuple[CodeSelectedParticipantRelationship, ...]
    profiles: tuple[CodeSelectedProfileRelationship, ...]

    def __post_init__(self) -> None:
        if type(self.declaration_closure_digest) is not ContentDigest:
            raise ContractViolation("exact declaration closure digest required")
        self.declaration_closure_digest.__post_init__()
        if type(self.root) is not CodeSelectedParticipant:
            raise ContractViolation("exact selected root required")
        self.root.__post_init__()
        if (
            type(self.participants) is not tuple
            or not 0 < len(self.participants) <= MAX_SELECTED_PARTICIPANTS
            or any(type(item) is not CodeSelectedParticipant for item in self.participants)
        ):
            raise ContractViolation("bounded exact selected participants required")
        if tuple(sorted(set(self.participants))) != self.participants or self.root not in self.participants:
            raise ContractViolation("selected participants unordered, duplicate, or rootless")
        for item in self.participants:
            item.__post_init__()
        if (
            type(self.relationships) is not tuple
            or len(self.relationships) > MAX_SELECTED_RELATIONSHIPS
            or any(type(item) is not CodeSelectedParticipantRelationship for item in self.relationships)
        ):
            raise ContractViolation("bounded exact selected relationships required")
        for item in self.relationships:
            item.__post_init__()
            if item.source not in self.participants or item.target not in self.participants:
                raise ContractViolation("selected relationship endpoint unavailable")
        relationships = tuple(item.ordering_key for item in self.relationships)
        if relationships != tuple(sorted(set(relationships))):
            raise ContractViolation("selected relationships unordered or duplicate")
        if (
            type(self.profiles) is not tuple
            or len(self.profiles) > MAX_SELECTED_RELATIONSHIPS
            or any(type(item) is not CodeSelectedProfileRelationship for item in self.profiles)
        ):
            raise ContractViolation("bounded exact selected profiles required")
        for item in self.profiles:
            item.__post_init__()
        profiles = tuple(item.ordering_key for item in self.profiles)
        if profiles != tuple(sorted(set(profiles))):
            raise ContractViolation("selected profiles unordered or duplicate")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.selected-participant-view.v1",
            "declaration_closure_digest": self.declaration_closure_digest.to_wire(),
            "root": self.root.to_wire(),
            "participants": [item.to_wire() for item in self.participants],
            "relationships": [item.to_wire() for item in self.relationships],
            "profiles": [item.to_wire() for item in self.profiles],
        }

    @property
    def digest(self) -> ContentDigest:
        return ContentDigest.of_bytes(canonical_json_bytes(self.to_wire()))


__all__ = [
    "CodeSelectedParticipant", "CodeSelectedParticipantRelationship",
    "CodeSelectedParticipantViewV1", "CodeSelectedProfileRelationship",
]
