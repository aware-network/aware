"""Detached cleanup knowledge; no supplier imports, handles or authority."""

import unicodedata
from dataclasses import dataclass, replace
from pathlib import PurePosixPath
from typing import cast

from aware_specification_runtime.values import sha256_ref, token

from .draft_evidence import SpecificationDraftPhysicalEffect, _path

SPECIFICATION_DRAFT_CLEANUP_PROFILE = "specification.draft.cleanup-evidence.v1"


def _enum(value: str, choices: set[str]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError("invalid_draft_cleanup_value")


def _texts(values: tuple[str, ...]) -> None:
    if type(values) is not tuple or len(values) > 16384:
        raise ValueError("invalid_draft_cleanup_diagnostics")
    for value in values:
        token(value, "cleanup_diagnostic")
        if len(value.encode("utf-8")) > 4096:
            raise ValueError("invalid_draft_cleanup_diagnostic")


def _exact(value: object, expected: type) -> None:
    if type(value) is not expected:
        raise ValueError("invalid_draft_cleanup_type")
    method = getattr(value, "__post_init__", None)
    if not callable(method):
        raise TypeError("invalid_draft_cleanup_type")
    method()


@dataclass(frozen=True, slots=True)
class SpecificationDraftCleanupRequest:
    issue_ref: str
    expected_issue_sha256: str
    manifest_locator: str
    expected_manifest_sha256: str
    target_locator: str
    scratch_locator: str
    ordered_members: tuple[tuple[str, bytes], ...]
    authoring_intent_ref: str
    client_intent_id: str
    intent: str
    mode_profile: str
    candidate_sha256: str
    ordered_effect_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDraftCleanupRequest:
            raise ValueError("invalid_draft_cleanup_request")
        for name in (
            "issue_ref",
            "authoring_intent_ref",
            "client_intent_id",
            "intent",
            "mode_profile",
        ):
            token(getattr(self, name), name)
        for name in (
            "expected_issue_sha256",
            "expected_manifest_sha256",
            "candidate_sha256",
        ):
            sha256_ref(getattr(self, name), name)
        for path in (self.manifest_locator, self.target_locator, self.scratch_locator):
            _path(path)
        if self.target_locator == self.scratch_locator:
            raise ValueError("invalid_draft_cleanup_locators")
        if (
            type(self.ordered_members) is not tuple
            or not 1 <= len(self.ordered_members) <= 4096
        ):
            raise ValueError("invalid_draft_cleanup_members")
        paths = []
        total = 0
        for member in self.ordered_members:
            if (
                type(member) is not tuple
                or len(member) != 2
                or type(member[1]) is not bytes
            ):
                raise ValueError("invalid_draft_cleanup_member")
            _path(member[0])
            if len(member[1]) > 2 * 1024**2:
                raise ValueError("invalid_draft_cleanup_member_size")
            paths.append(member[0])
            total += len(member[1])
        if paths != sorted(set(paths)) or total > 64 * 1024**2:
            raise ValueError("invalid_draft_cleanup_members")
        if (
            type(self.ordered_effect_paths) is not tuple
            or len(self.ordered_effect_paths) > 16384
        ):
            raise ValueError("invalid_draft_cleanup_effect_paths")
        for path in self.ordered_effect_paths:
            _path(path)


@dataclass(frozen=True, slots=True)
class SpecificationDraftCleanupLedger:
    package_outcome: str
    effects: tuple[SpecificationDraftPhysicalEffect, ...]
    residual_scratch_paths: tuple[str, ...]
    cleanup_diagnostics: tuple[str, ...]
    durability_confirmed: bool
    ledger_complete: bool | None

    def __post_init__(self) -> None:
        _enum(self.package_outcome, {"none", "published", "unknown"})
        if type(self.effects) is not tuple or len(self.effects) > 65536:
            raise ValueError("invalid_draft_cleanup_effects")
        for effect in self.effects:
            _exact(effect, SpecificationDraftPhysicalEffect)
        if (
            type(self.residual_scratch_paths) is not tuple
            or len(self.residual_scratch_paths) > 16384
        ):
            raise ValueError("invalid_draft_cleanup_residue")
        for path in self.residual_scratch_paths:
            _path(path)
        _texts(self.cleanup_diagnostics)
        if type(self.durability_confirmed) is not bool or (
            self.ledger_complete is not None and type(self.ledger_complete) is not bool
        ):
            raise ValueError("invalid_draft_cleanup_boolean")


@dataclass(frozen=True, slots=True)
class SpecificationDraftIssueCleanup:
    request: SpecificationDraftCleanupRequest
    execution_ref: str | None
    physical_claim: str
    physical_cleanup_owner: str
    physical_cleanup_attempted: bool | None
    physical_cleanup_outcome: str
    protocol_cleanup_owner: str
    evidence: SpecificationDraftCleanupLedger | None

    def __post_init__(self) -> None:
        _exact(self.request, SpecificationDraftCleanupRequest)
        if self.execution_ref is not None:
            token(self.execution_ref, "execution_ref")
        _enum(self.physical_claim, {"unclaimed", "claimed", "unknown"})
        _enum(self.physical_cleanup_owner, {"caller", "issue", "filesystem", "unknown"})
        _enum(
            self.physical_cleanup_outcome,
            {"not_attempted", "completed", "incomplete", "unknown"},
        )
        _enum(self.protocol_cleanup_owner, {"caller", "issue", "unknown"})
        if (
            self.physical_cleanup_attempted is not None
            and type(self.physical_cleanup_attempted) is not bool
        ):
            raise ValueError("invalid_draft_cleanup_boolean")
        if self.evidence is not None:
            _exact(self.evidence, SpecificationDraftCleanupLedger)


@dataclass(frozen=True, slots=True)
class SpecificationDraftPhysicalCleanup:
    root_locator: str
    target_path: str
    scratch_path: str
    attempted: bool
    outcome: str
    evidence: SpecificationDraftCleanupLedger

    def __post_init__(self) -> None:
        token(self.root_locator, "root_locator")
        if not PurePosixPath(self.root_locator).is_absolute():
            raise ValueError("invalid_draft_cleanup_root")
        _path(self.target_path)
        _path(self.scratch_path)
        if type(self.attempted) is not bool:
            raise ValueError("invalid_draft_cleanup_boolean")
        _enum(self.outcome, {"not_attempted", "completed", "incomplete", "unknown"})
        _exact(self.evidence, SpecificationDraftCleanupLedger)
        if self.evidence.ledger_complete is not None:
            raise ValueError("undeclared_physical_ledger_completeness")


@dataclass(frozen=True, slots=True)
class SpecificationDraftCleanupInvocation:
    responsibility: str
    invocation_state: str
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        _enum(self.responsibility, {"caller", "context", "unknown"})
        _enum(self.invocation_state, {"not_invoked", "invoked", "returned", "raised"})
        _texts(self.diagnostics)


def _custody_text(value: str) -> None:
    token(value, "custody_correlation")
    if (
        len(value.encode("utf-8")) > 1024
        or unicodedata.normalize("NFC", value) != value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
    ):
        raise ValueError("invalid_draft_custody_correlation")


@dataclass(frozen=True, slots=True)
class SpecificationDraftInputResourceObservation:
    acquisition: str
    responsibility: str
    transfer: str
    release_invocation: str
    owner_cleanup_attempted: bool | None
    owner_cleanup_outcome: str
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDraftInputResourceObservation:
            raise ValueError("invalid_draft_custody_type")
        _enum(self.acquisition, {"not_acquired", "acquired", "unknown"})
        _enum(
            self.responsibility, {"caller", "custody", "admission", "other", "unknown"}
        )
        _enum(self.transfer, {"not_attempted", "attempted", "completed", "unknown"})
        _enum(self.release_invocation, {"not_invoked", "invoked", "returned", "raised"})
        _enum(
            self.owner_cleanup_outcome,
            {"not_attempted", "completed", "incomplete", "unknown"},
        )
        if (
            self.owner_cleanup_attempted is not None
            and type(self.owner_cleanup_attempted) is not bool
        ):
            raise TypeError("invalid_draft_custody_boolean")
        _texts(self.diagnostics)


@dataclass(frozen=True, slots=True)
class SpecificationDraftInputCustodyObservation:
    attempt_ref: str
    client_intent_id: str
    execution_ref: str | None
    custody_state: str
    root_locator: str | None
    manifest_locator: str | None
    manifest_sha256: str | None
    target_locator: str | None
    scratch_locator: str | None
    physical: SpecificationDraftInputResourceObservation
    protocol: SpecificationDraftInputResourceObservation
    physical_evidence: SpecificationDraftCleanupLedger | None
    diagnostics: tuple[str, ...]
    context_ref: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDraftInputCustodyObservation:
            raise ValueError("invalid_draft_custody_type")
        for value in (self.attempt_ref, self.client_intent_id):
            _custody_text(value)
        for value in (self.execution_ref, self.context_ref):
            if value is not None:
                _custody_text(value)
        _enum(
            self.custody_state,
            {
                "reserving",
                "reserved",
                "transferring",
                "transferred",
                "releasing",
                "released",
                "failed",
                "unknown",
            },
        )
        if self.root_locator is not None:
            _custody_text(self.root_locator)
            root = PurePosixPath(self.root_locator)
            if (
                not root.is_absolute()
                or str(root) != self.root_locator
                or ".." in root.parts
            ):
                raise ValueError("invalid_draft_custody_root")
        for path in (self.manifest_locator, self.target_locator, self.scratch_locator):
            if path is not None:
                _path(path)
        if self.manifest_sha256 is not None:
            sha256_ref(self.manifest_sha256, "manifest_sha256")
        _exact(self.physical, SpecificationDraftInputResourceObservation)
        _exact(self.protocol, SpecificationDraftInputResourceObservation)
        if self.physical_evidence is not None:
            _exact(self.physical_evidence, SpecificationDraftCleanupLedger)
        _texts(self.diagnostics)


@dataclass(frozen=True, slots=True)
class SpecificationDraftCleanupEvidence:
    profile: str
    attempt_ref: str
    context_state: str
    issue_disposition: SpecificationDraftIssueCleanup | None
    physical_observation: SpecificationDraftPhysicalCleanup | None
    physical_invocation: SpecificationDraftCleanupInvocation
    protocol_invocation: SpecificationDraftCleanupInvocation
    protocol_owner_attempted: bool | None
    protocol_owner_outcome: str
    cleanup_diagnostics: tuple[str, ...]
    input_custody: SpecificationDraftInputCustodyObservation | None = None

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDraftCleanupEvidence:
            raise ValueError("invalid_draft_cleanup_evidence")
        _enum(self.profile, {SPECIFICATION_DRAFT_CLEANUP_PROFILE})
        token(self.attempt_ref, "attempt_ref")
        if self.input_custody is not None:
            _exact(self.input_custody, SpecificationDraftInputCustodyObservation)
            if self.input_custody.attempt_ref != self.attempt_ref:
                raise ValueError("draft_custody_attempt_mismatch")
        _enum(self.context_state, {"not_entered", "entering", "entered", "closed"})
        if self.issue_disposition is not None:
            _exact(self.issue_disposition, SpecificationDraftIssueCleanup)
        if self.physical_observation is not None:
            _exact(self.physical_observation, SpecificationDraftPhysicalCleanup)
        if self.issue_disposition is not None and self.physical_observation is not None:
            request = self.issue_disposition.request
            if (request.target_locator, request.scratch_locator) != (
                self.physical_observation.target_path,
                self.physical_observation.scratch_path,
            ):
                raise ValueError("draft_cleanup_source_mismatch")
        for value in (self.physical_invocation, self.protocol_invocation):
            _exact(value, SpecificationDraftCleanupInvocation)
        _enum(
            self.protocol_owner_outcome,
            {"not_attempted", "completed", "incomplete", "unknown"},
        )
        if (
            self.protocol_owner_attempted is not None
            and type(self.protocol_owner_attempted) is not bool
        ):
            raise ValueError("invalid_draft_cleanup_boolean")
        # Historical None/unknown receipts remain readable and are never
        # recomputed from their nested snapshot during decoding or cloning.
        if (self.protocol_owner_attempted, self.protocol_owner_outcome) != (
            None,
            "unknown",
        ):
            custody = self.input_custody
            if (
                custody is None
                or custody.protocol.acquisition != "acquired"
                or any(
                    value is None
                    for value in (
                        custody.execution_ref,
                        custody.context_ref,
                        custody.root_locator,
                        custody.manifest_locator,
                        custody.manifest_sha256,
                        custody.target_locator,
                        custody.scratch_locator,
                    )
                )
                or (self.protocol_owner_attempted, self.protocol_owner_outcome)
                != (
                    custody.protocol.owner_cleanup_attempted,
                    custody.protocol.owner_cleanup_outcome,
                )
                or (
                    self.protocol_owner_attempted is False
                    and self.protocol_owner_outcome != "not_attempted"
                )
                or (
                    self.protocol_owner_attempted is True
                    and self.protocol_owner_outcome == "not_attempted"
                )
                or self.protocol_owner_attempted is None
            ):
                raise ValueError("unqualified_protocol_cleanup_completion")
        _texts(self.cleanup_diagnostics)


def snapshot_draft_cleanup(value: object) -> SpecificationDraftCleanupEvidence:
    """Validate and clone every nested value, without any owner lookup."""
    _exact(value, SpecificationDraftCleanupEvidence)
    value = cast(SpecificationDraftCleanupEvidence, value)
    issue = value.issue_disposition
    physical = value.physical_observation
    return replace(
        value,
        issue_disposition=None
        if issue is None
        else replace(
            issue,
            request=replace(issue.request),
            evidence=None if issue.evidence is None else _ledger_copy(issue.evidence),
        ),
        physical_observation=None
        if physical is None
        else replace(physical, evidence=_ledger_copy(physical.evidence)),
        physical_invocation=replace(value.physical_invocation),
        protocol_invocation=replace(value.protocol_invocation),
        input_custody=None
        if value.input_custody is None
        else replace(
            value.input_custody,
            physical=replace(value.input_custody.physical),
            protocol=replace(value.input_custody.protocol),
            physical_evidence=None
            if value.input_custody.physical_evidence is None
            else _ledger_copy(value.input_custody.physical_evidence),
        ),
    )


def _ledger_copy(
    value: SpecificationDraftCleanupLedger,
) -> SpecificationDraftCleanupLedger:
    return replace(value, effects=tuple(replace(effect) for effect in value.effects))


def require_cleanup_extension(
    previous: SpecificationDraftCleanupEvidence,
    current: SpecificationDraftCleanupEvidence,
) -> None:
    """History consistency only; never supplier policy or authorization."""
    if current.attempt_ref != previous.attempt_ref:
        raise ValueError("draft_cleanup_attempt_mismatch")
    _require_custody_extension(previous.input_custody, current.input_custody)
    if previous.protocol_owner_attempted is not None and (
        current.protocol_owner_attempted is None
        or (
            previous.protocol_owner_attempted
            and current.protocol_owner_attempted is not True
        )
        or (
            previous.protocol_owner_attempted
            and current.protocol_owner_outcome != previous.protocol_owner_outcome
        )
    ):
        raise ValueError("draft_protocol_cleanup_history_regressed")
    for old, new in (
        (previous.issue_disposition, current.issue_disposition),
        (previous.physical_observation, current.physical_observation),
    ):
        if old is None:
            continue
        if new is None:
            raise ValueError("draft_cleanup_history_unavailable")
        if isinstance(old, SpecificationDraftIssueCleanup):
            if not isinstance(new, SpecificationDraftIssueCleanup):
                raise TypeError("draft_cleanup_type_mismatch")
            if (old.request, old.execution_ref) != (new.request, new.execution_ref):
                raise ValueError("draft_cleanup_source_mismatch")
            if old.physical_claim == "claimed" and new.physical_claim != "claimed":
                raise ValueError("draft_cleanup_claim_regressed")
            if (
                old.physical_cleanup_attempted is True
                and new.physical_cleanup_attempted is not True
            ):
                raise ValueError("draft_cleanup_attempt_regressed")
            _require_cleanup_outcome_extension(
                old.physical_cleanup_outcome,
                new.physical_cleanup_outcome,
                attempted=old.physical_cleanup_attempted,
            )
        else:
            if not isinstance(new, SpecificationDraftPhysicalCleanup):
                raise TypeError("draft_cleanup_type_mismatch")
            if old.attempted and not new.attempted:
                raise ValueError("draft_cleanup_attempt_regressed")
            _require_cleanup_outcome_extension(
                old.outcome, new.outcome, attempted=old.attempted
            )
            if (old.root_locator, old.target_path, old.scratch_path) != (
                new.root_locator,
                new.target_path,
                new.scratch_path,
            ):
                raise ValueError("draft_cleanup_source_mismatch")
        before, after = old.evidence, new.evidence
        if before is not None and (
            after is None
            or after.effects[: len(before.effects)] != before.effects
            or (
                before.package_outcome == "published"
                and after.package_outcome != "published"
            )
            or after.cleanup_diagnostics[: len(before.cleanup_diagnostics)]
            != before.cleanup_diagnostics
        ):
            raise ValueError("draft_cleanup_history_regressed")
    for old, new in (
        (previous.physical_invocation, current.physical_invocation),
        (previous.protocol_invocation, current.protocol_invocation),
    ):
        if old.invocation_state != "not_invoked" and (
            new.invocation_state == "not_invoked"
            or new.responsibility != old.responsibility
        ):
            raise ValueError("draft_cleanup_invocation_regressed")
        if old.invocation_state in {"returned", "raised"} and new != old:
            raise ValueError("draft_cleanup_invocation_regressed")
        if new.diagnostics[: len(old.diagnostics)] != old.diagnostics:
            raise ValueError("draft_cleanup_invocation_regressed")
    if (
        current.cleanup_diagnostics[: len(previous.cleanup_diagnostics)]
        != previous.cleanup_diagnostics
    ):
        raise ValueError("draft_cleanup_diagnostics_regressed")


def _require_cleanup_outcome_extension(
    previous: str, current: str, *, attempted: bool | None
) -> None:
    # History validation only. A later complete observation can extend partial
    # knowledge; it is not permission to retry cleanup. Missing newer knowledge
    # is reported separately and cannot erase an already observed outcome.
    if (
        (previous == "completed" and current != "completed")
        or (previous == "incomplete" and current not in {"incomplete", "completed"})
        or (previous == "unknown" and attempted is True and current == "not_attempted")
    ):
        raise ValueError("draft_cleanup_outcome_regressed")


def _require_custody_extension(previous, current) -> None:
    if previous is None:
        return
    if current is None:
        raise ValueError("draft_custody_history_unavailable")
    for name in (
        "attempt_ref",
        "client_intent_id",
        "execution_ref",
        "context_ref",
        "root_locator",
        "manifest_locator",
        "manifest_sha256",
        "target_locator",
        "scratch_locator",
    ):
        old = getattr(previous, name)
        if old is not None and getattr(current, name) != old:
            raise ValueError("draft_custody_correlation_regressed")
    states = (
        "reserving",
        "reserved",
        "transferring",
        "transferred",
        "releasing",
        "released",
    )
    if (
        previous.custody_state in states
        and (
            current.custody_state not in states
            or states.index(current.custody_state)
            < states.index(previous.custody_state)
        )
    ) or (previous.custody_state == "failed" and current.custody_state != "failed"):
        raise ValueError("draft_custody_state_regressed")
    for kind, old, new in (
        ("physical", previous.physical, current.physical),
        ("protocol", previous.protocol, current.protocol),
    ):
        # Protocol's original attempt is terminal knowledge: a later release or
        # descriptor scan cannot repair an incomplete/unknown first disposal.
        # Physical cleanup's separately qualified progress stays unchanged.
        if (
            kind == "protocol"
            and old.owner_cleanup_attempted is True
            and new.owner_cleanup_outcome != old.owner_cleanup_outcome
        ):
            raise ValueError("draft_protocol_cleanup_history_regressed")
        if old.acquisition == "acquired" and new.acquisition != "acquired":
            raise ValueError("draft_custody_acquisition_regressed")
        if old.transfer in {"attempted", "completed"} and new.transfer not in (
            {"attempted", "completed"} if old.transfer == "attempted" else {"completed"}
        ):
            raise ValueError("draft_custody_transfer_regressed")
        if old.responsibility in {
            "custody",
            "admission",
        } and new.responsibility not in (
            {"custody", "admission"}
            if old.responsibility == "custody"
            else {"admission"}
        ):
            raise ValueError("draft_custody_responsibility_regressed")
        allowed = {
            "not_invoked": {"not_invoked", "invoked", "returned", "raised"},
            "invoked": {"invoked", "returned", "raised"},
            "returned": {"returned"},
            "raised": {"raised"},
        }
        if new.release_invocation not in allowed[old.release_invocation]:
            raise ValueError("draft_custody_release_regressed")
        if (
            old.owner_cleanup_attempted is not None
            and new.owner_cleanup_attempted
            not in ({True} if old.owner_cleanup_attempted else {False, True})
        ):
            raise ValueError("draft_custody_attempt_regressed")
        _require_cleanup_outcome_extension(
            old.owner_cleanup_outcome,
            new.owner_cleanup_outcome,
            attempted=old.owner_cleanup_attempted,
        )
        if new.diagnostics[: len(old.diagnostics)] != old.diagnostics:
            raise ValueError("draft_custody_diagnostics_regressed")
    if current.diagnostics[: len(previous.diagnostics)] != previous.diagnostics:
        raise ValueError("draft_custody_diagnostics_regressed")
    before, after = previous.physical_evidence, current.physical_evidence
    if before is not None and (
        after is None
        or after.effects[: len(before.effects)] != before.effects
        or after.cleanup_diagnostics[: len(before.cleanup_diagnostics)]
        != before.cleanup_diagnostics
        or (
            before.package_outcome == "published"
            and after.package_outcome != "published"
        )
        or (before.durability_confirmed and not after.durability_confirmed)
    ):
        raise ValueError("draft_custody_effects_regressed")
