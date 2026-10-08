"""Bounded draft intent and observations; these values are never permits.

No filesystem reads, writes, provider discovery or validation callbacks belong
here. Original Issue, Protocol and FileSystem capabilities remain separately
issued. Portable requests and binding snapshots convey no effect authority.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .draft_input_custody import IssueDraftInputCustodyObservation

from .source_change import _digest

ISSUE_DRAFT_PACKAGE_INTENT = "protocol_specification_draft_v1"
ISSUE_DRAFT_PACKAGE_OPERATION_REF = "workflow.issue.draft_package.admit.v1"
ISSUE_DRAFT_PACKAGE_MODE_PROFILE = "specification_draft_package_v1"
ISSUE_DRAFT_PACKAGE_MAX_MEMBERS = 4096
ISSUE_DRAFT_PACKAGE_MAX_MEMBER_BYTES = 2 * 1024 * 1024
ISSUE_DRAFT_PACKAGE_MAX_TOTAL_BYTES = 64 * 1024 * 1024
ISSUE_DRAFT_PACKAGE_MAX_PATH_BYTES = 1024


def _text(value: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("Draft coordinates require exact non-control text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("Draft coordinates require UTF-8 text") from error
    return value


def _path(value: str) -> str:
    _text(value)
    path = PurePosixPath(value)
    if (
        "\\" in value
        or unicodedata.normalize("NFC", value) != value
        or any(0x7F <= ord(character) <= 0x9F for character in value)
        or path.is_absolute()
        or ".." in path.parts
        or str(path) != value
        or value == "."
        or len(value.encode("utf-8")) > ISSUE_DRAFT_PACKAGE_MAX_PATH_BYTES
    ):
        raise ValueError("Draft paths require bounded canonical relative locators")
    return value


def _directories(members: tuple[tuple[str, bytes], ...]) -> tuple[str, ...]:
    directories = {
        str(parent)
        for path, _ in members
        for parent in PurePosixPath(path).parents
        if str(parent) != "."
    }
    return tuple(sorted(directories, key=lambda path: (path.count("/"), path)))


@dataclass(frozen=True, slots=True)
class IssueDraftPackageRequest:
    """Immutable intent copied/bound by the original owner issuer.

    Locators are repository-relative; members are package-relative, nonempty,
    uniquely sorted exact bytes. Scope includes both explicit scratch members
    and their public counterparts, even though publication is one directory
    rename. The manifest is observed, not an effect path.
    """

    issue_ref: str
    expected_issue_sha256: str
    manifest_locator: str
    expected_manifest_sha256: str
    target_locator: str
    scratch_locator: str
    ordered_members: tuple[tuple[str, bytes], ...]
    authoring_intent_ref: str
    client_intent_id: str
    intent: str = ISSUE_DRAFT_PACKAGE_INTENT
    mode_profile: str = ISSUE_DRAFT_PACKAGE_MODE_PROFILE

    def __post_init__(self) -> None:
        for value in (self.issue_ref, self.authoring_intent_ref, self.client_intent_id):
            _text(value)
        _digest(self.expected_issue_sha256)
        _digest(self.expected_manifest_sha256)
        for value in (
            self.manifest_locator,
            self.target_locator,
            self.scratch_locator,
        ):
            _path(value)
        if type(self.intent) is not str or self.intent != ISSUE_DRAFT_PACKAGE_INTENT:
            raise ValueError("Draft intent unsupported; setup admission is separate")
        if (
            type(self.mode_profile) is not str
            or self.mode_profile != ISSUE_DRAFT_PACKAGE_MODE_PROFILE
        ):
            raise ValueError("Draft mode profile unsupported")
        target = PurePosixPath(self.target_locator)
        scratch = PurePosixPath(self.scratch_locator)
        if target == scratch or target.parent != scratch.parent:
            raise ValueError(
                "Draft scratch and target require distinct same-parent paths"
            )
        suffix = scratch.name.removeprefix(".aware-spec-draft-")
        if (
            not scratch.name.startswith(".aware-spec-draft-")
            or len(suffix) != 32
            or any(character not in "0123456789abcdef" for character in suffix)
        ):
            raise ValueError("Scratch requires the exact private draft naming profile")
        for root in (self.target_locator, self.scratch_locator):
            if self.manifest_locator == root or self.manifest_locator.startswith(
                root + "/"
            ):
                raise ValueError("Observed manifest cannot be a draft effect path")
        if (
            type(self.ordered_members) is not tuple
            or not 1 <= len(self.ordered_members) <= ISSUE_DRAFT_PACKAGE_MAX_MEMBERS
        ):
            raise ValueError("Draft members require a nonempty bounded tuple")
        prior = None
        files = set()
        total = 0
        for member in self.ordered_members:
            if type(member) is not tuple or len(member) != 2:
                raise ValueError("Draft members require exact path/bytes pairs")
            path, body = member
            _path(path)
            if (
                type(body) is not bytes
                or len(body) > ISSUE_DRAFT_PACKAGE_MAX_MEMBER_BYTES
            ):
                raise ValueError("Draft member body requires bounded exact bytes")
            if prior is not None and path <= prior:
                raise ValueError("Draft members must be uniquely path-sorted")
            prior = path
            files.add(path)
            total += len(body)
            if total > ISSUE_DRAFT_PACKAGE_MAX_TOTAL_BYTES:
                raise ValueError("Draft total member bytes exceeded")
        for path in files:
            if any(str(parent) in files for parent in PurePosixPath(path).parents):
                raise ValueError("Draft member file/directory conflict")

    @property
    def candidate_sha256(self) -> str:
        """Domain-separated length-framed member bytes, not semantic truth."""
        digest = hashlib.sha256(b"aware.issue.draft.members.v1\x00")
        digest.update(len(self.ordered_members).to_bytes(8, "big"))
        for path, body in self.ordered_members:
            encoded = path.encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
            digest.update(len(body).to_bytes(8, "big"))
            digest.update(body)
        return "sha256:" + digest.hexdigest()

    @property
    def ordered_effect_paths(self) -> tuple[str, ...]:
        """Exact policy footprint, not evidence that any effect occurred."""
        relative = (
            *_directories(self.ordered_members),
            *(p for p, _ in self.ordered_members),
        )
        return tuple(
            path
            for root in (self.scratch_locator, self.target_locator)
            for path in (root, *(f"{root}/{member}" for member in relative))
        )


@dataclass(frozen=True, slots=True)
class IssueDraftPackageBinding:
    """Historical bound execution/request observation, never a permit.

    The original issuer supplies recorded execution and a detached immutable
    request copy. Reading a snapshot does not validate freshness or renew writes.
    """

    execution_ref: str
    request: IssueDraftPackageRequest
    authority_grade: str = "filesystem_harness_observed_v1"


@dataclass(frozen=True, slots=True)
class IssueDraftPackageEffect:
    path: str
    kind: str
    state: str
    durability_confirmed: bool
    mode: int | None
    before_digest: str | None
    after_digest: str | None
    after_identity: tuple[int, int] | None


@dataclass(frozen=True, slots=True)
class IssueDraftPackageEvidence:
    package_outcome: str
    effects: tuple[IssueDraftPackageEffect, ...]
    residual_scratch_paths: tuple[str, ...]
    cleanup_diagnostics: tuple[str, ...]
    durability_confirmed: bool = False
    ledger_complete: bool = True


@dataclass(frozen=True, slots=True)
class IssueDraftPackageReceipt:
    issue_ref: str
    execution_ref: str
    client_intent_id: str
    authoring_intent_ref: str
    issue_sha256: str
    manifest_sha256: str
    candidate_sha256: str
    ordered_effect_paths: tuple[str, ...]
    evidence: IssueDraftPackageEvidence
    authority_grade: str = "filesystem_harness_observed_v1"


@dataclass(frozen=True, slots=True)
class IssueDraftPackageCleanupDisposition:
    """Correlated input/cleanup history; no admission or renewed authority.

    Unknown stays explicit. Protocol cleanup remains caller-owned at the Issue
    boundary; the SPEC context must separately account for its own transfer.
    """

    request: IssueDraftPackageRequest
    execution_ref: str | None
    physical_claim: str
    physical_cleanup_owner: str
    physical_cleanup_attempted: bool | None
    physical_cleanup_outcome: str
    protocol_cleanup_owner: str
    evidence: IssueDraftPackageEvidence | None


class IssueDraftPackageRefusal(RuntimeError):
    """None input_cleanup means unavailable/unknown, never caller-owned."""

    def __init__(
        self,
        code: str,
        evidence: IssueDraftPackageEvidence | None = None,
        required_effect_paths: tuple[str, ...] = (),
        *,
        input_cleanup: IssueDraftPackageCleanupDisposition | None = None,
        input_custody: IssueDraftInputCustodyObservation | None = None,
    ):
        super().__init__(code)
        self.code = code
        self.evidence = evidence
        self.required_effect_paths = tuple(required_effect_paths)
        self.input_cleanup = input_cleanup
        self.input_custody = input_custody


class IssueDraftPackageAdmission(Protocol):
    """Original owner capability, not a structural request or setup permit.

    Staged lenses/postimages remain original FileSystem objects. Semantic staged
    validation and fresh observation are SPEC responsibilities, not flags here.
    """

    @property
    def phase(self) -> str: ...
    @property
    def evidence(self) -> IssueDraftPackageEvidence: ...
    def observe_binding(self) -> IssueDraftPackageBinding: ...
    def observe_cleanup(self) -> IssueDraftPackageCleanupDisposition: ...
    def validate_current(self) -> None: ...
    def validate_completed_current(self) -> None: ...
    def stage_next_effect(self) -> IssueDraftPackageEffect | None: ...
    def lend_staged_source(self) -> object: ...
    def publish_package(self) -> object: ...
    def admit_published_read(self, *, physical_postimage: object) -> object: ...
    def validate_published_read(self, read_selection: object) -> None: ...
    def release_published_read(self, read_selection: object) -> None: ...
    def observe_input_custody(self) -> IssueDraftInputCustodyObservation: ...
    def finish(
        self, *, physical_postimage: object, read_selection: object
    ) -> IssueDraftPackageReceipt: ...
    def release(self) -> IssueDraftPackageEvidence: ...


class IssueDraftPackageProvider(Protocol):
    def retain_draft_inputs(
        self,
        *,
        protocol_target: object,
        physical_plan: object,
        attempt_ref: str,
        client_intent_id: str,
    ) -> object: ...
    def observe_draft_package_cleanup(
        self, *, protocol_target: object, physical_plan: object
    ) -> IssueDraftPackageCleanupDisposition: ...

    def admit_draft_package(
        self,
        request: IssueDraftPackageRequest,
        *,
        protocol_target: object,
        physical_plan: object,
        input_custody: object | None = None,
    ) -> IssueDraftPackageAdmission: ...

    def validate_draft_package(self, admission: object) -> None: ...
    def observe_draft_package_binding(
        self, admission: object
    ) -> IssueDraftPackageBinding: ...
