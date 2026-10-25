"""Explicit private selected-capture replay, with nonrefundable root charges.

This is observed byte correlation, not immutable custody or native admission.
The default scanner/replay paths do not select this composition.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from . import _product_member_capture as capture
from . import _product_member_replay as replay

ROOT_BYTES = 8388608
_PINS = (
    (
        Path(capture.__file__),
        "5267122f481995f5fed7a846866a72dc6f34cbb61d9cbecae196faa52c26284f",
    ),
    (
        Path(replay.__file__),
        "38d5825f641822f62d7faaff00fe04b80595eb64c136585d02f8c22bbeb14983",
    ),
)


@dataclass(frozen=True)
class _CaptureWitness:
    captured: capture.ProvisionalMemberCapture
    projection: tuple
    item: capture.original.tarfile.TarInfo
    entry: capture.original._Entry
    item_snapshot: tuple


@dataclass
class _CaptureSelection:
    pin: tuple
    witness: _CaptureWitness | None = None

    def publish(self, value, state, item, entry):
        if (
            self.witness is not None
            or type(value) is not capture.ProvisionalMemberCapture
        ):
            raise ValueError("original_single_selected_capture_required")
        if value.original_pin is not self.pin or value.original_state is not state:
            raise ValueError("original_capture_selection_binding_required")
        projection = (
            value.original_pin,
            value.original_chunks,
            value.original_digest_return,
            value.original_eof,
            value.original_close_return,
            value.original_state,
        )
        self.witness = _CaptureWitness(
            value, projection, item, entry, capture.original._snapshot(item)
        )


@dataclass(frozen=True)
class CapturedReplayObservation:
    original_provisional_capture: capture.ProvisionalMemberCapture
    original_replay: replay.MemberReplayObservation
    original_chunks: tuple[bytes, ...]
    cumulative_reserved_bytes: int
    enclosing_flow_correlated: bool = True
    final_guards_verified: bool = True
    provisional: bool = False
    authorizes_native_profile: bool = False
    cleanup: str = "not_observed"


class CaptureMountError(RuntimeError):
    def __init__(self, handle, error, provisional, outcome, charged):
        super().__init__("private_product_capture_mount")
        self.original_handle = handle
        self.original_replay_error = error
        self.original_provisional_capture = provisional
        self.original_replay_outcome = outcome
        self.cumulative_reserved_bytes = charged
        self.primary_cause = error
        self.member_bytes_accepted = False
        self.authorizes_retry = False
        self.authorizes_native_profile = False
        self.cleanup = "not_observed"


class _OriginalCaptureReceiver(replay._OriginalMemberReplayReceiver):
    @property
    def _capture_reserved_bytes(self):
        # Charges derive from the sole permanent replay ledger. No refundable
        # secondary counter, and failures/releases cannot remove an entry.
        return sum(attempt.member.pin[1] for attempt in self._replays.values())

    def _new_attempt(self, member, record):
        if (
            member.pin[1] > capture.SMALL_BYTES
            or self._capture_reserved_bytes + member.pin[1] > ROOT_BYTES
        ):
            raise ValueError("original_selected_capture_budget_exceeded")
        vars(record)["_capture_selection"] = _CaptureSelection(member.pin)
        return super()._new_attempt(member, record)

    @staticmethod
    def _invoke(record):
        selection = vars(record).get("_capture_selection")
        if selection is None:
            return replay.members.catalog._OriginalCatalogReceiver._invoke(record)
        if type(selection) is not _CaptureSelection:
            raise ValueError("original_capture_selection_required")
        return replay.catalog.joined._observe_product_catalog_flow(
            record.request,
            maximum_decoded_bytes=record.maximum,
            _selection=selection,
        )

    def _guards(self, record):
        returned = super()._guards(record)
        for path, digest in _PINS:
            value = replay.catalog.base._FILE(path, digest)
            record.guards += (value,)
            returned += (value,)
        return returned

    @staticmethod
    def _correlate_capture(attempt, outcome):
        selection = vars(attempt.flow).get("_capture_selection")
        if (
            type(selection) is not _CaptureSelection
            or selection.pin is not attempt.member.pin
        ):
            raise ValueError("original_capture_attempt_binding_required")
        witness = selection.witness
        if type(witness) is not _CaptureWitness:
            raise ValueError("original_capture_witness_required")
        value = witness.captured
        if type(value) is not capture.ProvisionalMemberCapture:
            raise ValueError("original_provisional_capture_required")
        current = (
            value.original_pin,
            value.original_chunks,
            value.original_digest_return,
            value.original_eof,
            value.original_close_return,
            value.original_state,
        )
        if (
            any(a is not b for a, b in zip(current, witness.projection, strict=True))
            or value.provisional is not True
            or value.enclosing_flow_verified is not False
            or value.final_guards_verified is not False
            or value.authorizes_native_profile is not False
            or value.cleanup != "not_observed"
            or outcome.original_replay_observation is not attempt.flow.returned
            or outcome.selected_pin is not selection.pin
        ):
            raise ValueError("original_capture_projection_changed")
        account = outcome.original_replay_observation.original_member_account
        state = value.original_state
        if (
            state.archive is not account.original_archive
            or state.header_policy is not account.original_header_policy
            or not any(entry is witness.entry for entry in account.entries)
            or witness.entry.original_item is not witness.item
            or witness.entry.snapshot != witness.item_snapshot
            or capture.original._snapshot(witness.item) != witness.item_snapshot
            or witness.entry.name != selection.pin[0]
            or witness.entry.size != selection.pin[1]
            or witness.entry.sha256 != selection.pin[2]
            or value.original_digest_return != selection.pin[2]
            or value.original_close_return != ("member", None)
            or type(value.original_eof) is not tuple
            or len(value.original_eof) != 3
            or type(value.original_eof[0]) is not capture.original.tarfile.ExFileObject
            or value.original_eof[0].closed is not True
            or value.original_eof[1] != b""
            or type(value.original_eof[1]) is not bytes
            or type(value.original_eof[2]) is not int
            or value.original_eof[2] != selection.pin[1]
            or type(value.original_chunks) is not tuple
        ):
            raise ValueError("original_capture_catalog_or_terminal_binding_required")
        digest = hashlib.sha256()
        size = 0
        for body in value.original_chunks:
            if type(body) is not bytes or not 0 < len(body) <= capture.original.WINDOW:
                raise ValueError("original_bounded_capture_chunk_required")
            size += len(body)
            if size > capture.SMALL_BYTES or size > selection.pin[1]:
                raise ValueError("original_capture_size_exceeded")
            digest.update(body)
        if size != selection.pin[1] or digest.hexdigest() != selection.pin[2]:
            raise ValueError("original_capture_body_correlation_required")
        return value

    def capture_member(self, handle):
        outcome = None
        try:
            outcome = self.replay_member(handle)
            attempt = self._replays[handle]
            provisional = self._correlate_capture(attempt, outcome)
            return CapturedReplayObservation(
                provisional,
                outcome,
                provisional.original_chunks,
                self._capture_reserved_bytes,
            )
        except BaseException as error:
            # Do not inspect another execution's private registry on an
            # affinity/reentrancy refusal, or expose the live attempt record.
            provisional = None
            if outcome is not None or (
                type(error) is replay.MemberReplayError and error.disposition == "spent"
            ):
                attempt = self._replays.get(handle)
                if attempt is not None:
                    selection = vars(attempt.flow).get("_capture_selection")
                    if (
                        type(selection) is _CaptureSelection
                        and selection.witness is not None
                    ):
                        provisional = selection.witness.captured
            raise CaptureMountError(
                handle, error, provisional, outcome, self._capture_reserved_bytes
            ) from error
