"""Immutable namespace evidence only; no lock, custody, dispatch or authority.

Original nested owner types resolve in private_directory's closed codec registry.
Constructing or decoding these values never enrolls a physical handle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .confined_entry import (
    ConfinedEntryObservation,
    EntryAncestorBookends,
    EntryCursorCleanup,
    EntryRequestSnapshot,
    EntryResource,
    EntryStat,
)
from .confined_mutation import ConfinedFileReadCleanup
from .retained_file_sequence import (
    ConfinedSequenceLimits,
    ConfinedSequencePrimaryFailure,
    ConfinedSequenceResourceEvidence,
    ConfinedSequenceStep,
)

if TYPE_CHECKING:
    from .private_directory import (
        PrivateDirectoryBinding,
        PrivateDirectoryRefusalEvidence,
        PrivateFileReadResult,
        PrivateSequenceBinding,
        PrivateSequenceCleanup,
    )


@dataclass(frozen=True, slots=True)
class PrivateNamespaceControlObservation:
    contract: Literal["aware.filesystem.private-namespace-control.v1"]
    observation_ref: str
    directory: PrivateDirectoryBinding
    control_path: Literal[".aware-source-authority.v1"]
    profile: Literal["aware.filesystem.local-cooperating-source.v1"]
    control_stat: EntryStat
    epoch: int
    original_read: PrivateFileReadResult
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class PrivateNamespaceLimits:
    inventory_entries: int
    name_bytes: int
    roster_bytes: int
    inventory_wire_bytes: int
    member_bytes: int
    owned_descriptor_budget: int
    cursor_resource_budget: Literal[2]
    sequence_limits: ConfinedSequenceLimits


@dataclass(frozen=True, slots=True)
class PrivateNamespaceBinding:
    contract: Literal["aware.filesystem.private-namespace-binding.v1"]
    transaction_ref: str
    provider_generation: str
    process_id: int
    thread_id: int
    directory: PrivateDirectoryBinding
    control_before: PrivateNamespaceControlObservation
    limits: PrivateNamespaceLimits


@dataclass(frozen=True, slots=True)
class PrivateNamespacePhysicalEffect:
    effect_ref: str
    kind: Literal["control_epoch_write", "control_fsync"]
    path: Literal[".aware-source-authority.v1"]
    dispatch: Literal["not_attempted", "attempted", "returned"]
    effect: Literal["none", "applied", "unknown"]
    durability: Literal["not_confirmed", "confirmed", "unknown"]
    epoch_before: int
    epoch_after: int | None
    requested_bytes: int | None
    returned_bytes: int | None
    cause: ConfinedSequencePrimaryFailure


@dataclass(frozen=True, slots=True)
class PrivateNamespaceInventoryMember:
    name: str
    stat: EntryStat


@dataclass(frozen=True, slots=True)
class PrivateNamespaceInventoryObservation:
    contract: Literal["aware.filesystem.private-namespace-inventory.v1"]
    transaction_ref: str
    observation_ref: str
    original_roster: ConfinedEntryObservation
    members: tuple[PrivateNamespaceInventoryMember, ...]
    complete: bool
    bookends_agree: bool
    encoded_bytes: int
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class PrivateNamespaceFootprint:
    contract: Literal["aware.filesystem.private-namespace-footprint.v1"]
    transaction_ref: str
    sequence_binding: PrivateSequenceBinding
    control_effect_paths: tuple[str, ...]
    ordered_steps: tuple[ConfinedSequenceStep, ...]
    scratch_paths: tuple[str, ...]
    body_bytes: int
    encoded_metadata_upper_bound: int
    peak_descriptors: int
    cursor_records: int
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class PrivateNamespaceTransactionObservation:
    contract: Literal["aware.filesystem.private-namespace-observation.v1"]
    binding: PrivateNamespaceBinding
    phase: Literal[
        "reserved",
        "prepared",
        "armed",
        "executing",
        "completed",
        "releasing",
        "released",
        "retired",
        "unknown",
    ]
    lock: Literal["not_acquired", "held", "confirmed_released", "unknown"]
    epoch_effects: tuple[PrivateNamespacePhysicalEffect, ...]
    footprint: PrivateNamespaceFootprint | None
    active_sequence_ref: str | None
    resources: tuple[ConfinedSequenceResourceEvidence, ...]
    primary_failure: ConfinedSequencePrimaryFailure
    ledger_complete: bool
    authorizes_dispatch: Literal[False]


@dataclass(frozen=True, slots=True)
class PrivateNamespaceCleanup:
    contract: Literal["aware.filesystem.private-namespace-cleanup.v1"]
    observation: PrivateNamespaceTransactionObservation
    child_cleanup: PrivateSequenceCleanup | None
    lock_release: Literal["not_acquired", "confirmed", "unknown"]
    control_close: Literal["not_acquired", "confirmed", "unknown"]
    root_close: Literal["not_acquired", "confirmed", "unknown"]
    secondary_failures: tuple[ConfinedSequencePrimaryFailure, ...]
    outcome: Literal["not_acquired", "confirmed", "unknown"]


@dataclass(frozen=True, slots=True)
class PrivateNamespaceAncestorPrefix:
    coordinate: str
    named_before: EntryStat | None
    opened_before: EntryStat | None
    named_after: EntryStat | None
    opened_after: EntryStat | None
    under_selected_root: bool | None
    resource_ref: str | None
    parent_resource_ref: str | None


@dataclass(frozen=True, slots=True)
class PrivateNamespaceEntryPrefix:
    root_before: EntryStat | None
    root_after: EntryStat | None
    entry_locator: str | None
    entry_before: EntryStat | None
    entry_after: EntryStat | None
    opened_directory: EntryStat | None
    kind: Literal["directory", "file", "symlink"] | None
    ancestors: tuple[PrivateNamespaceAncestorPrefix, ...]
    ancestor_bookends: tuple[EntryAncestorBookends, ...]
    children_before: tuple[str, ...] | None
    children_after: tuple[str, ...] | None
    link_text_bytes: bytes | None
    descriptor_resources: tuple[EntryResource, ...] | None
    cursor_resources: tuple[EntryResource, ...] | None
    resource_evidence_available: bool


@dataclass(frozen=True, slots=True)
class PrivateNamespaceEntryFailure:
    contract: Literal["aware.filesystem.private-namespace-entry-failure.v1"]
    request: EntryRequestSnapshot | None
    observation_ref: str | None
    phase: str
    prefix: PrivateNamespaceEntryPrefix
    roster_prefix: tuple[str, ...]
    raw_name_bytes: bytes | None
    raw_name_encoding: Literal["filesystem_surrogateescape", "raw_bytes", "unavailable"]
    descriptor_cleanup: ConfinedFileReadCleanup
    cursor_cleanup: EntryCursorCleanup
    original_cause: ConfinedSequencePrimaryFailure


@dataclass(frozen=True, slots=True)
class PrivateNamespaceRefusalEvidence:
    contract: Literal["aware.filesystem.private-namespace-refusal.v1"]
    code: str
    stage: str
    primary_failure: ConfinedSequencePrimaryFailure
    control: PrivateNamespaceControlObservation | None
    observation: PrivateNamespaceTransactionObservation | None
    inventory_prefix: PrivateNamespaceInventoryObservation | None
    original_private_failure: PrivateDirectoryRefusalEvidence | None
    original_entry_failure: PrivateNamespaceEntryFailure | None
    cleanup: PrivateNamespaceCleanup | None
    input_custody: Literal["not_acquired", "owned", "borrowed", "unknown"]
    ledger_complete: bool
    authorizes_retry: Literal[False]


__all__ = [  # noqa: RUF022 - preserve the accepted contract declaration order
    "PrivateNamespaceControlObservation",
    "PrivateNamespaceLimits",
    "PrivateNamespaceBinding",
    "PrivateNamespacePhysicalEffect",
    "PrivateNamespaceInventoryMember",
    "PrivateNamespaceInventoryObservation",
    "PrivateNamespaceFootprint",
    "PrivateNamespaceTransactionObservation",
    "PrivateNamespaceCleanup",
    "PrivateNamespaceAncestorPrefix",
    "PrivateNamespaceEntryPrefix",
    "PrivateNamespaceEntryFailure",
    "PrivateNamespaceRefusalEvidence",
]
