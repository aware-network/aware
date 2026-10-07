"""Immutable draft-attempt knowledge, never owner admission or a live verifier."""

from dataclasses import dataclass, replace
from pathlib import PurePosixPath
from typing import Protocol
from unicodedata import normalize

from aware_specification_runtime.values import sha256_ref, token

SPECIFICATION_DRAFT_EVIDENCE_PROFILE = "specification.draft.fs-evidence.v1"
_KINDS = frozenset(
    {
        "directory",
        "file",
        "file_write",
        "package_publication",
        "package_postimage",
        "cleanup_file",
        "cleanup_directory",
    }
)


def _path(value: str) -> None:
    token(value, "evidence_path")
    parsed = PurePosixPath(value)
    if (
        parsed.is_absolute()
        or str(parsed) != value
        or any(p in {".", ".."} for p in value.split("/"))
        or "\\" in value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
        or normalize("NFC", value) != value
        or len(value.encode("utf-8")) > 1024
    ):
        raise ValueError("invalid_draft_evidence_path")


def _identity(value: tuple[int, int] | None) -> None:
    if value is not None and (
        type(value) is not tuple
        or len(value) != 2
        or any(type(v) is not int or v < 0 for v in value)
    ):
        raise ValueError("invalid_draft_evidence_identity")


@dataclass(frozen=True, slots=True)
class SpecificationDraftMemberBinding:
    relative_path: str
    byte_count: int
    source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDraftMemberBinding:
            raise ValueError("invalid_draft_member_binding")
        _path(self.relative_path)
        if type(self.byte_count) is not int or not 0 <= self.byte_count <= 2 * 1024**2:
            raise ValueError("invalid_draft_member_size")
        sha256_ref(self.source_sha256, "member_source_sha256")


@dataclass(frozen=True, slots=True)
class SpecificationDraftPhysicalEffect:
    path: str
    kind: str
    state: str
    mode: int | None
    before_digest: str | None
    after_digest: str | None
    before_identity: tuple[int, int] | None
    after_identity: tuple[int, int] | None
    durability_confirmed: bool

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDraftPhysicalEffect:
            raise ValueError("invalid_draft_physical_effect")
        _path(self.path)
        if type(self.kind) is not str or self.kind not in _KINDS:
            raise ValueError("invalid_draft_effect_kind")
        if type(self.state) is not str or self.state not in {
            "none",
            "applied",
            "unknown",
        }:
            raise ValueError("invalid_draft_effect_state")
        if self.mode is not None and (
            type(self.mode) is not int or not 0 <= self.mode <= 0o7777
        ):
            raise ValueError("invalid_draft_effect_mode")
        for value in (self.before_digest, self.after_digest):
            if value is not None:
                sha256_ref(value, "effect_digest")
        _identity(self.before_identity)
        _identity(self.after_identity)
        if type(self.durability_confirmed) is not bool:
            raise ValueError("invalid_draft_effect_durability")


@dataclass(frozen=True, slots=True)
class SpecificationDraftEvidence:
    profile: str
    attempt_ref: str
    issue_ref: str
    execution_ref: str
    client_intent_id: str
    authoring_intent_ref: str
    protocol_manifest_sha256: str
    target_locator: str
    scratch_locator: str
    members: tuple[SpecificationDraftMemberBinding, ...]
    package_outcome: str
    effects: tuple[SpecificationDraftPhysicalEffect, ...]
    residual_scratch_paths: tuple[str, ...]
    cleanup_diagnostics: tuple[str, ...]
    ledger_complete: bool
    completion_verified: bool
    durability_confirmed: bool

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDraftEvidence:
            raise ValueError("invalid_draft_evidence")
        if (
            type(self.profile) is not str
            or self.profile != SPECIFICATION_DRAFT_EVIDENCE_PROFILE
        ):
            raise ValueError("invalid_draft_evidence_profile")
        for name in (
            "attempt_ref",
            "issue_ref",
            "execution_ref",
            "client_intent_id",
            "authoring_intent_ref",
        ):
            token(getattr(self, name), name)
        sha256_ref(self.protocol_manifest_sha256, "protocol_manifest_sha256")
        _path(self.target_locator)
        _path(self.scratch_locator)
        if self.target_locator == self.scratch_locator:
            raise ValueError("invalid_draft_evidence_locators")
        if type(self.members) is not tuple or not 1 <= len(self.members) <= 4096:
            raise ValueError("invalid_draft_member_bindings")
        for member in self.members:
            if type(member) is not SpecificationDraftMemberBinding:
                raise ValueError("invalid_draft_member_binding")
            member.__post_init__()
        paths = tuple(m.relative_path for m in self.members)
        if (
            paths != tuple(sorted(set(paths)))
            or sum(m.byte_count for m in self.members) > 64 * 1024**2
        ):
            raise ValueError("invalid_draft_member_bindings")
        known_paths = set(paths)
        if any(
            str(parent) in known_paths
            for path in paths
            for parent in PurePosixPath(path).parents
        ):
            raise ValueError("conflicting_draft_member_paths")
        if type(self.package_outcome) is not str or self.package_outcome not in {
            "none",
            "published",
            "unknown",
        }:
            raise ValueError("invalid_draft_package_outcome")
        if type(self.effects) is not tuple:
            raise ValueError("invalid_draft_effects")
        for effect in self.effects:
            if type(effect) is not SpecificationDraftPhysicalEffect:
                raise ValueError("invalid_draft_physical_effect")
            effect.__post_init__()
        if (
            type(self.residual_scratch_paths) is not tuple
            or type(self.cleanup_diagnostics) is not tuple
        ):
            raise ValueError("invalid_draft_cleanup_evidence")
        for path in self.residual_scratch_paths:
            _path(path)
        for diagnostic in self.cleanup_diagnostics:
            token(diagnostic, "cleanup_diagnostic")
        for value in (
            self.ledger_complete,
            self.completion_verified,
            self.durability_confirmed,
        ):
            if type(value) is not bool:
                raise ValueError("invalid_draft_evidence_boolean")


class SpecificationDraftEvidenceReader(Protocol):
    def observe_draft_evidence(self) -> SpecificationDraftEvidence: ...


def snapshot_draft_evidence(
    value: SpecificationDraftEvidence,
) -> SpecificationDraftEvidence:
    """Revalidate and detach the value from a provider's retained Python objects."""
    if type(value) is not SpecificationDraftEvidence:
        raise ValueError("invalid_draft_evidence")
    value.__post_init__()
    return replace(
        value,
        members=tuple(replace(member) for member in value.members),
        effects=tuple(replace(effect) for effect in value.effects),
    )
