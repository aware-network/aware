"""Native Phase-definition document authority with optional operational facts."""
# pyright: reportUnusedCallResult=false

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from .dependencies import GoalDependencyRelation
from .phase_codec import decode_goal_phase_bundle, goal_phase_bundle_to_wire
from .phase_contracts import (
    GoalLanePhaseGate,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
)

GOAL_PHASE_NATIVE_DOCUMENT_SCHEMA = "aware.goal.lane-phase.document.v1"
GOAL_PHASE_NATIVE_DOCUMENT_V2_SCHEMA = "aware.goal.lane-phase.document.v2"
GOAL_PHASE_NATIVE_DOCUMENT_V3_SCHEMA = "aware.goal.lane-phase.document.v3"
GOAL_PHASE_NATIVE_AUTHORITY_PROFILE = "native_phase_definition_v1"
GOAL_PHASE_NATIVE_COMPATIBILITY_PROFILE = "markdown_legacy_v1"
GOAL_PHASE_EXECUTION_AUTHORITY_SCHEMA = "aware.goal.phase-execution-authority.v1"
GOAL_PHASE_OPERATION_JOURNAL_SCHEMA = "aware.goal.phase-operation-journal.v1"
GOAL_PHASE_OPERATION_JOURNAL_ENTRY_SCHEMA = (
    "aware.goal.phase-operation-journal-entry.v1"
)
GOAL_PHASE_NATIVE_START_MARKER = b"<!-- aware.goal.lane-phase.document.v1:start -->"
GOAL_PHASE_NATIVE_END_MARKER = b"<!-- aware.goal.lane-phase.document.v1:end -->"
_CARRIER_OPEN = GOAL_PHASE_NATIVE_START_MARKER + b"\n```json\n"
_CARRIER_CLOSE = b"\n```\n" + GOAL_PHASE_NATIVE_END_MARKER + b"\n"

_MEMBER_KEY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_TYPED_REF = re.compile(r"^[a-z][a-z0-9-]*:sha256:[0-9a-f]{64}$")


class GoalPhaseNativeDocumentError(ValueError):
    """Native Phase document bytes or authority bindings are invalid."""


class GoalPhaseNativeCarrierError(ValueError):
    """Canonical terminal framing around a native document is invalid."""


@dataclass(frozen=True, slots=True)
class GoalPhaseExecutionAuthorityV1:
    """Durable retirement of legacy execution, independent of presentation."""

    source_execution_authority_profile: str
    parity_ref: str
    proposal_aggregate_ref: str
    coordinator_acceptance_ref: str
    authority_ref: str = field(init=False)
    target_execution_authority_profile: str = "phase_native_operational_v1"
    legacy_execution_disposition: str = "retired"
    schema_id: str = GOAL_PHASE_EXECUTION_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseExecutionAuthorityV1:
            raise GoalPhaseNativeDocumentError("execution authority type must be exact")
        if self.schema_id != GOAL_PHASE_EXECUTION_AUTHORITY_SCHEMA:
            raise GoalPhaseNativeDocumentError("unsupported execution authority schema")
        if self.source_execution_authority_profile not in {
            "legacy_goal_lane_row_v1",
            "hybrid_legacy_row_phase_native_v1",
        }:
            raise GoalPhaseNativeDocumentError("invalid source execution authority")
        if self.target_execution_authority_profile != "phase_native_operational_v1":
            raise GoalPhaseNativeDocumentError("invalid target execution authority")
        if self.legacy_execution_disposition != "retired":
            raise GoalPhaseNativeDocumentError("legacy execution must be retired")
        _qualified(self.parity_ref, "parity_ref", "goal-phase-native-compatibility-parity")
        _qualified(
            self.proposal_aggregate_ref,
            "proposal_aggregate_ref",
            "goal-phase-native-operational-bootstrap-proposal",
        )
        _qualified(
            self.coordinator_acceptance_ref,
            "coordinator_acceptance_ref",
            "goal-phase-native-operational-bootstrap-coordinator-acceptance",
        )
        object.__setattr__(
            self,
            "authority_ref",
            "goal-phase-execution-authority:"
            + _digest(_canonical(_execution_authority_body(self))),
        )


@dataclass(frozen=True, slots=True)
class GoalLanePhaseDefinitionV1:
    """Durable Phase/Gate meaning, independent of lifecycle availability."""

    coordinate: GoalPhaseCoordinate
    ordinal: int
    gate: GoalLanePhaseGate
    title: str | None = None
    intent: str | None = None
    definition_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseDefinitionV1:
            raise GoalPhaseNativeDocumentError("definition type must be exact")
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("coordinate must be GoalPhaseCoordinate")
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise GoalPhaseNativeDocumentError("ordinal must be nonnegative integer")
        if type(self.gate) is not GoalLanePhaseGate:
            raise TypeError("gate must be GoalLanePhaseGate")
        _ = _optional_text(self.title, "title")
        _ = _optional_text(self.intent, "intent")
        object.__setattr__(
            self,
            "definition_ref",
            "goal-phase-definition:" + _digest(_canonical(_definition_body(self))),
        )


@dataclass(frozen=True, slots=True)
class GoalPhaseUnresolvedDependencyV1:
    """Authored edge retained without a prerequisite Gate digest or eligibility."""

    owner_goal_tag: str
    dependency_key: str
    dependent: GoalPhaseCoordinate
    prerequisite: GoalPhaseCoordinate
    relation: GoalDependencyRelation
    reason: str
    evidence_refs: tuple[str, ...] = ()
    resolution_state: str = "required_gate_digest_unresolved"
    eligibility_effect: str = "none"

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseUnresolvedDependencyV1:
            raise GoalPhaseNativeDocumentError(
                "unresolved dependency type must be exact"
            )
        _ = _text(self.owner_goal_tag, "owner_goal_tag")
        _ = _member_key(self.dependency_key, "dependency_key")
        if type(self.dependent) is not GoalPhaseCoordinate:
            raise TypeError("dependent must be GoalPhaseCoordinate")
        if type(self.prerequisite) is not GoalPhaseCoordinate:
            raise TypeError("prerequisite must be GoalPhaseCoordinate")
        if self.dependent.goal_tag != self.owner_goal_tag:
            raise GoalPhaseNativeDocumentError(
                "dependent coordinate must belong to owner Goal"
            )
        if self.dependent == self.prerequisite:
            raise GoalPhaseNativeDocumentError("dependency cannot depend on itself")
        if type(self.relation) is not GoalDependencyRelation:
            raise TypeError("relation must be GoalDependencyRelation")
        _ = _text(self.reason, "reason")
        _ = _tokens(self.evidence_refs, "evidence_refs")
        if self.resolution_state != "required_gate_digest_unresolved":
            raise GoalPhaseNativeDocumentError("invalid unresolved dependency state")
        if self.eligibility_effect != "none":
            raise GoalPhaseNativeDocumentError(
                "unresolved dependency cannot produce eligibility"
            )


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDocumentV1:
    """One native Phase definition graph plus independently qualified facts."""

    goal_tag: str
    compatibility_projection_sha256: str
    compatibility_projection_byte_count: int
    definitions: tuple[GoalLanePhaseDefinitionV1, ...]
    operational_bundle: GoalPhaseContractBundleV1
    unresolved_dependencies: tuple[GoalPhaseUnresolvedDependencyV1, ...]
    source_refs: tuple[str, ...]
    document_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_NATIVE_DOCUMENT_SCHEMA
    authority_profile: str = GOAL_PHASE_NATIVE_AUTHORITY_PROFILE
    compatibility_profile: str = GOAL_PHASE_NATIVE_COMPATIBILITY_PROFILE

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_NATIVE_DOCUMENT_SCHEMA:
            raise GoalPhaseNativeDocumentError("unsupported native document schema")
        if self.authority_profile != GOAL_PHASE_NATIVE_AUTHORITY_PROFILE:
            raise GoalPhaseNativeDocumentError("unsupported authority profile")
        if self.compatibility_profile != GOAL_PHASE_NATIVE_COMPATIBILITY_PROFILE:
            raise GoalPhaseNativeDocumentError("unsupported compatibility profile")
        _ = _text(self.goal_tag, "goal_tag")
        _ = _sha(
            self.compatibility_projection_sha256,
            "compatibility_projection_sha256",
        )
        if (
            type(self.compatibility_projection_byte_count) is not int
            or self.compatibility_projection_byte_count < 1
        ):
            raise GoalPhaseNativeDocumentError(
                "compatibility_projection_byte_count must be positive integer"
            )
        if type(self.definitions) is not tuple or not self.definitions:
            raise GoalPhaseNativeDocumentError("definitions must be non-empty tuple")
        definitions: dict[GoalPhaseCoordinate, GoalLanePhaseDefinitionV1] = {}
        lane_ordinals: set[tuple[str, int]] = set()
        for definition in self.definitions:
            if type(definition) is not GoalLanePhaseDefinitionV1:
                raise TypeError("definitions must contain exact definitions")
            definition.__post_init__()
            if definition.coordinate.goal_tag != self.goal_tag:
                raise GoalPhaseNativeDocumentError(
                    "definition belongs to a different Goal"
                )
            if definition.coordinate in definitions:
                raise GoalPhaseNativeDocumentError("duplicate Phase definition")
            ordinal_key = (definition.coordinate.lane_key, definition.ordinal)
            if ordinal_key in lane_ordinals:
                raise GoalPhaseNativeDocumentError("duplicate lane ordinal")
            definitions[definition.coordinate] = definition
            lane_ordinals.add(ordinal_key)
        if type(self.operational_bundle) is not GoalPhaseContractBundleV1:
            raise TypeError("operational_bundle must be GoalPhaseContractBundleV1")
        self.operational_bundle.__post_init__()
        for phase in self.operational_bundle.phases:
            definition = definitions.get(phase.coordinate)
            if definition is None:
                raise GoalPhaseNativeDocumentError(
                    "operational Phase lacks an admitted definition"
                )
            if definition.title is None or definition.intent is None:
                raise GoalPhaseNativeDocumentError(
                    "operational Phase requires complete title and intent definition"
                )
            if (
                phase.title != definition.title
                or phase.intent != definition.intent
                or phase.ordinal != definition.ordinal
                or phase.gate != definition.gate
            ):
                raise GoalPhaseNativeDocumentError(
                    "operational Phase differs from admitted definition"
                )
        for dependency in self.operational_bundle.dependencies:
            dependent = definitions.get(dependency.dependent)
            if dependent is None:
                raise GoalPhaseNativeDocumentError(
                    "dependency dependent Phase is not defined"
                )
            prerequisite = definitions.get(dependency.prerequisite)
            if (
                dependency.prerequisite.goal_tag == self.goal_tag
                and prerequisite is None
            ):
                raise GoalPhaseNativeDocumentError(
                    "same-Goal dependency prerequisite Phase is not defined"
                )
            if (
                prerequisite is not None
                and prerequisite.gate.gate_digest
                != dependency.required_gate_digest
            ):
                raise GoalPhaseNativeDocumentError(
                    "dependency prerequisite Gate digest differs from definition"
                )
        if type(self.unresolved_dependencies) is not tuple:
            raise TypeError("unresolved_dependencies must be exact tuple")
        resolved_keys = {
            (item.owner_goal_tag, item.dependency_key)
            for item in self.operational_bundle.dependencies
        }
        unresolved_keys: set[tuple[str, str]] = set()
        for dependency in self.unresolved_dependencies:
            if type(dependency) is not GoalPhaseUnresolvedDependencyV1:
                raise TypeError("unresolved_dependencies contain invalid value")
            dependency.__post_init__()
            if dependency.dependent not in definitions:
                raise GoalPhaseNativeDocumentError(
                    "unresolved dependent Phase is not defined"
                )
            if dependency.prerequisite in definitions:
                raise GoalPhaseNativeDocumentError(
                    "defined prerequisite Gate cannot remain unresolved"
                )
            key = (dependency.owner_goal_tag, dependency.dependency_key)
            if key in resolved_keys or key in unresolved_keys:
                raise GoalPhaseNativeDocumentError("duplicate dependency identity")
            unresolved_keys.add(key)
        _ = _tokens(self.source_refs, "source_refs")
        object.__setattr__(
            self,
            "document_ref",
            "goal-phase-document:" + _digest(_canonical(_document_body(self))),
        )


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDocumentV2:
    """Native graph after an explicit execution-authority transition."""

    goal_tag: str
    compatibility_projection_sha256: str
    compatibility_projection_byte_count: int
    definitions: tuple[GoalLanePhaseDefinitionV1, ...]
    operational_bundle: GoalPhaseContractBundleV1
    unresolved_dependencies: tuple[GoalPhaseUnresolvedDependencyV1, ...]
    source_refs: tuple[str, ...]
    execution_authority: GoalPhaseExecutionAuthorityV1
    document_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_NATIVE_DOCUMENT_V2_SCHEMA
    authority_profile: str = GOAL_PHASE_NATIVE_AUTHORITY_PROFILE
    compatibility_profile: str = GOAL_PHASE_NATIVE_COMPATIBILITY_PROFILE

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseNativeDocumentV2:
            raise GoalPhaseNativeDocumentError("V2 document type must be exact")
        if self.schema_id != GOAL_PHASE_NATIVE_DOCUMENT_V2_SCHEMA:
            raise GoalPhaseNativeDocumentError("unsupported V2 document schema")
        # V1 remains the single graph validator; V2 adds only execution authority.
        GoalPhaseNativeDocumentV1(
            goal_tag=self.goal_tag,
            compatibility_projection_sha256=self.compatibility_projection_sha256,
            compatibility_projection_byte_count=self.compatibility_projection_byte_count,
            definitions=self.definitions,
            operational_bundle=self.operational_bundle,
            unresolved_dependencies=self.unresolved_dependencies,
            source_refs=self.source_refs,
        )
        if type(self.execution_authority) is not GoalPhaseExecutionAuthorityV1:
            raise TypeError("execution_authority must be GoalPhaseExecutionAuthorityV1")
        self.execution_authority.__post_init__()
        object.__setattr__(
            self,
            "document_ref",
            "goal-phase-document:" + _digest(_canonical(_document_body_v2(self))),
        )


@dataclass(frozen=True, slots=True)
class GoalPhaseOperationJournalEntryV1:
    """Structural record of one operation; it does not attest its issuer."""

    operation_kind: str
    decision: str
    coordinate: GoalPhaseCoordinate
    gate_digest: str
    source_preimage_ref: str
    actor_ref: str
    action_occurrence_ref: str
    policy_ref: str
    policy_digest: str
    idempotency_key: str
    delta_ref: str
    event_ref: str
    approval_entry_ref: str | None = None
    agent_run_request_ref: str | None = None
    assignment_ref: str | None = None
    execution_ref: str | None = None
    entry_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_OPERATION_JOURNAL_ENTRY_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseOperationJournalEntryV1:
            raise GoalPhaseNativeDocumentError("journal entry type must be exact")
        if self.schema_id != GOAL_PHASE_OPERATION_JOURNAL_ENTRY_SCHEMA:
            raise GoalPhaseNativeDocumentError("unsupported journal entry schema")
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("journal coordinate must be exact")
        _ = _sha(self.gate_digest, "gate_digest")
        _ = _qualified(self.source_preimage_ref, "source_preimage_ref", "goal-phase-document")
        _ = _text(self.actor_ref, "actor_ref")
        for name, value in (
            ("action_occurrence_ref", self.action_occurrence_ref),
            ("policy_ref", self.policy_ref),
            ("delta_ref", self.delta_ref),
            ("event_ref", self.event_ref),
        ):
            _ = _typed_ref(value, name)
        _ = _sha(self.policy_digest, "policy_digest")
        _ = _text(self.idempotency_key, "idempotency_key")
        if self.operation_kind == "approve_pursuit" and self.decision == "approve":
            if any(
                value is not None
                for value in (
                    self.approval_entry_ref,
                    self.agent_run_request_ref,
                    self.assignment_ref,
                    self.execution_ref,
                )
            ):
                raise GoalPhaseNativeDocumentError("approval has foreign chain fields")
        elif self.operation_kind == "approve_pursuit" and self.decision == "revoke":
            _ = _qualified(
                self.approval_entry_ref, "approval_entry_ref",
                "goal-phase-operation-journal-entry",
            )
            if any(
                value is not None
                for value in (
                    self.agent_run_request_ref, self.assignment_ref, self.execution_ref
                )
            ):
                raise GoalPhaseNativeDocumentError("revocation has execution fields")
        elif self.operation_kind == "admit_pursuit" and self.decision == "admit":
            _ = _qualified(
                self.approval_entry_ref, "approval_entry_ref",
                "goal-phase-operation-journal-entry",
            )
            for name, value in (
                ("agent_run_request_ref", self.agent_run_request_ref),
                ("assignment_ref", self.assignment_ref),
                ("execution_ref", self.execution_ref),
            ):
                _ = _typed_ref(value, name)
        else:
            raise GoalPhaseNativeDocumentError("invalid journal operation/decision")
        object.__setattr__(
            self,
            "entry_ref",
            "goal-phase-operation-journal-entry:"
            + _digest(_canonical(_journal_entry_body(self))),
        )


@dataclass(frozen=True, slots=True)
class GoalPhaseOperationJournalV1:
    """Append-ordered local state, with no claim of external action authority."""

    entries: tuple[GoalPhaseOperationJournalEntryV1, ...]
    journal_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_OPERATION_JOURNAL_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseOperationJournalV1:
            raise GoalPhaseNativeDocumentError("journal type must be exact")
        if self.schema_id != GOAL_PHASE_OPERATION_JOURNAL_SCHEMA:
            raise GoalPhaseNativeDocumentError("unsupported journal schema")
        if type(self.entries) is not tuple or not self.entries:
            raise GoalPhaseNativeDocumentError("V3 journal requires entries")
        live: dict[GoalPhaseCoordinate, str] = {}
        running: set[GoalPhaseCoordinate] = set()
        action_refs: set[str] = set()
        idempotency_keys: set[str] = set()
        for entry in self.entries:
            if type(entry) is not GoalPhaseOperationJournalEntryV1:
                raise TypeError("journal entries must be exact")
            entry.__post_init__()
            if (
                entry.action_occurrence_ref in action_refs
                or entry.idempotency_key in idempotency_keys
            ):
                raise GoalPhaseNativeDocumentError("duplicate journal action or idempotency")
            action_refs.add(entry.action_occurrence_ref)
            idempotency_keys.add(entry.idempotency_key)
            coordinate = entry.coordinate
            if coordinate in running:
                raise GoalPhaseNativeDocumentError("operation after admitted pursuit")
            if entry.decision == "approve":
                if coordinate in live:
                    raise GoalPhaseNativeDocumentError("conflicting live approval")
                live[coordinate] = entry.entry_ref
            else:
                if live.get(coordinate) != entry.approval_entry_ref:
                    raise GoalPhaseNativeDocumentError("operation lacks exact live approval")
                if entry.decision == "revoke":
                    del live[coordinate]
                else:
                    running.add(coordinate)
        object.__setattr__(
            self,
            "journal_ref",
            "goal-phase-operation-journal:"
            + _digest(_canonical(_journal_body(self))),
        )


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDocumentV3:
    """Strict V2 graph plus one append-only operation journal."""

    goal_tag: str
    compatibility_projection_sha256: str
    compatibility_projection_byte_count: int
    definitions: tuple[GoalLanePhaseDefinitionV1, ...]
    operational_bundle: GoalPhaseContractBundleV1
    unresolved_dependencies: tuple[GoalPhaseUnresolvedDependencyV1, ...]
    source_refs: tuple[str, ...]
    execution_authority: GoalPhaseExecutionAuthorityV1
    phase_operation_journal: GoalPhaseOperationJournalV1
    document_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_NATIVE_DOCUMENT_V3_SCHEMA
    authority_profile: str = GOAL_PHASE_NATIVE_AUTHORITY_PROFILE
    compatibility_profile: str = GOAL_PHASE_NATIVE_COMPATIBILITY_PROFILE

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseNativeDocumentV3:
            raise GoalPhaseNativeDocumentError("V3 document type must be exact")
        if self.schema_id != GOAL_PHASE_NATIVE_DOCUMENT_V3_SCHEMA:
            raise GoalPhaseNativeDocumentError("unsupported V3 document schema")
        GoalPhaseNativeDocumentV2(
            goal_tag=self.goal_tag,
            compatibility_projection_sha256=self.compatibility_projection_sha256,
            compatibility_projection_byte_count=self.compatibility_projection_byte_count,
            definitions=self.definitions,
            operational_bundle=self.operational_bundle,
            unresolved_dependencies=self.unresolved_dependencies,
            source_refs=self.source_refs,
            execution_authority=self.execution_authority,
        )
        if type(self.phase_operation_journal) is not GoalPhaseOperationJournalV1:
            raise TypeError("phase_operation_journal must be exact")
        self.phase_operation_journal.__post_init__()
        coordinates = {definition.coordinate for definition in self.definitions}
        operational_coordinates = {
            phase.coordinate for phase in self.operational_bundle.phases
        }
        if any(
            entry.coordinate.goal_tag != self.goal_tag
            or entry.coordinate not in coordinates
            for entry in self.phase_operation_journal.entries
        ):
            raise GoalPhaseNativeDocumentError("journal coordinate is not defined")
        if any(
            entry.coordinate not in operational_coordinates
            for entry in self.phase_operation_journal.entries
        ):
            raise GoalPhaseNativeDocumentError("journal coordinate is not operational")
        object.__setattr__(
            self,
            "document_ref",
            "goal-phase-document:" + _digest(_canonical(_document_body_v3(self))),
        )


def encode_goal_phase_native_document(
    value: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
) -> bytes:
    if type(value) not in {
        GoalPhaseNativeDocumentV1, GoalPhaseNativeDocumentV2,
        GoalPhaseNativeDocumentV3,
    }:
        raise TypeError("value must be an exact native Goal document")
    value.__post_init__()
    if type(value) is GoalPhaseNativeDocumentV3:
        return _canonical(_document_wire_v3(value))
    if type(value) is GoalPhaseNativeDocumentV2:
        return _canonical(_document_wire_v2(value))
    return _canonical(_document_wire(cast(GoalPhaseNativeDocumentV1, value)))


def attach_goal_phase_native_carrier(
    compatibility: bytes,
    document: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
) -> bytes:
    """Frame exact native document bytes; compatibility semantics are external."""

    if type(compatibility) is not bytes:
        raise TypeError("compatibility must be exact bytes")
    if GOAL_PHASE_NATIVE_START_MARKER in compatibility or GOAL_PHASE_NATIVE_END_MARKER in compatibility:
        raise GoalPhaseNativeCarrierError("compatibility contains native authority markers")
    if (
        document.compatibility_projection_byte_count != len(compatibility)
        or document.compatibility_projection_sha256
        != "sha256:" + hashlib.sha256(compatibility).hexdigest()
    ):
        raise GoalPhaseNativeCarrierError("document does not bind compatibility bytes")
    separator = b"" if compatibility.endswith(b"\n") else b"\n"
    return (
        compatibility + separator + _CARRIER_OPEN
        + encode_goal_phase_native_document(document) + _CARRIER_CLOSE
    )


def extract_goal_phase_native_carrier(
    candidate: bytes,
) -> tuple[bytes, GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3]:
    """Decode one exact terminal carrier without interpreting Goal Markdown."""

    if type(candidate) is not bytes:
        raise TypeError("candidate must be exact bytes")
    start = candidate.rfind(_CARRIER_OPEN)
    if start < 0 or not candidate.endswith(_CARRIER_CLOSE):
        raise GoalPhaseNativeCarrierError("authority block must be canonical and terminal")
    end = len(candidate) - len(_CARRIER_CLOSE)
    if end < start + len(_CARRIER_OPEN):
        raise GoalPhaseNativeCarrierError("authority block framing is invalid")
    document = decode_goal_phase_native_document(candidate[start + len(_CARRIER_OPEN):end])
    prefix = candidate[:start]
    byte_count = document.compatibility_projection_byte_count
    if byte_count > len(prefix):
        raise GoalPhaseNativeCarrierError("compatibility byte count exceeds prefix")
    compatibility = prefix[:byte_count]
    separator = prefix[byte_count:]
    if separator != (b"" if compatibility.endswith(b"\n") else b"\n"):
        raise GoalPhaseNativeCarrierError("authority block separator is not canonical")
    if attach_goal_phase_native_carrier(compatibility, document) != candidate:
        raise GoalPhaseNativeCarrierError("candidate is not byte-canonical")
    return compatibility, document


def decode_goal_phase_native_document(
    payload: bytes,
) -> GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3:
    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    try:
        raw = cast(
            object,
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseNativeDocumentError("native document is not JSON") from error
    values = _mapping(raw, "document")
    if values.get("schema_id") == GOAL_PHASE_NATIVE_DOCUMENT_V3_SCHEMA:
        return _decode_document_v3(values)
    if values.get("schema_id") == GOAL_PHASE_NATIVE_DOCUMENT_V2_SCHEMA:
        return _decode_document_v2(values)
    _keys(
        values,
        {
            "schema_id",
            "authority_profile",
            "compatibility_profile",
            "goal_tag",
            "compatibility_projection_sha256",
            "compatibility_projection_byte_count",
            "definitions",
            "operational_bundle",
            "unresolved_dependencies",
            "source_refs",
            "document_ref",
        },
        "document",
    )
    definitions = tuple(
        _decode_definition(item) for item in _list(values["definitions"], "definitions")
    )
    operational_bundle = decode_goal_phase_bundle(
        _canonical(values["operational_bundle"])
    )
    unresolved = tuple(
        _decode_unresolved(item)
        for item in _list(
            values["unresolved_dependencies"], "unresolved_dependencies"
        )
    )
    document = GoalPhaseNativeDocumentV1(
        schema_id=_text(values["schema_id"], "schema_id"),
        authority_profile=_text(values["authority_profile"], "authority_profile"),
        compatibility_profile=_text(
            values["compatibility_profile"], "compatibility_profile"
        ),
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        compatibility_projection_sha256=_text(
            values["compatibility_projection_sha256"],
            "compatibility_projection_sha256",
        ),
        compatibility_projection_byte_count=_integer(
            values["compatibility_projection_byte_count"],
            "compatibility_projection_byte_count",
        ),
        definitions=definitions,
        operational_bundle=operational_bundle,
        unresolved_dependencies=unresolved,
        source_refs=_tokens_from_json(values["source_refs"], "source_refs"),
    )
    if _text(values["document_ref"], "document_ref") != document.document_ref:
        raise GoalPhaseNativeDocumentError("document_ref mismatch")
    if not _exact_json_equal(_document_wire(document), values):
        raise GoalPhaseNativeDocumentError("native document is not canonical")
    return document


def _decode_document_v2(values: Mapping[str, object]) -> GoalPhaseNativeDocumentV2:
    _keys(
        values,
        {
            "schema_id", "authority_profile", "compatibility_profile", "goal_tag",
            "compatibility_projection_sha256", "compatibility_projection_byte_count",
            "definitions", "operational_bundle", "unresolved_dependencies",
            "source_refs", "execution_authority", "document_ref",
        },
        "document",
    )
    document = GoalPhaseNativeDocumentV2(
        schema_id=_text(values["schema_id"], "schema_id"),
        authority_profile=_text(values["authority_profile"], "authority_profile"),
        compatibility_profile=_text(values["compatibility_profile"], "compatibility_profile"),
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        compatibility_projection_sha256=_text(values["compatibility_projection_sha256"], "compatibility_projection_sha256"),
        compatibility_projection_byte_count=_integer(values["compatibility_projection_byte_count"], "compatibility_projection_byte_count"),
        definitions=tuple(_decode_definition(item) for item in _list(values["definitions"], "definitions")),
        operational_bundle=decode_goal_phase_bundle(_canonical(values["operational_bundle"])),
        unresolved_dependencies=tuple(_decode_unresolved(item) for item in _list(values["unresolved_dependencies"], "unresolved_dependencies")),
        source_refs=_tokens_from_json(values["source_refs"], "source_refs"),
        execution_authority=_decode_execution_authority(values["execution_authority"]),
    )
    if _text(values["document_ref"], "document_ref") != document.document_ref:
        raise GoalPhaseNativeDocumentError("document_ref mismatch")
    if not _exact_json_equal(_document_wire_v2(document), values):
        raise GoalPhaseNativeDocumentError("native document is not canonical")
    return document


def _decode_document_v3(values: Mapping[str, object]) -> GoalPhaseNativeDocumentV3:
    _keys(
        values,
        {
            "schema_id", "authority_profile", "compatibility_profile", "goal_tag",
            "compatibility_projection_sha256", "compatibility_projection_byte_count",
            "definitions", "operational_bundle", "unresolved_dependencies",
            "source_refs", "execution_authority", "phase_operation_journal",
            "document_ref",
        },
        "document",
    )
    document = GoalPhaseNativeDocumentV3(
        schema_id=_text(values["schema_id"], "schema_id"),
        authority_profile=_text(values["authority_profile"], "authority_profile"),
        compatibility_profile=_text(values["compatibility_profile"], "compatibility_profile"),
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        compatibility_projection_sha256=_text(values["compatibility_projection_sha256"], "compatibility_projection_sha256"),
        compatibility_projection_byte_count=_integer(values["compatibility_projection_byte_count"], "compatibility_projection_byte_count"),
        definitions=tuple(_decode_definition(item) for item in _list(values["definitions"], "definitions")),
        operational_bundle=decode_goal_phase_bundle(_canonical(values["operational_bundle"])),
        unresolved_dependencies=tuple(
            _decode_unresolved(item)
            for item in _list(values["unresolved_dependencies"], "unresolved_dependencies")
        ),
        source_refs=_tokens_from_json(values["source_refs"], "source_refs"),
        execution_authority=_decode_execution_authority(values["execution_authority"]),
        phase_operation_journal=_decode_journal(values["phase_operation_journal"]),
    )
    if _text(values["document_ref"], "document_ref") != document.document_ref:
        raise GoalPhaseNativeDocumentError("document_ref mismatch")
    if not _exact_json_equal(_document_wire_v3(document), values):
        raise GoalPhaseNativeDocumentError("native document is not canonical")
    return document


def _definition_body(value: GoalLanePhaseDefinitionV1) -> dict[str, object]:
    return {
        "coordinate": _coordinate_wire(value.coordinate),
        "ordinal": value.ordinal,
        "title": value.title,
        "intent": value.intent,
        "gate": _gate_wire(value.gate),
    }


def _document_body(value: GoalPhaseNativeDocumentV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "authority_profile": value.authority_profile,
        "compatibility_profile": value.compatibility_profile,
        "goal_tag": value.goal_tag,
        "compatibility_projection_sha256": value.compatibility_projection_sha256,
        "compatibility_projection_byte_count": value.compatibility_projection_byte_count,
        "definitions": [_definition_wire(item) for item in value.definitions],
        "operational_bundle": goal_phase_bundle_to_wire(value.operational_bundle),
        "unresolved_dependencies": [
            _unresolved_wire(item) for item in value.unresolved_dependencies
        ],
        "source_refs": list(value.source_refs),
    }


def _document_wire(value: GoalPhaseNativeDocumentV1) -> dict[str, object]:
    return {**_document_body(value), "document_ref": value.document_ref}


def _execution_authority_body(value: GoalPhaseExecutionAuthorityV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "source_execution_authority_profile": value.source_execution_authority_profile,
        "target_execution_authority_profile": value.target_execution_authority_profile,
        "legacy_execution_disposition": value.legacy_execution_disposition,
        "parity_ref": value.parity_ref,
        "proposal_aggregate_ref": value.proposal_aggregate_ref,
        "coordinator_acceptance_ref": value.coordinator_acceptance_ref,
    }


def _execution_authority_wire(value: GoalPhaseExecutionAuthorityV1) -> dict[str, object]:
    return {**_execution_authority_body(value), "authority_ref": value.authority_ref}


def _decode_execution_authority(raw: object) -> GoalPhaseExecutionAuthorityV1:
    values = _mapping(raw, "execution_authority")
    _keys(values, {
        "schema_id", "source_execution_authority_profile",
        "target_execution_authority_profile", "legacy_execution_disposition",
        "parity_ref", "proposal_aggregate_ref", "coordinator_acceptance_ref",
        "authority_ref",
    }, "execution_authority")
    authority = GoalPhaseExecutionAuthorityV1(
        schema_id=_text(values["schema_id"], "schema_id"),
        source_execution_authority_profile=_text(values["source_execution_authority_profile"], "source_execution_authority_profile"),
        target_execution_authority_profile=_text(values["target_execution_authority_profile"], "target_execution_authority_profile"),
        legacy_execution_disposition=_text(values["legacy_execution_disposition"], "legacy_execution_disposition"),
        parity_ref=_text(values["parity_ref"], "parity_ref"),
        proposal_aggregate_ref=_text(values["proposal_aggregate_ref"], "proposal_aggregate_ref"),
        coordinator_acceptance_ref=_text(values["coordinator_acceptance_ref"], "coordinator_acceptance_ref"),
    )
    if _text(values["authority_ref"], "authority_ref") != authority.authority_ref:
        raise GoalPhaseNativeDocumentError("execution authority_ref mismatch")
    return authority


def _document_body_v2(value: GoalPhaseNativeDocumentV2) -> dict[str, object]:
    body = _document_body(GoalPhaseNativeDocumentV1(
        goal_tag=value.goal_tag,
        compatibility_projection_sha256=value.compatibility_projection_sha256,
        compatibility_projection_byte_count=value.compatibility_projection_byte_count,
        definitions=value.definitions,
        operational_bundle=value.operational_bundle,
        unresolved_dependencies=value.unresolved_dependencies,
        source_refs=value.source_refs,
    ))
    body["schema_id"] = value.schema_id
    body["execution_authority"] = _execution_authority_wire(value.execution_authority)
    return body


def _document_wire_v2(value: GoalPhaseNativeDocumentV2) -> dict[str, object]:
    return {**_document_body_v2(value), "document_ref": value.document_ref}


def _journal_entry_body(value: GoalPhaseOperationJournalEntryV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "operation_kind": value.operation_kind,
        "decision": value.decision,
        "coordinate": _coordinate_wire(value.coordinate),
        "gate_digest": value.gate_digest,
        "source_preimage_ref": value.source_preimage_ref,
        "actor_ref": value.actor_ref,
        "action_occurrence_ref": value.action_occurrence_ref,
        "policy_ref": value.policy_ref,
        "policy_digest": value.policy_digest,
        "idempotency_key": value.idempotency_key,
        "delta_ref": value.delta_ref,
        "event_ref": value.event_ref,
        "approval_entry_ref": value.approval_entry_ref,
        "agent_run_request_ref": value.agent_run_request_ref,
        "assignment_ref": value.assignment_ref,
        "execution_ref": value.execution_ref,
    }


def _journal_entry_wire(value: GoalPhaseOperationJournalEntryV1) -> dict[str, object]:
    return {**_journal_entry_body(value), "entry_ref": value.entry_ref}


def _journal_body(value: GoalPhaseOperationJournalV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "entries": [_journal_entry_wire(item) for item in value.entries],
    }


def _journal_wire(value: GoalPhaseOperationJournalV1) -> dict[str, object]:
    return {**_journal_body(value), "journal_ref": value.journal_ref}


def _document_body_v3(value: GoalPhaseNativeDocumentV3) -> dict[str, object]:
    body = _document_body_v2(GoalPhaseNativeDocumentV2(
        goal_tag=value.goal_tag,
        compatibility_projection_sha256=value.compatibility_projection_sha256,
        compatibility_projection_byte_count=value.compatibility_projection_byte_count,
        definitions=value.definitions,
        operational_bundle=value.operational_bundle,
        unresolved_dependencies=value.unresolved_dependencies,
        source_refs=value.source_refs,
        execution_authority=value.execution_authority,
    ))
    body["schema_id"] = value.schema_id
    body["phase_operation_journal"] = _journal_wire(value.phase_operation_journal)
    return body


def _document_wire_v3(value: GoalPhaseNativeDocumentV3) -> dict[str, object]:
    return {**_document_body_v3(value), "document_ref": value.document_ref}


def _decode_journal_entry(raw: object) -> GoalPhaseOperationJournalEntryV1:
    values = _mapping(raw, "journal entry")
    _keys(values, set(_journal_entry_body_keys()), "journal entry")
    entry = GoalPhaseOperationJournalEntryV1(
        schema_id=_text(values["schema_id"], "schema_id"),
        operation_kind=_text(values["operation_kind"], "operation_kind"),
        decision=_text(values["decision"], "decision"),
        coordinate=_coordinate(values["coordinate"]),
        gate_digest=_text(values["gate_digest"], "gate_digest"),
        source_preimage_ref=_text(values["source_preimage_ref"], "source_preimage_ref"),
        actor_ref=_text(values["actor_ref"], "actor_ref"),
        action_occurrence_ref=_text(values["action_occurrence_ref"], "action_occurrence_ref"),
        policy_ref=_text(values["policy_ref"], "policy_ref"),
        policy_digest=_text(values["policy_digest"], "policy_digest"),
        idempotency_key=_text(values["idempotency_key"], "idempotency_key"),
        delta_ref=_text(values["delta_ref"], "delta_ref"),
        event_ref=_text(values["event_ref"], "event_ref"),
        approval_entry_ref=_optional_text(values["approval_entry_ref"], "approval_entry_ref"),
        agent_run_request_ref=_optional_text(values["agent_run_request_ref"], "agent_run_request_ref"),
        assignment_ref=_optional_text(values["assignment_ref"], "assignment_ref"),
        execution_ref=_optional_text(values["execution_ref"], "execution_ref"),
    )
    if _text(values["entry_ref"], "entry_ref") != entry.entry_ref:
        raise GoalPhaseNativeDocumentError("entry_ref mismatch")
    if not _exact_json_equal(_journal_entry_wire(entry), values):
        raise GoalPhaseNativeDocumentError("journal entry is not canonical")
    return entry


def _journal_entry_body_keys() -> tuple[str, ...]:
    return (
        "schema_id", "operation_kind", "decision", "coordinate", "gate_digest",
        "source_preimage_ref", "actor_ref", "action_occurrence_ref", "policy_ref",
        "policy_digest", "idempotency_key", "delta_ref", "event_ref",
        "approval_entry_ref", "agent_run_request_ref", "assignment_ref", "execution_ref",
        "entry_ref",
    )


def _decode_journal(raw: object) -> GoalPhaseOperationJournalV1:
    values = _mapping(raw, "phase_operation_journal")
    _keys(values, {"schema_id", "entries", "journal_ref"}, "phase_operation_journal")
    journal = GoalPhaseOperationJournalV1(
        schema_id=_text(values["schema_id"], "schema_id"),
        entries=tuple(
            _decode_journal_entry(item) for item in _list(values["entries"], "entries")
        ),
    )
    if _text(values["journal_ref"], "journal_ref") != journal.journal_ref:
        raise GoalPhaseNativeDocumentError("journal_ref mismatch")
    if not _exact_json_equal(_journal_wire(journal), values):
        raise GoalPhaseNativeDocumentError("phase_operation_journal is not canonical")
    return journal


def _definition_wire(value: GoalLanePhaseDefinitionV1) -> dict[str, object]:
    return {**_definition_body(value), "definition_ref": value.definition_ref}


def _unresolved_wire(value: GoalPhaseUnresolvedDependencyV1) -> dict[str, object]:
    return {
        "owner_goal_tag": value.owner_goal_tag,
        "dependency_key": value.dependency_key,
        "dependent": _coordinate_wire(value.dependent),
        "prerequisite": _coordinate_wire(value.prerequisite),
        "relation": value.relation.value,
        "reason": value.reason,
        "evidence_refs": list(value.evidence_refs),
        "resolution_state": value.resolution_state,
        "eligibility_effect": value.eligibility_effect,
    }


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, object]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def _gate_wire(value: GoalLanePhaseGate) -> dict[str, object]:
    return {**value.semantic_body(), "gate_digest": value.gate_digest}


def _decode_definition(raw: object) -> GoalLanePhaseDefinitionV1:
    values = _mapping(raw, "definition")
    _keys(
        values,
        {"coordinate", "ordinal", "title", "intent", "gate", "definition_ref"},
        "definition",
    )
    definition = GoalLanePhaseDefinitionV1(
        coordinate=_coordinate(values["coordinate"]),
        ordinal=_integer(values["ordinal"], "ordinal"),
        title=_optional_text(values["title"], "title"),
        intent=_optional_text(values["intent"], "intent"),
        gate=_gate(values["gate"]),
    )
    if _text(values["definition_ref"], "definition_ref") != definition.definition_ref:
        raise GoalPhaseNativeDocumentError("definition_ref mismatch")
    return definition


def _decode_unresolved(raw: object) -> GoalPhaseUnresolvedDependencyV1:
    values = _mapping(raw, "unresolved_dependency")
    _keys(
        values,
        {
            "owner_goal_tag",
            "dependency_key",
            "dependent",
            "prerequisite",
            "relation",
            "reason",
            "evidence_refs",
            "resolution_state",
            "eligibility_effect",
        },
        "unresolved_dependency",
    )
    return GoalPhaseUnresolvedDependencyV1(
        owner_goal_tag=_text(values["owner_goal_tag"], "owner_goal_tag"),
        dependency_key=_text(values["dependency_key"], "dependency_key"),
        dependent=_coordinate(values["dependent"]),
        prerequisite=_coordinate(values["prerequisite"]),
        relation=GoalDependencyRelation(_text(values["relation"], "relation")),
        reason=_text(values["reason"], "reason"),
        evidence_refs=_tokens_from_json(values["evidence_refs"], "evidence_refs"),
        resolution_state=_text(values["resolution_state"], "resolution_state"),
        eligibility_effect=_text(values["eligibility_effect"], "eligibility_effect"),
    )


def _coordinate(raw: object) -> GoalPhaseCoordinate:
    values = _mapping(raw, "coordinate")
    _keys(values, {"goal_tag", "lane_key", "phase_key"}, "coordinate")
    return GoalPhaseCoordinate(
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        lane_key=_text(values["lane_key"], "lane_key"),
        phase_key=_text(values["phase_key"], "phase_key"),
    )


def _gate(raw: object) -> GoalLanePhaseGate:
    values = _mapping(raw, "gate")
    _keys(
        values,
        {
            "gate_key",
            "promise",
            "gate_contract_ref",
            "evidence_schema_ref",
            "invariant_refs",
            "semantic_revision",
            "gate_digest",
        },
        "gate",
    )
    gate = GoalLanePhaseGate(
        gate_key=_text(values["gate_key"], "gate_key"),
        promise=_text(values["promise"], "promise"),
        gate_contract_ref=_text(values["gate_contract_ref"], "gate_contract_ref"),
        evidence_schema_ref=_text(
            values["evidence_schema_ref"], "evidence_schema_ref"
        ),
        invariant_refs=_tokens_from_json(values["invariant_refs"], "invariant_refs"),
        semantic_revision=_integer(values["semantic_revision"], "semantic_revision"),
    )
    if _text(values["gate_digest"], "gate_digest") != gate.gate_digest:
        raise GoalPhaseNativeDocumentError("Gate digest mismatch")
    return gate


def _unique(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise GoalPhaseNativeDocumentError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise GoalPhaseNativeDocumentError(f"{name} must be an object")
    result = cast(dict[object, object], value)
    if any(type(key) is not str for key in result):
        raise GoalPhaseNativeDocumentError(f"{name} keys must be text")
    return cast(dict[str, object], result)


def _keys(value: Mapping[str, object], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise GoalPhaseNativeDocumentError(f"{name} fields are not canonical")


def _list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        raise GoalPhaseNativeDocumentError(f"{name} must be an array")
    return cast(list[object], value)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise GoalPhaseNativeDocumentError(f"{name} must be canonical text")
    return value


def _optional_text(value: object | None, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _member_key(value: object, name: str) -> str:
    result = _text(value, name)
    if not _MEMBER_KEY.fullmatch(result):
        raise GoalPhaseNativeDocumentError(f"{name} must be kebab-case")
    return result


def _sha(value: object, name: str) -> str:
    result = _text(value, name)
    if not _SHA256.fullmatch(result):
        raise GoalPhaseNativeDocumentError(f"{name} must be qualified SHA-256")
    return result


def _qualified(value: object, name: str, prefix: str) -> str:
    result = _text(value, name)
    if not re.fullmatch(re.escape(prefix) + r":sha256:[0-9a-f]{64}", result):
        raise GoalPhaseNativeDocumentError(f"{name} has invalid qualified digest")
    return result


def _typed_ref(value: object, name: str) -> str:
    result = _text(value, name)
    if not _TYPED_REF.fullmatch(result):
        raise GoalPhaseNativeDocumentError(f"{name} must be a typed digest ref")
    return result


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise GoalPhaseNativeDocumentError(f"{name} must be integer")
    return value


def _tokens(value: object, name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{name} must be exact tuple")
    result = tuple(_text(item, name) for item in cast(tuple[object, ...], value))
    if result != tuple(sorted(set(result))):
        raise GoalPhaseNativeDocumentError(f"{name} must be sorted and unique")
    return result


def _tokens_from_json(value: object, name: str) -> tuple[str, ...]:
    result = tuple(_text(item, name) for item in _list(value, name))
    return _tokens(result, name)


def _exact_json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_map = cast(dict[object, object], left)
        right_map = cast(dict[object, object], right)
        return left_map.keys() == right_map.keys() and all(
            _exact_json_equal(left_map[key], right_map[key]) for key in left_map
        )
    if type(left) is list:
        left_list = cast(list[object], left)
        right_list = cast(list[object], right)
        return len(left_list) == len(right_list) and all(
            _exact_json_equal(left_item, right_item)
            for left_item, right_item in zip(left_list, right_list, strict=True)
        )
    return left == right


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


__all__ = [
    "GOAL_PHASE_NATIVE_AUTHORITY_PROFILE",
    "GOAL_PHASE_NATIVE_COMPATIBILITY_PROFILE",
    "GOAL_PHASE_NATIVE_DOCUMENT_SCHEMA",
    "GOAL_PHASE_NATIVE_DOCUMENT_V2_SCHEMA",
    "GOAL_PHASE_NATIVE_DOCUMENT_V3_SCHEMA",
    "GOAL_PHASE_EXECUTION_AUTHORITY_SCHEMA",
    "GOAL_PHASE_OPERATION_JOURNAL_SCHEMA",
    "GOAL_PHASE_OPERATION_JOURNAL_ENTRY_SCHEMA",
    "GoalPhaseExecutionAuthorityV1",
    "GoalLanePhaseDefinitionV1",
    "GoalPhaseNativeDocumentError",
    "GoalPhaseNativeDocumentV1",
    "GoalPhaseNativeDocumentV2",
    "GoalPhaseNativeDocumentV3",
    "GoalPhaseOperationJournalEntryV1",
    "GoalPhaseOperationJournalV1",
    "GoalPhaseUnresolvedDependencyV1",
    "decode_goal_phase_native_document",
    "encode_goal_phase_native_document",
]
