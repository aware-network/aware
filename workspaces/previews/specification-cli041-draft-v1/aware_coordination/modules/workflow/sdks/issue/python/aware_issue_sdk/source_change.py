"""Neutral source-change admission contracts; portable values are not permits."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Protocol

ISSUE_SOURCE_CHANGE_OPERATION_REF = "workflow.issue.source_change.admit.v1"
ISSUE_SOURCE_CHANGE_INTENT = "protocol_specification_setup_v1"


def _digest(value: str) -> str:
    if (
        type(value) is not str
        or len(value) != 71
        or not value.startswith("sha256:")
        or any(c not in "0123456789abcdef" for c in value[7:])
    ):
        raise ValueError("Expected exact sha256-prefixed digest")
    return value


def _relative(value: str) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("Expected canonical relative source path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value or value == ".":
        raise ValueError("Expected canonical relative source path")
    return value


@dataclass(frozen=True, slots=True)
class IssueSourceChangeRequest:
    issue_ref: str
    expected_issue_sha256: str
    manifest_locator: str
    expected_manifest_sha256: str
    candidate: bytes
    directory_paths: tuple[str, ...]
    client_intent_id: str
    intent: str = ISSUE_SOURCE_CHANGE_INTENT

    def __post_init__(self) -> None:
        for text in (self.issue_ref, self.manifest_locator, self.client_intent_id):
            if (
                type(text) is not str
                or not text
                or text.strip() != text
                or any(ord(c) < 32 for c in text)
            ):
                raise ValueError("Source-change coordinates must be exact trimmed text")
        _digest(self.expected_issue_sha256)
        _digest(self.expected_manifest_sha256)
        if type(self.candidate) is not bytes or len(self.candidate) > 16 * 1024 * 1024:
            raise ValueError("Candidate must be bounded exact bytes")
        if self.intent != ISSUE_SOURCE_CHANGE_INTENT:
            raise ValueError("Source-change intent unsupported")
        if type(self.directory_paths) is not tuple or len(self.directory_paths) > 64:
            raise ValueError("Directory paths must be an ordered bounded tuple")
        for path in self.directory_paths:
            _relative(path)
        if len(set(self.directory_paths)) != len(self.directory_paths):
            raise ValueError("Directory paths must be unique")

    @property
    def candidate_sha256(self) -> str:
        return "sha256:" + hashlib.sha256(self.candidate).hexdigest()


@dataclass(frozen=True, slots=True)
class IssueSourceChangeEffect:
    path: str
    kind: str
    state: str
    durability_confirmed: bool
    mode: int | None
    before_digest: str | None
    after_digest: str | None
    after_identity: tuple[int, int] | None


@dataclass(frozen=True, slots=True)
class IssueSourceChangeReceipt:
    issue_ref: str
    execution_ref: str
    client_intent_id: str
    issue_sha256: str
    manifest_preimage_sha256: str
    manifest_postimage_sha256: str
    ordered_effect_paths: tuple[str, ...]
    effects: tuple[IssueSourceChangeEffect, ...]
    authority_grade: str = "filesystem_harness_observed_v1"
    confinement_profile: str = "descriptor_walk_v1"


class IssueSourceChangeRefusal(RuntimeError):
    def __init__(self, code: str, effects=(), residual_scratch_paths=()):
        super().__init__(code)
        self.code = code
        self.effects = tuple(effects)
        self.residual_scratch_paths = tuple(residual_scratch_paths)


class IssueSourceChangeAdmission(Protocol):
    """Actual owner-issued capability, not a decoded contract or callback guard.

    The consumption surface performs only the bound concrete physical effects.
    Protocol retains candidate semantics and separately integrates this port.
    """

    @property
    def phase(self) -> str: ...
    @property
    def effects(self) -> tuple[IssueSourceChangeEffect, ...]: ...
    def validate_current(self) -> None: ...
    def prepare_next_directory(self) -> IssueSourceChangeEffect: ...
    def replace_manifest(self) -> IssueSourceChangeEffect: ...
    def finish(self) -> IssueSourceChangeReceipt: ...
    def release(self) -> None: ...


class IssueSourceChangeProvider(Protocol):
    def admit_source_change(
        self, request: IssueSourceChangeRequest
    ) -> IssueSourceChangeAdmission: ...

    def validate_source_change(self, admission: IssueSourceChangeAdmission) -> None: ...


@dataclass(frozen=True)
class IssueSourceChangeClient:
    provider: IssueSourceChangeProvider

    def admit(self, request: IssueSourceChangeRequest) -> IssueSourceChangeAdmission:
        return self.provider.admit_source_change(request)

    def validate(self, admission: IssueSourceChangeAdmission) -> None:
        self.provider.validate_source_change(admission)
