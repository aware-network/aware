"""Portable proposed-pairing observations, never a persisted association."""

import re
from dataclasses import dataclass
from enum import StrEnum

from aware_issue_runtime import IssueReadProjection

OPERATION_REF = "issue_sdk.observe_specification_iteration_binding"
PROVIDER_OPERATION_REF = "workflow.issue.specification_iteration_binding.observe"
REQUEST_CONTRACT = "aware.issue.specification-iteration-binding-observe-request.v1"
RESULT_CONTRACT = "aware.issue.specification-iteration-binding-observe-result.v1"


class IssueSpecificationIterationBindingError(ValueError):
    """Typed, read-only refusal. No publication or mutation has occurred."""

    def __init__(self, code: str, *, diagnostics: tuple[str, ...] = ()) -> None:
        self.code = code
        self.diagnostics = (code, *diagnostics)
        self.effect = "none"
        super().__init__(code)


class SpecificationIterationBindingOutcome(StrEnum):
    VERIFIED = "verified_proposed_pairing"
    REFUSED = "refused"
    UNAVAILABLE = "unavailable"


def _text(value: object, field: str) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(ord(c) < 32 or ord(c) == 127 for c in value)
    ):
        raise IssueSpecificationIterationBindingError(f"invalid_{field}")


def _digest(value: object, field: str) -> None:
    if type(value) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise IssueSpecificationIterationBindingError(f"invalid_{field}")


def _oid(value: object, field: str) -> None:
    if (
        type(value) is not str
        or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value) is None
    ):
        raise IssueSpecificationIterationBindingError(f"invalid_{field}")


@dataclass(frozen=True, slots=True)
class IssueSpecificationIterationBindingObserveRequest:
    issue_ref: str
    iteration_ref: str
    plan_revision: int
    plan_digest: str
    expected_specification_source_digest: str
    expected_issue_source_sha256: str
    expected_manifest_sha256: str
    expected_head: str

    def __post_init__(self) -> None:
        for field in ("issue_ref", "iteration_ref"):
            _text(getattr(self, field), field)
        if type(self.plan_revision) is not int or self.plan_revision < 1:
            raise IssueSpecificationIterationBindingError("invalid_plan_revision")
        for field in (
            "plan_digest",
            "expected_specification_source_digest",
            "expected_issue_source_sha256",
            "expected_manifest_sha256",
        ):
            _digest(getattr(self, field), field)
        _oid(self.expected_head, "expected_head")

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": REQUEST_CONTRACT,
            **{field: getattr(self, field) for field in self.__dataclass_fields__},
        }


@dataclass(frozen=True, slots=True)
class CommittedSpecificationMember:
    path: str
    blob_oid: str
    body_digest: str

    def __post_init__(self) -> None:
        _text(self.path, "member_path")
        if (
            self.path.startswith("/")
            or "\\" in self.path
            or any(part in {"", ".", ".."} for part in self.path.split("/"))
        ):
            raise IssueSpecificationIterationBindingError("invalid_member_path")
        _oid(self.blob_oid, "member_blob_oid")
        _digest(self.body_digest, "member_body_digest")

    def to_wire(self) -> dict[str, str]:
        return {
            "path": self.path,
            "blob_oid": self.blob_oid,
            "body_digest": self.body_digest,
        }


@dataclass(frozen=True, slots=True)
class IssueSpecificationIterationBindingObservation:
    request: IssueSpecificationIterationBindingObserveRequest
    outcome: SpecificationIterationBindingOutcome
    provider_ref: str
    diagnostics: tuple[str, ...] = ()
    phase_ref: str | None = None
    specification_source_digest: str | None = None
    source_context_digest: str | None = None
    snapshot_digest: str | None = None
    manifest_sha256: str | None = None
    head: str | None = None
    issue_projection: IssueReadProjection | None = None
    roots: tuple[str, ...] = ()
    committed_members: tuple[CommittedSpecificationMember, ...] = ()
    operation_ref: str = OPERATION_REF
    binding_persisted: bool = False
    approval_verified: bool = False
    work_authorized: bool = False

    def __post_init__(self) -> None:
        if type(self.request) is not IssueSpecificationIterationBindingObserveRequest:
            raise IssueSpecificationIterationBindingError("invalid_pairing_request")
        self.request.__post_init__()
        if (
            type(self.outcome) is not SpecificationIterationBindingOutcome
            or self.operation_ref != OPERATION_REF
        ):
            raise IssueSpecificationIterationBindingError("invalid_pairing_result")
        _text(self.provider_ref, "provider_ref")
        for field in ("binding_persisted", "approval_verified", "work_authorized"):
            if getattr(self, field) is not False:
                raise IssueSpecificationIterationBindingError(
                    "pairing_cannot_authorize"
                )
        for field in ("diagnostics", "roots", "committed_members"):
            value = getattr(self, field)
            if isinstance(value, (str, bytes)):
                raise IssueSpecificationIterationBindingError("invalid_pairing_result")
            object.__setattr__(self, field, tuple(value))
        for item in self.diagnostics:
            _text(item, "diagnostic")
        if self.outcome is not SpecificationIterationBindingOutcome.VERIFIED:
            if (
                not self.diagnostics
                or any(
                    value is not None
                    for value in (
                        self.phase_ref,
                        self.specification_source_digest,
                        self.source_context_digest,
                        self.snapshot_digest,
                        self.manifest_sha256,
                        self.head,
                        self.issue_projection,
                    )
                )
                or self.roots
                or self.committed_members
            ):
                raise IssueSpecificationIterationBindingError(
                    "refusal_cannot_carry_verified_evidence"
                )
            return
        _text(self.phase_ref, "phase_ref")
        if self.request.iteration_ref.rsplit("/iteration:", 1)[0] != self.phase_ref:
            raise IssueSpecificationIterationBindingError("pairing_phase_mismatch")
        for field in (
            "specification_source_digest",
            "source_context_digest",
            "snapshot_digest",
            "manifest_sha256",
        ):
            _digest(getattr(self, field), field)
        _oid(self.head, "head")
        if (
            self.specification_source_digest
            != self.request.expected_specification_source_digest
            or self.manifest_sha256 != self.request.expected_manifest_sha256
            or self.head != self.request.expected_head
            or type(self.issue_projection) is not IssueReadProjection
            or self.issue_projection.issue_ref != self.request.issue_ref
            or self.issue_projection.source_digest
            != self.request.expected_issue_source_sha256
        ):
            raise IssueSpecificationIterationBindingError("pairing_evidence_mismatch")
        # Issue owns parsing. Check the complete returned projection structure,
        # not just the identity/digest attributes on a partially built object.
        self.issue_projection.to_payload(include_raw_markdown=False)
        _text(self.issue_projection.title, "issue_title")
        _text(self.issue_projection.status, "issue_status")
        if self.issue_projection.owner_ref is not None:
            _text(self.issue_projection.owner_ref, "issue_owner")
        if type(self.issue_projection.ownership_scope) is not tuple:
            raise IssueSpecificationIterationBindingError("invalid_issue_scope")
        for path in self.issue_projection.ownership_scope:
            _text(path, "issue_scope_path")
        if not self.roots or not self.committed_members:
            raise IssueSpecificationIterationBindingError(
                "pairing_source_evidence_missing"
            )
        for root in self.roots:
            _text(root, "root")
        if self.roots != tuple(sorted(set(self.roots))):
            raise IssueSpecificationIterationBindingError(
                "pairing_roots_not_unique_ordered"
            )
        for member in self.committed_members:
            if type(member) is not CommittedSpecificationMember:
                raise IssueSpecificationIterationBindingError(
                    "invalid_committed_member"
                )
            member.__post_init__()
            if not any(member.path.startswith(root + "/") for root in self.roots):
                raise IssueSpecificationIterationBindingError(
                    "member_outside_selection"
                )
        paths = tuple(m.path for m in self.committed_members)
        if paths != tuple(sorted(set(paths))):
            raise IssueSpecificationIterationBindingError(
                "pairing_members_not_unique_ordered"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": RESULT_CONTRACT,
            "operation_ref": self.operation_ref,
            "request": self.request.to_wire(),
            "outcome": self.outcome.value,
            "provider_ref": self.provider_ref,
            "diagnostics": list(self.diagnostics),
            "phase_ref": self.phase_ref,
            "specification_source_digest": self.specification_source_digest,
            "source_context_digest": self.source_context_digest,
            "snapshot_digest": self.snapshot_digest,
            "manifest_sha256": self.manifest_sha256,
            "head": self.head,
            "issue_projection": None
            if self.issue_projection is None
            else self.issue_projection.to_payload(include_raw_markdown=False),
            "roots": list(self.roots),
            "committed_members": [m.to_wire() for m in self.committed_members],
            "binding_persisted": False,
            "approval_verified": False,
            "work_authorized": False,
            "horizon": "bounded_revalidated_read_not_future_authority",
        }


def observe_pairing(
    provider: object, request: IssueSpecificationIterationBindingObserveRequest
) -> IssueSpecificationIterationBindingObservation:
    """Optional port: absent Service/other providers are not an FS fallback."""
    try:
        if type(request) is not IssueSpecificationIterationBindingObserveRequest:
            raise ValueError("wrong request type")
        request.__post_init__()
    except (AttributeError, TypeError, ValueError) as error:
        raise IssueSpecificationIterationBindingError(
            "pairing_request_invalid"
        ) from error
    operation = getattr(provider, "observe_specification_iteration_binding", None)
    if not callable(operation):
        raise IssueSpecificationIterationBindingError("pairing_authority_unavailable")
    result = operation(request)
    try:
        if type(result) is not IssueSpecificationIterationBindingObservation:
            raise ValueError("wrong result type")
        result.__post_init__()
        if result.request != request:
            raise ValueError("uncorrelated response")
        return result
    except (AttributeError, TypeError, ValueError) as error:
        raise IssueSpecificationIterationBindingError(
            "pairing_result_invalid"
        ) from error
