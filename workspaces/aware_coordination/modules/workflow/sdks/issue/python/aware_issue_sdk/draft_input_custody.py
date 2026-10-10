"""Detached custody evidence. No lower-owner imports or cleanup authority."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .draft_package import IssueDraftPackageEvidence, _path
from .source_change import _digest


def _text(value):
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or unicodedata.normalize("NFC", value) != value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
    ):
        raise ValueError("Exact custody correlation required")
    if len(value.encode("utf-8")) > 1024:
        raise ValueError("Bounded custody correlation required")
    return value


def _diagnostics(value):
    if type(value) is not tuple:
        raise TypeError("Exact diagnostic tuple required")
    for item in value:
        _text(item)


def _coordinate(value, kind):
    if value is None:
        return
    if kind == "root":
        _text(value)
        path = Path(value)
        if not path.is_absolute() or str(path) != value or ".." in path.parts:
            raise ValueError("Absolute custody root required")
    elif kind == "digest":
        _digest(value)
    else:
        _path(value)


@dataclass(frozen=True, slots=True)
class IssueDraftInputResourceObservation:
    acquisition: str
    responsibility: str
    transfer: str
    release_invocation: str
    owner_cleanup_attempted: bool | None
    owner_cleanup_outcome: str
    diagnostics: tuple[str, ...]

    def __post_init__(self):
        for value, allowed in (
            (self.acquisition, {"not_acquired", "acquired", "unknown"}),
            (
                self.responsibility,
                {"caller", "custody", "admission", "other", "unknown"},
            ),
            (self.transfer, {"not_attempted", "attempted", "completed", "unknown"}),
            (self.release_invocation, {"not_invoked", "invoked", "returned", "raised"}),
            (
                self.owner_cleanup_outcome,
                {"not_attempted", "completed", "incomplete", "unknown"},
            ),
        ):
            if type(value) is not str or value not in allowed:
                raise ValueError("Invalid custody resource observation")
        if (
            self.owner_cleanup_attempted is not None
            and type(self.owner_cleanup_attempted) is not bool
        ):
            raise TypeError("Cleanup attempt must be bool or unknown")
        _diagnostics(self.diagnostics)


@dataclass(frozen=True, slots=True)
class IssueDraftInputCustodyObservation:
    attempt_ref: str
    client_intent_id: str
    execution_ref: str | None
    custody_state: str
    root_locator: str | None
    manifest_locator: str | None
    manifest_sha256: str | None
    target_locator: str | None
    scratch_locator: str | None
    physical: IssueDraftInputResourceObservation
    protocol: IssueDraftInputResourceObservation
    physical_evidence: IssueDraftPackageEvidence | None
    diagnostics: tuple[str, ...]
    context_ref: str | None = None

    def __post_init__(self):
        _text(self.attempt_ref)
        _text(self.client_intent_id)
        for value in (self.execution_ref, self.context_ref):
            if value is not None:
                _text(value)
        if self.custody_state not in {
            "reserving",
            "reserved",
            "transferring",
            "transferred",
            "releasing",
            "released",
            "failed",
            "unknown",
        }:
            raise ValueError("Invalid custody state")
        for value, kind in (
            (self.root_locator, "root"),
            (self.manifest_locator, "path"),
            (self.manifest_sha256, "digest"),
            (self.target_locator, "path"),
            (self.scratch_locator, "path"),
        ):
            _coordinate(value, kind)
        if (
            type(self.physical) is not IssueDraftInputResourceObservation
            or type(self.protocol) is not IssueDraftInputResourceObservation
        ):
            raise TypeError("Exact nested custody observations required")
        if (
            self.physical_evidence is not None
            and type(self.physical_evidence) is not IssueDraftPackageEvidence
        ):
            raise TypeError("Exact physical evidence required")
        _diagnostics(self.diagnostics)


@dataclass(frozen=True, slots=True)
class IssueDraftInputBinding:
    attempt_ref: str
    client_intent_id: str
    execution_ref: str | None
    context_ref: str | None
    root_locator: str
    manifest_locator: str
    manifest_sha256: str
    target_locator: str
    scratch_locator: str
    ordered_members: tuple[tuple[str, bytes], ...]

    def __post_init__(self):
        for value in (self.attempt_ref, self.client_intent_id):
            _text(value)
        for value in (self.execution_ref, self.context_ref):
            if value is not None:
                _text(value)
        _coordinate(self.root_locator, "root")
        _digest(self.manifest_sha256)
        for value in (self.manifest_locator, self.target_locator, self.scratch_locator):
            _path(value)
        # Reuse the same neutral bounded member/path policy, not a new evaluator.
        from .draft_package import IssueDraftPackageRequest

        IssueDraftPackageRequest(
            "binding",
            "sha256:" + "0" * 64,
            self.manifest_locator,
            self.manifest_sha256,
            self.target_locator,
            self.scratch_locator,
            self.ordered_members,
            "binding",
            self.client_intent_id,
        )


class IssueDraftInputCustodyRefusal(RuntimeError):
    def __init__(self, code, *, input_custody, cause_diagnostics=()):
        super().__init__(_text(code))
        if (
            input_custody is not None
            and type(input_custody) is not IssueDraftInputCustodyObservation
        ):
            raise TypeError("Exact custody observation required")
        _diagnostics(cause_diagnostics)
        self.code = code
        self.input_custody = input_custody
        self.cause_diagnostics = cause_diagnostics
