"""Scope-aware currentness for aggregate Phase-native Goal documents.

This module is runtime-neutral.  It consumes already qualified Goal-global,
lane, source, and dependency authority.  Markdown and Git qualification belong
to source adapters.
"""
# pyright: reportUnusedCallResult=false, reportAny=false

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast

from .identity import fingerprint, normalize_goal_tag, required_text, required_token
from .phase_codec import goal_phase_bundle_to_wire
from .phase_contracts import (
    GoalLanePhaseWorkDisposition,
    GoalPhaseCoordinate,
)
from .phase_document import (
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    encode_goal_phase_native_document,
)
from .phase_frontier import (
    GoalPhaseDependencyObservationV2,
    decode_goal_phase_dependency_observation,
    goal_phase_dependency_digest,
)
from .phase_pursuit import GoalPhaseRevisionLineageV1, GoalPhaseSourceBindingV1
from .phase_publication import (
    GoalPhaseMutationKind,
    GoalPhaseProjectionReconciliationReceiptV1,
    GoalPhasePublicationReceiptV1,
    reconcile_goal_phase_projection,
    verify_goal_phase_publication_transition,
)

GOAL_GLOBAL_DIRECTION_AUTHORITY_SCHEMA = "aware.goal.global-direction-authority.v1"
GOAL_LANE_DIRECTION_AUTHORITY_SCHEMA = "aware.goal.lane-direction-authority.v1"
GOAL_PHASE_NATIVE_SCOPE_SCHEMA = "aware.goal.phase-native-scope.v1"
GOAL_PHASE_NATIVE_SCOPE_PROJECTION_SCHEMA = (
    "aware.goal.phase-native-scope-projection.v1"
)
GOAL_PHASE_NATIVE_SCOPE_ADVANCEMENT_SCHEMA = (
    "aware.goal.phase-native-scope-advancement.v1"
)
GOAL_PHASE_NATIVE_SCOPE_SOURCE_EPOCH_SCHEMA = (
    "aware.goal.phase-native-scope-source-epoch.v1"
)
GOAL_PHASE_NATIVE_SCOPE_DELTA_ADMISSION_SCHEMA = (
    "aware.goal.phase-native-scope-delta-admission.v1"
)
GOAL_PHASE_PROJECTION_CURRENTNESS_VERIFICATION_SCHEMA = (
    "aware.goal.phase-projection-currentness-verification.v1"
)

_MEMBER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class GoalPhaseNativeScopeError(ValueError):
    """A scope, authority projection, or advancement is not canonical."""


class GoalPhaseNativeScopeProfile(StrEnum):
    PHASE_DIRECTION = "phase_direction_v1"
    LANE_DIRECTION = "lane_direction_v1"
    GOAL_GRAPH = "goal_graph_v1"


class GoalPhaseNativeScopeRelation(StrEnum):
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    AMBIGUOUS = "ambiguous"


class GoalPhaseNativeRetainedCurrentness(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    AMBIGUOUS = "ambiguous"


class GoalPhaseNativeAdvancementDisposition(StrEnum):
    EXACT = "exact"
    REOBSERVED_UNCHANGED = "reobserved_unchanged"
    ADMITTED_DELTA_REQUIRED = "admitted_delta_required"
    REFUSE = "refuse"


class GoalPhaseNativeCompatibilityRelation(StrEnum):
    EXACT = "exact"
    ALLOWLISTED_APPEND = "allowlisted_append"
    DECODED_AUTHORITY_CHANGE = "decoded_authority_change"
    UNKNOWN = "unknown"


class GoalPhaseNativeDependencyCoverageState(StrEnum):
    OBSERVED = "observed"
    NOT_EVALUATED = "not_evaluated"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class GoalGlobalDirectionAuthorityV1:
    goal_tag: str
    lifecycle_status: str
    owner_ref: str
    governance_authority_refs: tuple[str, ...]
    hold_state: str
    hold_authority_refs: tuple[str, ...]
    execution_authority_ref: str
    compatibility_guard_ref: str
    source_revision_ref: str
    projector_ref: str
    projection_receipt_ref: str
    authority_ref: str = field(init=False)
    schema_id: str = GOAL_GLOBAL_DIRECTION_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalGlobalDirectionAuthorityV1:
            raise TypeError("Goal-global authority type must be exact")
        if self.schema_id != GOAL_GLOBAL_DIRECTION_AUTHORITY_SCHEMA:
            raise GoalPhaseNativeScopeError("unsupported Goal-global authority schema")
        object.__setattr__(self, "goal_tag", normalize_goal_tag(self.goal_tag))
        if self.lifecycle_status not in {
            "proposed",
            "active",
            "parked",
            "held",
            "completed",
            "withdrawn",
        }:
            raise GoalPhaseNativeScopeError("unsupported Goal lifecycle status")
        if self.hold_state not in {"clear", "held"}:
            raise GoalPhaseNativeScopeError("unsupported Goal hold state")
        _tokens(self.governance_authority_refs, "governance_authority_refs")
        _tokens(self.hold_authority_refs, "hold_authority_refs")
        if self.hold_state == "held" and not self.hold_authority_refs:
            raise GoalPhaseNativeScopeError("held Goal requires hold authority")
        if self.hold_state == "clear" and self.hold_authority_refs:
            raise GoalPhaseNativeScopeError("clear Goal cannot carry hold authority")
        for name in (
            "owner_ref",
            "execution_authority_ref",
            "compatibility_guard_ref",
            "source_revision_ref",
            "projector_ref",
            "projection_receipt_ref",
        ):
            required_token(cast(str, getattr(self, name)), name)
        object.__setattr__(
            self,
            "authority_ref",
            "goal-global-direction:" + fingerprint(_global_body(self)),
        )

    def to_wire(self) -> dict[str, object]:
        return {**_global_body(self), "authority_ref": self.authority_ref}

    def semantic_wire(self) -> dict[str, object]:
        return {
            "goal_tag": self.goal_tag,
            "lifecycle_status": self.lifecycle_status,
            "owner_ref": self.owner_ref,
            "governance_authority_refs": list(self.governance_authority_refs),
            "hold_state": self.hold_state,
            "hold_authority_refs": list(self.hold_authority_refs),
            "execution_authority_ref": self.execution_authority_ref,
            "compatibility_guard_ref": self.compatibility_guard_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalLaneDirectionAuthorityV1:
    goal_tag: str
    lane_key: str
    role: str
    owner_ref: str
    operational_state: str
    state_detail: str | None
    blocker_authority_refs: tuple[str, ...]
    current_issue_ref: str | None
    current_issue_authority_ref: str | None
    compatibility_guard_ref: str
    source_revision_ref: str
    projector_ref: str
    projection_receipt_ref: str
    qualification: str = "qualified"
    ambiguity_reasons: tuple[str, ...] = ()
    authority_ref: str = field(init=False)
    schema_id: str = GOAL_LANE_DIRECTION_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalLaneDirectionAuthorityV1:
            raise TypeError("lane authority type must be exact")
        if self.schema_id != GOAL_LANE_DIRECTION_AUTHORITY_SCHEMA:
            raise GoalPhaseNativeScopeError("unsupported lane authority schema")
        object.__setattr__(self, "goal_tag", normalize_goal_tag(self.goal_tag))
        if not _MEMBER.fullmatch(self.lane_key):
            raise GoalPhaseNativeScopeError("lane_key must be kebab-case")
        required_text(self.role, "role")
        required_token(self.owner_ref, "owner_ref")
        if self.operational_state not in {
            "planned",
            "active",
            "held",
            "blocked",
            "ready",
            "complete",
            "withdrawn",
        }:
            raise GoalPhaseNativeScopeError("unsupported lane operational state")
        if self.qualification not in {"qualified", "ambiguous"}:
            raise GoalPhaseNativeScopeError("unsupported lane qualification")
        _tokens(self.ambiguity_reasons, "ambiguity_reasons")
        if (self.qualification == "ambiguous") != bool(self.ambiguity_reasons):
            raise GoalPhaseNativeScopeError(
                "lane ambiguity requires exact typed reasons"
            )
        if self.state_detail is not None:
            required_text(self.state_detail, "state_detail")
        _tokens(self.blocker_authority_refs, "blocker_authority_refs")
        if self.operational_state in {"held", "blocked"}:
            if self.state_detail is None or not self.blocker_authority_refs:
                raise GoalPhaseNativeScopeError(
                    "held/blocked lane requires detail and authority"
                )
        elif self.blocker_authority_refs:
            raise GoalPhaseNativeScopeError(
                "non-held lane cannot carry blocker authority"
            )
        if (self.current_issue_ref is None) != (
            self.current_issue_authority_ref is None
        ):
            raise GoalPhaseNativeScopeError(
                "current Issue and its authority must be paired"
            )
        for name in (
            "current_issue_ref",
            "current_issue_authority_ref",
            "compatibility_guard_ref",
            "source_revision_ref",
            "projector_ref",
            "projection_receipt_ref",
        ):
            value = cast(str | None, getattr(self, name))
            if value is not None:
                required_token(value, name)
        object.__setattr__(
            self,
            "authority_ref",
            "goal-lane-direction:" + fingerprint(_lane_body(self)),
        )

    def to_wire(self) -> dict[str, object]:
        return {**_lane_body(self), "authority_ref": self.authority_ref}

    def semantic_wire(self) -> dict[str, object]:
        return {
            "goal_tag": self.goal_tag,
            "lane_key": self.lane_key,
            "role": self.role,
            "owner_ref": self.owner_ref,
            "operational_state": self.operational_state,
            "state_detail": self.state_detail,
            "blocker_authority_refs": list(self.blocker_authority_refs),
            "current_issue_ref": self.current_issue_ref,
            "current_issue_authority_ref": self.current_issue_authority_ref,
            "compatibility_guard_ref": self.compatibility_guard_ref,
            "qualification": self.qualification,
            "ambiguity_reasons": list(self.ambiguity_reasons),
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeScopeDescriptorV1:
    root: GoalPhaseCoordinate
    profile: GoalPhaseNativeScopeProfile
    consumer_authority_ref: str
    projector_ref: str
    scope_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_NATIVE_SCOPE_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseNativeScopeDescriptorV1:
            raise TypeError("scope descriptor type must be exact")
        if self.schema_id != GOAL_PHASE_NATIVE_SCOPE_SCHEMA:
            raise GoalPhaseNativeScopeError("unsupported scope schema")
        if type(self.root) is not GoalPhaseCoordinate:
            raise TypeError("root must be GoalPhaseCoordinate")
        if type(self.profile) is not GoalPhaseNativeScopeProfile:
            raise TypeError("profile must be GoalPhaseNativeScopeProfile")
        required_token(self.consumer_authority_ref, "consumer_authority_ref")
        required_token(self.projector_ref, "projector_ref")
        object.__setattr__(
            self,
            "scope_ref",
            "goal-phase-native-scope:" + fingerprint(_scope_body(self)),
        )

    def to_wire(self) -> dict[str, object]:
        return {**_scope_body(self), "scope_ref": self.scope_ref}


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeScopeComponentV1:
    kind: str
    coordinate_ref: str
    value_digest: str

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseNativeScopeComponentV1:
            raise TypeError("component type must be exact")
        if not _MEMBER.fullmatch(self.kind):
            raise GoalPhaseNativeScopeError("component kind must be kebab-case")
        required_token(self.coordinate_ref, "coordinate_ref")
        if not _SHA.fullmatch(self.value_digest):
            raise GoalPhaseNativeScopeError("component digest must be SHA-256")

    def to_wire(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "coordinate_ref": self.coordinate_ref,
            "value_digest": self.value_digest,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDependencyCoverageEntryV1:
    owner_goal_tag: str
    dependency_key: str
    dependency_digest: str
    dependent_ref: str
    prerequisite_ref: str
    state: GoalPhaseNativeDependencyCoverageState
    observation_ref: str | None
    currentness_ref: str | None
    cross_goal: bool

    def __post_init__(self) -> None:
        required_token(self.dependency_key, "dependency_key")
        normalize_goal_tag(self.owner_goal_tag)
        for value, name in (
            (self.dependency_digest, "dependency_digest"),
            (self.dependent_ref, "dependent_ref"),
            (self.prerequisite_ref, "prerequisite_ref"),
        ):
            required_token(value, name)
        if type(self.state) is not GoalPhaseNativeDependencyCoverageState:
            raise TypeError("dependency coverage state must be exact")
        if self.state is GoalPhaseNativeDependencyCoverageState.OBSERVED:
            if self.observation_ref is None or self.currentness_ref is None:
                raise GoalPhaseNativeScopeError(
                    "observed dependency requires observation currentness"
                )
        elif self.observation_ref is not None or self.currentness_ref is not None:
            raise GoalPhaseNativeScopeError(
                "non-observed dependency cannot carry observation authority"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "dependency_key": self.dependency_key,
            "owner_goal_tag": self.owner_goal_tag,
            "dependency_digest": self.dependency_digest,
            "dependent_ref": self.dependent_ref,
            "prerequisite_ref": self.prerequisite_ref,
            "state": self.state.value,
            "observation_ref": self.observation_ref,
            "currentness_ref": self.currentness_ref,
            "cross_goal": self.cross_goal,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDependencySnapshotV1:
    descriptor_ref: str
    entries: tuple[GoalPhaseNativeDependencyCoverageEntryV1, ...]
    snapshot_ref: str = field(init=False)

    def __post_init__(self) -> None:
        required_token(self.descriptor_ref, "descriptor_ref")
        keys = tuple(
            (item.owner_goal_tag, item.dependency_key) for item in self.entries
        )
        if keys != tuple(sorted(set(keys))):
            raise GoalPhaseNativeScopeError(
                "dependency snapshot entries must be sorted and unique"
            )
        object.__setattr__(
            self,
            "snapshot_ref",
            "goal-phase-native-dependency-snapshot:"
            + fingerprint(
                {
                    "descriptor_ref": self.descriptor_ref,
                    "entries": [item.to_wire() for item in self.entries],
                }
            ),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "descriptor_ref": self.descriptor_ref,
            "entries": [item.to_wire() for item in self.entries],
            "snapshot_ref": self.snapshot_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeScopeProjectionV1:
    descriptor: GoalPhaseNativeScopeDescriptorV1
    document_ref: str
    source_revision_ref: str
    authority_binding_refs: tuple[str, ...]
    dependency_snapshot_ref: str
    components: tuple[GoalPhaseNativeScopeComponentV1, ...]
    scope_digest: str
    qualification: str
    ambiguity_reasons: tuple[str, ...]
    projection_ref: str
    schema_id: str = GOAL_PHASE_NATIVE_SCOPE_PROJECTION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_NATIVE_SCOPE_PROJECTION_SCHEMA:
            raise GoalPhaseNativeScopeError("unsupported scope projection schema")
        required_token(self.dependency_snapshot_ref, "dependency_snapshot_ref")
        _tokens(self.authority_binding_refs, "authority_binding_refs")
        if self.components != tuple(
            sorted(self.components, key=lambda item: (item.kind, item.coordinate_ref))
        ):
            raise GoalPhaseNativeScopeError("scope components are not canonical")
        if self.scope_digest != _digest([item.to_wire() for item in self.components]):
            raise GoalPhaseNativeScopeError("scope digest is not canonical")
        if self.qualification not in {"qualified", "ambiguous"}:
            raise GoalPhaseNativeScopeError("scope qualification is unsupported")
        _tokens(self.ambiguity_reasons, "ambiguity_reasons")
        if (self.qualification == "ambiguous") != bool(self.ambiguity_reasons):
            raise GoalPhaseNativeScopeError("scope ambiguity is not canonical")
        body = self.to_wire()
        supplied = body.pop("projection_ref")
        if supplied != "goal-phase-native-scope-projection:" + fingerprint(body):
            raise GoalPhaseNativeScopeError(
                "scope projection reference is not canonical"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "read_only_non_authorizing",
            "descriptor": self.descriptor.to_wire(),
            "document_ref": self.document_ref,
            "source_revision_ref": self.source_revision_ref,
            "authority_binding_refs": list(self.authority_binding_refs),
            "dependency_snapshot_ref": self.dependency_snapshot_ref,
            "components": [item.to_wire() for item in self.components],
            "scope_digest": self.scope_digest,
            "qualification": self.qualification,
            "ambiguity_reasons": list(self.ambiguity_reasons),
            "projection_ref": self.projection_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeScopeChangeV1:
    kind: str
    coordinate_ref: str
    before_digest: str | None
    after_digest: str | None

    def to_wire(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "coordinate_ref": self.coordinate_ref,
            "before_digest": self.before_digest,
            "after_digest": self.after_digest,
        }


@dataclass(frozen=True, slots=True, init=False)
class GoalPhaseNativeScopeSourceEpochV1:
    goal_path: str
    previous_source: GoalPhaseSourceBindingV1
    candidate_source: GoalPhaseSourceBindingV1
    observed_head_ref: str
    lineage: GoalPhaseRevisionLineageV1
    previous_source_verification_ref: str
    candidate_source_verification_ref: str
    currentness_ref: str
    compatibility_relation: GoalPhaseNativeCompatibilityRelation
    verifier_token: object = field(compare=False)
    schema_id: str = GOAL_PHASE_NATIVE_SCOPE_SOURCE_EPOCH_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseNativeScopeSourceEpochV1:
            raise TypeError("source epoch type must be exact")
        if self.schema_id != GOAL_PHASE_NATIVE_SCOPE_SOURCE_EPOCH_SCHEMA:
            raise GoalPhaseNativeScopeError("unsupported source epoch schema")
        required_token(self.goal_path, "goal_path")
        if (
            self.lineage.expected_revision_ref
            != self.previous_source.repository_revision_ref
            or self.lineage.observed_revision_ref
            != self.candidate_source.repository_revision_ref
        ):
            raise GoalPhaseNativeScopeError("lineage does not bind scope sources")
        for name in (
            "observed_head_ref",
            "previous_source_verification_ref",
            "candidate_source_verification_ref",
            "currentness_ref",
        ):
            required_token(cast(str, getattr(self, name)), name)
        if self.candidate_source.repository_revision_ref != self.observed_head_ref:
            raise GoalPhaseNativeScopeError(
                "candidate source must be verified at observed HEAD"
            )
        if (
            type(self.compatibility_relation)
            is not GoalPhaseNativeCompatibilityRelation
        ):
            raise TypeError("compatibility relation must be exact")
        previous_verification = "goal-scope-source-verification:" + fingerprint(
            {"goal_path": self.goal_path, "source": self.previous_source.to_wire()}
        )
        candidate_verification = "goal-scope-source-verification:" + fingerprint(
            {
                "goal_path": self.goal_path,
                "source": self.candidate_source.to_wire(),
                "observed_head_ref": self.observed_head_ref,
            }
        )
        currentness = "goal-scope-source-currentness:" + fingerprint(
            {
                "previous_verification_ref": previous_verification,
                "candidate_verification_ref": candidate_verification,
                "lineage": self.lineage.to_wire(),
                "compatibility_relation": self.compatibility_relation.value,
            }
        )
        if (
            self.previous_source_verification_ref != previous_verification
            or self.candidate_source_verification_ref != candidate_verification
            or self.currentness_ref != currentness
        ):
            raise GoalPhaseNativeScopeError(
                "source epoch verification references are not canonical"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "goal_path": self.goal_path,
            "previous_source": self.previous_source.to_wire(),
            "candidate_source": self.candidate_source.to_wire(),
            "observed_head_ref": self.observed_head_ref,
            "lineage": self.lineage.to_wire(),
            "previous_source_verification_ref": self.previous_source_verification_ref,
            "candidate_source_verification_ref": self.candidate_source_verification_ref,
            "currentness_ref": self.currentness_ref,
            "compatibility_relation": self.compatibility_relation.value,
        }


@dataclass(frozen=True, slots=True)
class _SourceEpochVerificationToken:
    nonce: object = field(default_factory=object)


_SOURCE_EPOCH_REGISTRY_LIMIT = 256
_SOURCE_EPOCH_REGISTRY: OrderedDict[_SourceEpochVerificationToken, str] = (
    OrderedDict()
)


def verify_goal_phase_native_scope_source_epoch(
    *,
    goal_path: str,
    previous_source: GoalPhaseSourceBindingV1,
    candidate_source: GoalPhaseSourceBindingV1,
    repository_resolver: Callable[[str, str, str], Mapping[str, object]],
) -> GoalPhaseNativeScopeSourceEpochV1:
    """Issue a sealed epoch from an independent repository authority resolver."""

    resolved = repository_resolver(
        goal_path,
        previous_source.repository_revision_ref,
        candidate_source.repository_revision_ref,
    )
    required = {
        "observed_head_ref",
        "lineage",
        "previous_source",
        "candidate_source",
        "compatibility_relation",
    }
    if set(resolved) != required:
        raise GoalPhaseNativeScopeError("repository epoch evidence fields differ")
    if resolved["previous_source"] != previous_source.to_wire() or resolved[
        "candidate_source"
    ] != candidate_source.to_wire():
        raise GoalPhaseNativeScopeError(
            "repository resolver source bindings differ"
        )
    observed_head_ref = required_token(
        cast(str, resolved["observed_head_ref"]), "observed_head_ref"
    )
    lineage = GoalPhaseRevisionLineageV1(
        previous_source.repository_revision_ref,
        candidate_source.repository_revision_ref,
        required_token(cast(str, resolved["lineage"]), "lineage"),
    )
    try:
        compatibility_relation = GoalPhaseNativeCompatibilityRelation(
            required_token(
                cast(str, resolved["compatibility_relation"]),
                "compatibility_relation",
            )
        )
    except ValueError as error:
        raise GoalPhaseNativeScopeError(
            "repository compatibility relation is unsupported"
        ) from error
    previous_verification = "goal-scope-source-verification:" + fingerprint(
        {"goal_path": goal_path, "source": previous_source.to_wire()}
    )
    candidate_verification = "goal-scope-source-verification:" + fingerprint(
        {
            "goal_path": goal_path,
            "source": candidate_source.to_wire(),
            "observed_head_ref": observed_head_ref,
        }
    )
    currentness = "goal-scope-source-currentness:" + fingerprint(
        {
            "previous_verification_ref": previous_verification,
            "candidate_verification_ref": candidate_verification,
            "lineage": lineage.to_wire(),
            "compatibility_relation": compatibility_relation.value,
        }
    )
    value = object.__new__(GoalPhaseNativeScopeSourceEpochV1)
    for name, item in (
        ("goal_path", goal_path),
        ("previous_source", previous_source),
        ("candidate_source", candidate_source),
        ("observed_head_ref", observed_head_ref),
        ("lineage", lineage),
        ("previous_source_verification_ref", previous_verification),
        ("candidate_source_verification_ref", candidate_verification),
        ("currentness_ref", currentness),
        ("compatibility_relation", compatibility_relation),
        ("schema_id", GOAL_PHASE_NATIVE_SCOPE_SOURCE_EPOCH_SCHEMA),
    ):
        object.__setattr__(value, name, item)
    value.__post_init__()
    body = value.to_wire()
    token = _SourceEpochVerificationToken()
    _SOURCE_EPOCH_REGISTRY[token] = _digest(body)
    while len(_SOURCE_EPOCH_REGISTRY) > _SOURCE_EPOCH_REGISTRY_LIMIT:
        _SOURCE_EPOCH_REGISTRY.popitem(last=False)
    object.__setattr__(value, "verifier_token", token)
    return value


def _require_verified_source_epoch(value: GoalPhaseNativeScopeSourceEpochV1) -> None:
    if type(value) is not GoalPhaseNativeScopeSourceEpochV1 or not hasattr(
        value, "verifier_token"
    ):
        raise GoalPhaseNativeScopeError(
            "source epoch is not independently verified"
        )
    value.__post_init__()
    token = value.verifier_token
    if type(token) is not _SourceEpochVerificationToken or _SOURCE_EPOCH_REGISTRY.get(
        token
    ) != _digest(value.to_wire()):
        raise GoalPhaseNativeScopeError("source epoch verifier output was mutated")


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeScopeAdvancementV1:
    descriptor: GoalPhaseNativeScopeDescriptorV1
    previous_document_ref: str
    candidate_document_ref: str
    source_epoch: GoalPhaseNativeScopeSourceEpochV1
    previous_scope_digest: str
    candidate_scope_digest: str
    changes: tuple[GoalPhaseNativeScopeChangeV1, ...]
    aggregate_projection: str
    scope_relation: GoalPhaseNativeScopeRelation
    retained_scope_currentness: GoalPhaseNativeRetainedCurrentness
    disposition: GoalPhaseNativeAdvancementDisposition
    advancement_ref: str
    schema_id: str = GOAL_PHASE_NATIVE_SCOPE_ADVANCEMENT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_NATIVE_SCOPE_ADVANCEMENT_SCHEMA:
            raise GoalPhaseNativeScopeError("unsupported advancement schema")
        expected_changes = tuple(
            sorted(self.changes, key=lambda item: (item.kind, item.coordinate_ref))
        )
        if self.changes != expected_changes:
            raise GoalPhaseNativeScopeError("advancement changes are not canonical")
        if (
            self.scope_relation is GoalPhaseNativeScopeRelation.UNCHANGED
            and self.changes
        ):
            raise GoalPhaseNativeScopeError(
                "unchanged advancement cannot carry changes"
            )
        if (
            self.scope_relation is GoalPhaseNativeScopeRelation.CHANGED
            and not self.changes
        ):
            raise GoalPhaseNativeScopeError("changed advancement requires changes")
        body = self.to_wire()
        supplied = body.pop("advancement_ref")
        if supplied != "goal-phase-native-scope-advancement:" + fingerprint(body):
            raise GoalPhaseNativeScopeError("advancement reference is not canonical")

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "read_only_non_authorizing",
            "descriptor": self.descriptor.to_wire(),
            "previous_document_ref": self.previous_document_ref,
            "candidate_document_ref": self.candidate_document_ref,
            "source_epoch": self.source_epoch.to_wire(),
            "previous_scope_digest": self.previous_scope_digest,
            "candidate_scope_digest": self.candidate_scope_digest,
            "changes": [item.to_wire() for item in self.changes],
            "aggregate_projection": self.aggregate_projection,
            "scope_relation": self.scope_relation.value,
            "retained_scope_currentness": self.retained_scope_currentness.value,
            "disposition": self.disposition.value,
            "advancement_ref": self.advancement_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeScopeDeltaAdmissionV1:
    """Typed evidence that one changed scope is covered by a lawful publication."""

    descriptor: GoalPhaseNativeScopeDescriptorV1
    advancement_ref: str
    publication_receipt_ref: str
    reconciliation_receipt_ref: str
    projection_currentness_verification_ref: str
    admitted_change: GoalPhaseNativeScopeChangeV1
    admission_ref: str
    schema_id: str = GOAL_PHASE_NATIVE_SCOPE_DELTA_ADMISSION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseNativeScopeDeltaAdmissionV1:
            raise TypeError("scope delta admission type must be exact")
        if self.schema_id != GOAL_PHASE_NATIVE_SCOPE_DELTA_ADMISSION_SCHEMA:
            raise GoalPhaseNativeScopeError("unsupported scope delta admission schema")
        self.descriptor.__post_init__()
        if type(self.admitted_change) is not GoalPhaseNativeScopeChangeV1:
            raise TypeError("admitted change type must be exact")
        body = self.to_wire()
        supplied = body.pop("admission_ref")
        if supplied != "goal-phase-native-scope-delta-admission:" + fingerprint(body):
            raise GoalPhaseNativeScopeError(
                "scope delta admission ref is not canonical"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "read_only_non_authorizing",
            "descriptor": self.descriptor.to_wire(),
            "advancement_ref": self.advancement_ref,
            "publication_receipt_ref": self.publication_receipt_ref,
            "reconciliation_receipt_ref": self.reconciliation_receipt_ref,
            "projection_currentness_verification_ref": (
                self.projection_currentness_verification_ref
            ),
            "admitted_change": self.admitted_change.to_wire(),
            "admission_ref": self.admission_ref,
        }


@dataclass(frozen=True, slots=True, init=False)
class GoalPhaseProjectionCurrentnessVerificationV1:
    """Ephemeral verifier output proving the M10 projection is current now."""

    goal_path: str
    publication_receipt_ref: str
    publication_commit_ref: str
    observed_head_ref: str
    worktree_sha256: str
    index_blob_oid: str
    verification_ref: str
    verifier_token: object = field(compare=False)
    schema_id: str = GOAL_PHASE_PROJECTION_CURRENTNESS_VERIFICATION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseProjectionCurrentnessVerificationV1:
            raise TypeError("projection currentness verification type must be exact")
        if self.schema_id != GOAL_PHASE_PROJECTION_CURRENTNESS_VERIFICATION_SCHEMA:
            raise GoalPhaseNativeScopeError(
                "unsupported projection currentness verification schema"
            )
        for name in (
            "goal_path",
            "publication_receipt_ref",
            "publication_commit_ref",
            "observed_head_ref",
            "worktree_sha256",
            "index_blob_oid",
        ):
            required_token(cast(str, getattr(self, name)), name)
        if not _SHA.fullmatch(self.worktree_sha256):
            raise GoalPhaseNativeScopeError("worktree digest is not canonical")
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", self.index_blob_oid):
            raise GoalPhaseNativeScopeError("index blob identity is not canonical")
        body = self.to_wire()
        supplied = body.pop("verification_ref")
        expected = "goal-phase-projection-currentness-verification:" + fingerprint(body)
        if supplied != expected:
            raise GoalPhaseNativeScopeError(
                "projection currentness verification ref is not canonical"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "read_only_non_authorizing",
            "goal_path": self.goal_path,
            "publication_receipt_ref": self.publication_receipt_ref,
            "publication_commit_ref": self.publication_commit_ref,
            "observed_head_ref": self.observed_head_ref,
            "worktree_sha256": self.worktree_sha256,
            "index_blob_oid": self.index_blob_oid,
            "verification_ref": self.verification_ref,
        }


@dataclass(frozen=True, slots=True)
class _ProjectionCurrentnessVerificationToken:
    nonce: object = field(default_factory=object)


_PROJECTION_CURRENTNESS_REGISTRY_LIMIT = 256
_PROJECTION_CURRENTNESS_REGISTRY: OrderedDict[
    _ProjectionCurrentnessVerificationToken, str
] = OrderedDict()


def verify_goal_phase_projection_currentness(
    *,
    publication_receipt: GoalPhasePublicationReceiptV1,
    repository_resolver: Callable[[str, str], Mapping[str, object]],
) -> GoalPhaseProjectionCurrentnessVerificationV1:
    """Observe the worktree and index through an independent repository adapter."""

    publication_receipt.__post_init__()
    if len(publication_receipt.changed_paths) != 1:
        raise GoalPhaseNativeScopeError(
            "projection currentness requires one changed Goal path"
        )
    goal_path = publication_receipt.changed_paths[0]
    publication_commit_ref = (
        publication_receipt.after_binding.projection_revision.repository_commit
    )
    resolved = repository_resolver(goal_path, publication_commit_ref)
    required = {
        "goal_path",
        "publication_receipt_ref",
        "publication_commit_ref",
        "observed_head_ref",
        "worktree_sha256",
        "index_blob_oid",
    }
    if set(resolved) != required:
        raise GoalPhaseNativeScopeError(
            "projection currentness evidence fields differ"
        )
    expected: dict[str, object] = {
        "goal_path": goal_path,
        "publication_receipt_ref": publication_receipt.receipt_ref,
        "publication_commit_ref": publication_commit_ref,
        "worktree_sha256": (
            publication_receipt.after_binding.projection_revision.source_sha256
        ),
        "index_blob_oid": (
            publication_receipt.after_binding.projection_revision.phase_blob_oid
        ),
    }
    for name, value in expected.items():
        if resolved[name] != value:
            raise GoalPhaseNativeScopeError(
                f"projection currentness {name} differs from publication"
            )
    observed_head_ref = required_token(
        cast(str, resolved["observed_head_ref"]), "observed_head_ref"
    )
    body = {
        "schema_id": GOAL_PHASE_PROJECTION_CURRENTNESS_VERIFICATION_SCHEMA,
        "effect_profile": "read_only_non_authorizing",
        **expected,
        "observed_head_ref": observed_head_ref,
    }
    value = object.__new__(GoalPhaseProjectionCurrentnessVerificationV1)
    for name, item in (
        *tuple(expected.items()),
        ("observed_head_ref", observed_head_ref),
        (
            "verification_ref",
            "goal-phase-projection-currentness-verification:" + fingerprint(body),
        ),
        ("schema_id", GOAL_PHASE_PROJECTION_CURRENTNESS_VERIFICATION_SCHEMA),
    ):
        object.__setattr__(value, name, item)
    value.__post_init__()
    token = _ProjectionCurrentnessVerificationToken()
    _PROJECTION_CURRENTNESS_REGISTRY[token] = _digest(value.to_wire())
    while len(_PROJECTION_CURRENTNESS_REGISTRY) > _PROJECTION_CURRENTNESS_REGISTRY_LIMIT:
        _PROJECTION_CURRENTNESS_REGISTRY.popitem(last=False)
    object.__setattr__(value, "verifier_token", token)
    return value


def _require_verified_projection_currentness(
    value: GoalPhaseProjectionCurrentnessVerificationV1,
) -> None:
    if type(value) is not GoalPhaseProjectionCurrentnessVerificationV1 or not hasattr(
        value, "verifier_token"
    ):
        raise GoalPhaseNativeScopeError(
            "projection currentness is not independently verified"
        )
    value.__post_init__()
    token = value.verifier_token
    if (
        type(token) is not _ProjectionCurrentnessVerificationToken
        or _PROJECTION_CURRENTNESS_REGISTRY.get(token) != _digest(value.to_wire())
    ):
        raise GoalPhaseNativeScopeError(
            "projection currentness verifier output was mutated"
        )


NativeDocument = GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3


def project_goal_phase_native_scope(
    *,
    document: NativeDocument,
    descriptor: GoalPhaseNativeScopeDescriptorV1,
    goal_authority: GoalGlobalDirectionAuthorityV1,
    lane_authorities: tuple[GoalLaneDirectionAuthorityV1, ...],
    dependency_observations: tuple[GoalPhaseDependencyObservationV2, ...] = (),
) -> GoalPhaseNativeScopeProjectionV1:
    """Derive one complete canonical scope; callers cannot supply members."""

    _validate_inputs(document, descriptor, goal_authority, lane_authorities)
    document_wire = cast(
        dict[str, object], json.loads(encode_goal_phase_native_document(document))
    )
    bundle_wire = goal_phase_bundle_to_wire(document.operational_bundle)
    definitions = {item.coordinate: item for item in document.definitions}
    phases = {item.coordinate: item for item in document.operational_bundle.phases}
    lane_map = {item.lane_key: item for item in lane_authorities}
    dependency_snapshot, observation_map = _dependency_snapshot(
        document=document,
        descriptor=descriptor,
        observations=dependency_observations,
    )
    root_def = definitions.get(descriptor.root)
    if root_def is None:
        raise GoalPhaseNativeScopeError("scope root is not defined")
    components: dict[tuple[str, str], GoalPhaseNativeScopeComponentV1] = {}

    def add(kind: str, coordinate_ref: str, value: object) -> None:
        key = (kind, coordinate_ref)
        component = GoalPhaseNativeScopeComponentV1(
            kind, coordinate_ref, _digest(value)
        )
        existing = components.get(key)
        if existing is not None and existing != component:
            raise GoalPhaseNativeScopeError("component identity is ambiguous")
        components[key] = component

    journal_entries: dict[GoalPhaseCoordinate, list[object]] = {}
    if type(document) is GoalPhaseNativeDocumentV3:
        journal_wire = cast(dict[str, object], document_wire["phase_operation_journal"])
        entries_wire = cast(list[object], journal_wire["entries"])
        for entry, entry_wire in zip(document.phase_operation_journal.entries, entries_wire, strict=True):
            journal_entries.setdefault(entry.coordinate, []).append(entry_wire)

    def add_journal(coordinate: GoalPhaseCoordinate) -> None:
        entries = journal_entries.get(coordinate)
        if entries:
            # Journal structure affects only its Phase, containing lane, and graph.
            # This is not a claim that the actor action or policy was verified.
            add("phase-operation-journal", _coordinate_ref(coordinate), entries)

    add("goal-global", document.goal_tag, goal_authority.semantic_wire())
    add(
        "dependency-snapshot",
        descriptor.scope_ref,
        dependency_snapshot.to_wire(),
    )
    if descriptor.profile is GoalPhaseNativeScopeProfile.GOAL_GRAPH:
        for lane in lane_authorities:
            add(
                "lane-direction",
                _lane_ref(lane.goal_tag, lane.lane_key),
                lane.semantic_wire(),
            )
            disagreement = _lane_work_disagreement(document, lane)
            add(
                "lane-work-consistency",
                _lane_ref(lane.goal_tag, lane.lane_key),
                {"disagreement": disagreement},
            )
        for definition in document.definitions:
            add(
                "phase-definition",
                _coordinate_ref(definition.coordinate),
                _definition_wire(document_wire, definition.coordinate),
            )
            add_journal(definition.coordinate)
        for phase in document.operational_bundle.phases:
            add(
                "phase-operational",
                _coordinate_ref(phase.coordinate),
                _phase_wire(bundle_wire, phase.coordinate),
            )
        for dependency in document.operational_bundle.dependencies:
            ref = _dependency_ref(dependency.owner_goal_tag, dependency.dependency_key)
            add(
                "dependency-declaration",
                ref,
                _dependency_wire(
                    bundle_wire, dependency.owner_goal_tag, dependency.dependency_key
                ),
            )
            observation = observation_map.get(
                (dependency.owner_goal_tag, dependency.dependency_key)
            )
            if observation is not None:
                add("dependency-observation", ref, observation.to_wire())
        for dependency in document.unresolved_dependencies:
            add(
                "dependency-unresolved",
                _dependency_ref(dependency.owner_goal_tag, dependency.dependency_key),
                _unresolved_wire(
                    document_wire, dependency.owner_goal_tag, dependency.dependency_key
                ),
            )
    else:
        roots = (
            tuple(
                item.coordinate
                for item in document.definitions
                if item.coordinate.lane_key == descriptor.root.lane_key
            )
            if descriptor.profile is GoalPhaseNativeScopeProfile.LANE_DIRECTION
            else (descriptor.root,)
        )
        lane = lane_map[descriptor.root.lane_key]
        add(
            "lane-direction",
            _lane_ref(lane.goal_tag, lane.lane_key),
            lane.semantic_wire(),
        )
        add(
            "lane-work-consistency",
            _lane_ref(lane.goal_tag, lane.lane_key),
            {"disagreement": _lane_work_disagreement(document, lane)},
        )
        for root in roots:
            add(
                "phase-definition",
                _coordinate_ref(root),
                _definition_wire(document_wire, root),
            )
            add_journal(root)
            phase = phases.get(root)
            if phase is not None:
                add(
                    "phase-operational",
                    _coordinate_ref(root),
                    _phase_wire(bundle_wire, root),
                )
            for dependency in document.operational_bundle.dependencies:
                if dependency.dependent != root:
                    continue
                ref = _dependency_ref(
                    dependency.owner_goal_tag, dependency.dependency_key
                )
                add(
                    "dependency-declaration",
                    ref,
                    _dependency_wire(
                        bundle_wire,
                        dependency.owner_goal_tag,
                        dependency.dependency_key,
                    ),
                )
                prerequisite = definitions.get(dependency.prerequisite)
                if prerequisite is not None:
                    add(
                        "prerequisite-definition",
                        _coordinate_ref(dependency.prerequisite),
                        _definition_wire(document_wire, dependency.prerequisite),
                    )
                    prerequisite_phase = phases.get(dependency.prerequisite)
                    if prerequisite_phase is not None:
                        add(
                            "prerequisite-operational",
                            _coordinate_ref(dependency.prerequisite),
                            _phase_wire(bundle_wire, dependency.prerequisite),
                        )
                observation = observation_map.get(
                    (dependency.owner_goal_tag, dependency.dependency_key)
                )
                if observation is not None:
                    add("dependency-observation", ref, observation.to_wire())
            for dependency in document.unresolved_dependencies:
                if dependency.dependent == root:
                    add(
                        "dependency-unresolved",
                        _dependency_ref(
                            dependency.owner_goal_tag, dependency.dependency_key
                        ),
                        _unresolved_wire(
                            document_wire,
                            dependency.owner_goal_tag,
                            dependency.dependency_key,
                        ),
                    )

    ordered = tuple(components[key] for key in sorted(components))
    scope_digest = _digest([item.to_wire() for item in ordered])
    included_lane_keys = (
        {item.lane_key for item in lane_authorities}
        if descriptor.profile is GoalPhaseNativeScopeProfile.GOAL_GRAPH
        else {descriptor.root.lane_key}
    )
    ambiguity_values: set[str] = set()
    for lane in lane_authorities:
        if lane.lane_key not in included_lane_keys:
            continue
        ambiguity_values.update(lane.ambiguity_reasons)
        disagreement = _lane_work_disagreement(document, lane)
        if disagreement is not None:
            ambiguity_values.add(disagreement)
    for entry in dependency_snapshot.entries:
        if (
            entry.cross_goal
            and entry.state is not GoalPhaseNativeDependencyCoverageState.OBSERVED
        ):
            ambiguity_values.add(
                f"external-dependency-currentness-unavailable:{entry.owner_goal_tag}:{entry.dependency_key}"
            )
    ambiguity_reasons = tuple(sorted(ambiguity_values))
    qualification = "ambiguous" if ambiguity_reasons else "qualified"
    selected_lanes = {
        item.authority_ref
        for item in lane_authorities
        if item.lane_key in included_lane_keys
    }
    incident_observations = {
        entry.observation_ref
        for entry in dependency_snapshot.entries
        if entry.observation_ref is not None
    }
    authority_binding_refs = tuple(
        sorted(
            {goal_authority.authority_ref, dependency_snapshot.snapshot_ref}
            | selected_lanes
            | incident_observations
        )
    )
    body = {
        "schema_id": GOAL_PHASE_NATIVE_SCOPE_PROJECTION_SCHEMA,
        "effect_profile": "read_only_non_authorizing",
        "descriptor": descriptor.to_wire(),
        "document_ref": document.document_ref,
        "source_revision_ref": goal_authority.source_revision_ref,
        "authority_binding_refs": list(authority_binding_refs),
        "dependency_snapshot_ref": dependency_snapshot.snapshot_ref,
        "components": [item.to_wire() for item in ordered],
        "scope_digest": scope_digest,
        "qualification": qualification,
        "ambiguity_reasons": list(ambiguity_reasons),
    }
    return GoalPhaseNativeScopeProjectionV1(
        descriptor=descriptor,
        document_ref=document.document_ref,
        source_revision_ref=goal_authority.source_revision_ref,
        authority_binding_refs=authority_binding_refs,
        dependency_snapshot_ref=dependency_snapshot.snapshot_ref,
        components=ordered,
        scope_digest=scope_digest,
        qualification=qualification,
        ambiguity_reasons=ambiguity_reasons,
        projection_ref="goal-phase-native-scope-projection:" + fingerprint(body),
    )


def assess_goal_phase_native_scope_advancement(
    *,
    previous: GoalPhaseNativeScopeProjectionV1,
    candidate: GoalPhaseNativeScopeProjectionV1,
    source_epoch: GoalPhaseNativeScopeSourceEpochV1,
) -> GoalPhaseNativeScopeAdvancementV1:
    previous.__post_init__()
    candidate.__post_init__()
    _require_verified_source_epoch(source_epoch)
    if previous.descriptor != candidate.descriptor:
        raise GoalPhaseNativeScopeError("scope descriptor drift is ambiguous")
    if (
        source_epoch.previous_source.repository_revision_ref
        != previous.source_revision_ref
        or source_epoch.candidate_source.repository_revision_ref
        != candidate.source_revision_ref
    ):
        raise GoalPhaseNativeScopeError("source epoch does not bind both projections")
    changes = _changes(previous.components, candidate.components)
    authority_ambiguity_changed = (
        previous.ambiguity_reasons != candidate.ambiguity_reasons
    )
    stable_background_ambiguity = (
        previous.ambiguity_reasons
        and previous.ambiguity_reasons == candidate.ambiguity_reasons
    )
    if (
        source_epoch.lineage.relation == "unproven"
        or source_epoch.compatibility_relation
        is GoalPhaseNativeCompatibilityRelation.UNKNOWN
        or authority_ambiguity_changed
        or (
            stable_background_ambiguity
            and previous.scope_digest == candidate.scope_digest
        )
    ):
        relation = GoalPhaseNativeScopeRelation.AMBIGUOUS
        currentness = GoalPhaseNativeRetainedCurrentness.AMBIGUOUS
        disposition = GoalPhaseNativeAdvancementDisposition.REFUSE
    elif previous.scope_digest == candidate.scope_digest:
        relation = GoalPhaseNativeScopeRelation.UNCHANGED
        currentness = GoalPhaseNativeRetainedCurrentness.CURRENT
        disposition = (
            GoalPhaseNativeAdvancementDisposition.EXACT
            if source_epoch.lineage.relation == "equal"
            and previous.document_ref == candidate.document_ref
            else GoalPhaseNativeAdvancementDisposition.REOBSERVED_UNCHANGED
        )
    else:
        relation = GoalPhaseNativeScopeRelation.CHANGED
        currentness = GoalPhaseNativeRetainedCurrentness.STALE
        disposition = GoalPhaseNativeAdvancementDisposition.ADMITTED_DELTA_REQUIRED
    aggregate_projection = (
        "exact"
        if source_epoch.lineage.relation == "equal"
        and previous.document_ref == candidate.document_ref
        else "advanced"
    )
    body = {
        "schema_id": GOAL_PHASE_NATIVE_SCOPE_ADVANCEMENT_SCHEMA,
        "effect_profile": "read_only_non_authorizing",
        "descriptor": previous.descriptor.to_wire(),
        "previous_document_ref": previous.document_ref,
        "candidate_document_ref": candidate.document_ref,
        "source_epoch": source_epoch.to_wire(),
        "previous_scope_digest": previous.scope_digest,
        "candidate_scope_digest": candidate.scope_digest,
        "changes": [item.to_wire() for item in changes],
        "aggregate_projection": aggregate_projection,
        "scope_relation": relation.value,
        "retained_scope_currentness": currentness.value,
        "disposition": disposition.value,
    }
    return GoalPhaseNativeScopeAdvancementV1(
        descriptor=previous.descriptor,
        previous_document_ref=previous.document_ref,
        candidate_document_ref=candidate.document_ref,
        source_epoch=source_epoch,
        previous_scope_digest=previous.scope_digest,
        candidate_scope_digest=candidate.scope_digest,
        changes=changes,
        aggregate_projection=aggregate_projection,
        scope_relation=relation,
        retained_scope_currentness=currentness,
        disposition=disposition,
        advancement_ref="goal-phase-native-scope-advancement:" + fingerprint(body),
    )


def admit_goal_phase_native_scope_delta(
    *,
    advancement: GoalPhaseNativeScopeAdvancementV1,
    previous_projection: GoalPhaseNativeScopeProjectionV1,
    candidate_projection: GoalPhaseNativeScopeProjectionV1,
    source_epoch: GoalPhaseNativeScopeSourceEpochV1,
    before_document: GoalPhaseNativeDocumentV2,
    after_document: GoalPhaseNativeDocumentV2,
    publication_receipt: GoalPhasePublicationReceiptV1,
    reconciliation_receipt: GoalPhaseProjectionReconciliationReceiptV1,
    projection_currentness: GoalPhaseProjectionCurrentnessVerificationV1,
) -> GoalPhaseNativeScopeDeltaAdmissionV1:
    """Qualify one exact Phase Work delta without rebinding retained authority."""

    advancement.__post_init__()
    expected_advancement = assess_goal_phase_native_scope_advancement(
        previous=previous_projection,
        candidate=candidate_projection,
        source_epoch=source_epoch,
    )
    if advancement != expected_advancement:
        raise GoalPhaseNativeScopeError("delta advancement is not authority-derived")
    before_document.__post_init__()
    after_document.__post_init__()
    publication_receipt.__post_init__()
    if (
        type(reconciliation_receipt)
        is not GoalPhaseProjectionReconciliationReceiptV1
    ):
        raise TypeError("reconciliation receipt type must be exact")
    if (
        advancement.descriptor.profile
        is not GoalPhaseNativeScopeProfile.PHASE_DIRECTION
    ):
        raise GoalPhaseNativeScopeError(
            "delta admission requires phase direction scope"
        )
    if (
        advancement.scope_relation is not GoalPhaseNativeScopeRelation.CHANGED
        or advancement.retained_scope_currentness
        is not GoalPhaseNativeRetainedCurrentness.STALE
        or advancement.disposition
        is not GoalPhaseNativeAdvancementDisposition.ADMITTED_DELTA_REQUIRED
        or advancement.aggregate_projection != "advanced"
    ):
        raise GoalPhaseNativeScopeError("scope is not an admissible changed delta")
    expected_change = GoalPhaseNativeScopeChangeV1(
        kind="phase-operational",
        coordinate_ref=_coordinate_ref(advancement.descriptor.root),
        before_digest=_component_digest(
            advancement, "phase-operational", before=True
        ),
        after_digest=_component_digest(
            advancement, "phase-operational", before=False
        ),
    )
    if advancement.changes != (expected_change,):
        raise GoalPhaseNativeScopeError(
            "delta is not one exact Phase operational change"
        )
    if publication_receipt.operation is not GoalPhaseMutationKind.CONTINUE_WORK:
        raise GoalPhaseNativeScopeError("delta publication is not continue_work")
    if publication_receipt.coordinate != advancement.descriptor.root:
        raise GoalPhaseNativeScopeError("delta publication coordinate differs")
    if (
        advancement.previous_document_ref != before_document.document_ref
        or advancement.candidate_document_ref != after_document.document_ref
    ):
        raise GoalPhaseNativeScopeError("delta documents differ from advancement")
    verify_goal_phase_publication_transition(
        before_document=before_document,
        after_document=after_document,
        publication_receipt=publication_receipt,
    )
    if (
        publication_receipt.before_binding.projection_revision.source_sha256
        != advancement.source_epoch.previous_source.goal_sha256
        or publication_receipt.after_binding.projection_revision.source_sha256
        != advancement.source_epoch.candidate_source.goal_sha256
    ):
        raise GoalPhaseNativeScopeError("publication source binding differs from epoch")
    canonical_reconciliation = reconcile_goal_phase_projection(
        publication_receipt=publication_receipt,
        worktree_current=True,
        index_current=True,
    )
    if reconciliation_receipt != canonical_reconciliation:
        raise GoalPhaseNativeScopeError(
            "delta reconciliation is not current and canonical"
        )
    _require_verified_projection_currentness(projection_currentness)
    if (
        projection_currentness.goal_path != publication_receipt.changed_paths[0]
        or projection_currentness.publication_receipt_ref
        != publication_receipt.receipt_ref
        or projection_currentness.publication_commit_ref
        != publication_receipt.after_binding.projection_revision.repository_commit
        or projection_currentness.observed_head_ref
        != source_epoch.observed_head_ref
    ):
        raise GoalPhaseNativeScopeError(
            "projection currentness does not bind the admitted source epoch"
        )
    body = {
        "schema_id": GOAL_PHASE_NATIVE_SCOPE_DELTA_ADMISSION_SCHEMA,
        "effect_profile": "read_only_non_authorizing",
        "descriptor": advancement.descriptor.to_wire(),
        "advancement_ref": advancement.advancement_ref,
        "publication_receipt_ref": publication_receipt.receipt_ref,
        "reconciliation_receipt_ref": reconciliation_receipt.receipt_ref,
        "projection_currentness_verification_ref": (
            projection_currentness.verification_ref
        ),
        "admitted_change": expected_change.to_wire(),
    }
    return GoalPhaseNativeScopeDeltaAdmissionV1(
        descriptor=advancement.descriptor,
        advancement_ref=advancement.advancement_ref,
        publication_receipt_ref=publication_receipt.receipt_ref,
        reconciliation_receipt_ref=reconciliation_receipt.receipt_ref,
        projection_currentness_verification_ref=(
            projection_currentness.verification_ref
        ),
        admitted_change=expected_change,
        admission_ref="goal-phase-native-scope-delta-admission:" + fingerprint(body),
    )


def _component_digest(
    advancement: GoalPhaseNativeScopeAdvancementV1,
    kind: str,
    *,
    before: bool,
) -> str:
    matches = tuple(change for change in advancement.changes if change.kind == kind)
    if len(matches) != 1:
        raise GoalPhaseNativeScopeError("required changed component is absent")
    value = matches[0].before_digest if before else matches[0].after_digest
    if value is None:
        raise GoalPhaseNativeScopeError("changed component digest is absent")
    return value


def encode_goal_phase_native_scope_projection(
    value: GoalPhaseNativeScopeProjectionV1,
) -> bytes:
    return _canonical(value.to_wire())


def decode_goal_phase_native_scope_projection(
    payload: bytes,
    *,
    document: NativeDocument,
    descriptor: GoalPhaseNativeScopeDescriptorV1,
    goal_authority: GoalGlobalDirectionAuthorityV1,
    lane_authorities: tuple[GoalLaneDirectionAuthorityV1, ...],
    dependency_observations: tuple[GoalPhaseDependencyObservationV2, ...] = (),
) -> GoalPhaseNativeScopeProjectionV1:
    expected = project_goal_phase_native_scope(
        document=document,
        descriptor=descriptor,
        goal_authority=goal_authority,
        lane_authorities=lane_authorities,
        dependency_observations=dependency_observations,
    )
    if _decode(payload) != expected.to_wire():
        raise GoalPhaseNativeScopeError("scope projection is not canonical")
    return expected


def encode_goal_phase_native_scope_advancement(
    value: GoalPhaseNativeScopeAdvancementV1,
) -> bytes:
    return _canonical(value.to_wire())


def decode_goal_phase_native_scope_advancement(
    payload: bytes,
    *,
    previous_document: NativeDocument,
    candidate_document: NativeDocument,
    descriptor: GoalPhaseNativeScopeDescriptorV1,
    previous_goal_authority: GoalGlobalDirectionAuthorityV1,
    candidate_goal_authority: GoalGlobalDirectionAuthorityV1,
    previous_lane_authorities: tuple[GoalLaneDirectionAuthorityV1, ...],
    candidate_lane_authorities: tuple[GoalLaneDirectionAuthorityV1, ...],
    previous_dependency_observations: tuple[GoalPhaseDependencyObservationV2, ...] = (),
    candidate_dependency_observations: tuple[
        GoalPhaseDependencyObservationV2, ...
    ] = (),
    source_epoch: GoalPhaseNativeScopeSourceEpochV1,
) -> GoalPhaseNativeScopeAdvancementV1:
    previous = project_goal_phase_native_scope(
        document=previous_document,
        descriptor=descriptor,
        goal_authority=previous_goal_authority,
        lane_authorities=previous_lane_authorities,
        dependency_observations=previous_dependency_observations,
    )
    candidate = project_goal_phase_native_scope(
        document=candidate_document,
        descriptor=descriptor,
        goal_authority=candidate_goal_authority,
        lane_authorities=candidate_lane_authorities,
        dependency_observations=candidate_dependency_observations,
    )
    expected = assess_goal_phase_native_scope_advancement(
        previous=previous, candidate=candidate, source_epoch=source_epoch
    )
    if _decode(payload) != expected.to_wire():
        raise GoalPhaseNativeScopeError("scope advancement is not canonical")
    return expected


def encode_goal_phase_native_scope_delta_admission(
    value: GoalPhaseNativeScopeDeltaAdmissionV1,
) -> bytes:
    return _canonical(value.to_wire())


def decode_goal_phase_native_scope_delta_admission(
    payload: bytes,
    *,
    advancement: GoalPhaseNativeScopeAdvancementV1,
    previous_projection: GoalPhaseNativeScopeProjectionV1,
    candidate_projection: GoalPhaseNativeScopeProjectionV1,
    source_epoch: GoalPhaseNativeScopeSourceEpochV1,
    before_document: GoalPhaseNativeDocumentV2,
    after_document: GoalPhaseNativeDocumentV2,
    publication_receipt: GoalPhasePublicationReceiptV1,
    reconciliation_receipt: GoalPhaseProjectionReconciliationReceiptV1,
    projection_currentness: GoalPhaseProjectionCurrentnessVerificationV1,
) -> GoalPhaseNativeScopeDeltaAdmissionV1:
    expected = admit_goal_phase_native_scope_delta(
        advancement=advancement,
        previous_projection=previous_projection,
        candidate_projection=candidate_projection,
        source_epoch=source_epoch,
        before_document=before_document,
        after_document=after_document,
        publication_receipt=publication_receipt,
        reconciliation_receipt=reconciliation_receipt,
        projection_currentness=projection_currentness,
    )
    if _decode(payload) != expected.to_wire():
        raise GoalPhaseNativeScopeError("scope delta admission is not canonical")
    return expected


def _validate_inputs(
    document: NativeDocument,
    descriptor: GoalPhaseNativeScopeDescriptorV1,
    goal: GoalGlobalDirectionAuthorityV1,
    lanes: tuple[GoalLaneDirectionAuthorityV1, ...],
) -> None:
    if type(document) not in {GoalPhaseNativeDocumentV1, GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}:
        raise TypeError("document must be an exact native document")
    document.__post_init__()
    if (
        descriptor.root.goal_tag != document.goal_tag
        or goal.goal_tag != document.goal_tag
    ):
        raise GoalPhaseNativeScopeError("Goal identity differs across scope inputs")
    if (
        isinstance(document, (GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3))
        and goal.execution_authority_ref != document.execution_authority.authority_ref
    ):
        raise GoalPhaseNativeScopeError("Goal-global execution authority differs")
    if type(lanes) is not tuple:
        raise TypeError("lane_authorities must be tuple")
    lane_keys: set[str] = set()
    for lane in lanes:
        lane.__post_init__()
        if lane.goal_tag != document.goal_tag or lane.lane_key in lane_keys:
            raise GoalPhaseNativeScopeError(
                "lane authority is missing, duplicate, or cross-Goal"
            )
        lane_keys.add(lane.lane_key)
    required_lanes = {item.coordinate.lane_key for item in document.definitions}
    if lane_keys != required_lanes:
        raise GoalPhaseNativeScopeError("lane authority set is not complete")


def _lane_work_disagreement(
    document: NativeDocument, lane: GoalLaneDirectionAuthorityV1
) -> str | None:
    if lane.qualification == "ambiguous":
        return "compatibility-lane-authority-ambiguous"
    current = tuple(
        work
        for phase in document.operational_bundle.phases
        if phase.coordinate.lane_key == lane.lane_key
        for work in phase.work_associations
        if work.disposition is GoalLanePhaseWorkDisposition.CURRENT
    )
    if lane.current_issue_ref is None:
        if current:
            return "lane-omits-native-current-work"
        return None
    if lane.current_issue_ref.startswith("TBD:"):
        if current:
            return "planned-lane-conflicts-with-native-current-work"
        return None
    matches = tuple(
        item for item in current if item.issue_ref == lane.current_issue_ref
    )
    if len(matches) != 1 or len(current) != 1:
        return "lane-current-issue-disagrees-with-native-phase-work"
    return None


def _dependency_snapshot(
    *,
    document: NativeDocument,
    descriptor: GoalPhaseNativeScopeDescriptorV1,
    observations: tuple[GoalPhaseDependencyObservationV2, ...],
) -> tuple[
    GoalPhaseNativeDependencySnapshotV1,
    dict[tuple[str, str], GoalPhaseDependencyObservationV2],
]:
    roots = (
        {item.coordinate for item in document.definitions}
        if descriptor.profile is GoalPhaseNativeScopeProfile.GOAL_GRAPH
        else {
            item.coordinate
            for item in document.definitions
            if (
                descriptor.profile is GoalPhaseNativeScopeProfile.LANE_DIRECTION
                and item.coordinate.lane_key == descriptor.root.lane_key
            )
            or item.coordinate == descriptor.root
        }
    )
    dependencies = tuple(
        item
        for item in document.operational_bundle.dependencies
        if descriptor.profile is GoalPhaseNativeScopeProfile.GOAL_GRAPH
        or item.dependent in roots
    )
    unresolved = tuple(
        item
        for item in document.unresolved_dependencies
        if descriptor.profile is GoalPhaseNativeScopeProfile.GOAL_GRAPH
        or item.dependent in roots
    )
    declarations = {
        (item.owner_goal_tag, item.dependency_key): item for item in dependencies
    }
    observation_map: dict[tuple[str, str], GoalPhaseDependencyObservationV2] = {}
    for observation in observations:
        key = (observation.dependent.goal_tag, observation.dependency_key)
        dependency = declarations.get(key)
        if dependency is None or key in observation_map:
            raise GoalPhaseNativeScopeError(
                "dependency observation is unrelated or duplicate"
            )
        canonical = decode_goal_phase_dependency_observation(
            observation.to_wire(), dependency=dependency
        )
        observation_map[key] = canonical

    entries: list[GoalPhaseNativeDependencyCoverageEntryV1] = []
    for dependency in dependencies:
        key = (dependency.owner_goal_tag, dependency.dependency_key)
        observation = observation_map.get(key)
        entries.append(
            GoalPhaseNativeDependencyCoverageEntryV1(
                owner_goal_tag=dependency.owner_goal_tag,
                dependency_key=dependency.dependency_key,
                dependency_digest=goal_phase_dependency_digest(dependency),
                dependent_ref=_coordinate_ref(dependency.dependent),
                prerequisite_ref=_coordinate_ref(dependency.prerequisite),
                state=(
                    GoalPhaseNativeDependencyCoverageState.OBSERVED
                    if observation is not None
                    else GoalPhaseNativeDependencyCoverageState.NOT_EVALUATED
                ),
                observation_ref=(
                    None if observation is None else observation.observation_ref
                ),
                currentness_ref=(
                    None if observation is None else observation.currentness_ref
                ),
                cross_goal=(
                    dependency.prerequisite.goal_tag != dependency.dependent.goal_tag
                ),
            )
        )
    for dependency in unresolved:
        entries.append(
            GoalPhaseNativeDependencyCoverageEntryV1(
                owner_goal_tag=dependency.owner_goal_tag,
                dependency_key=dependency.dependency_key,
                dependency_digest=_digest(
                    {
                        "owner_goal_tag": dependency.owner_goal_tag,
                        "dependency_key": dependency.dependency_key,
                        "dependent": _coordinate_wire(dependency.dependent),
                        "prerequisite": _coordinate_wire(dependency.prerequisite),
                        "relation": dependency.relation.value,
                        "resolution_state": dependency.resolution_state,
                    }
                ),
                dependent_ref=_coordinate_ref(dependency.dependent),
                prerequisite_ref=_coordinate_ref(dependency.prerequisite),
                state=GoalPhaseNativeDependencyCoverageState.UNRESOLVED,
                observation_ref=None,
                currentness_ref=None,
                cross_goal=(
                    dependency.prerequisite.goal_tag != dependency.dependent.goal_tag
                ),
            )
        )
    entries.sort(key=lambda item: (item.owner_goal_tag, item.dependency_key))
    snapshot = GoalPhaseNativeDependencySnapshotV1(
        descriptor_ref=descriptor.scope_ref,
        entries=tuple(entries),
    )
    return snapshot, observation_map


def _changes(
    before: tuple[GoalPhaseNativeScopeComponentV1, ...],
    after: tuple[GoalPhaseNativeScopeComponentV1, ...],
) -> tuple[GoalPhaseNativeScopeChangeV1, ...]:
    left = {(x.kind, x.coordinate_ref): x.value_digest for x in before}
    right = {(x.kind, x.coordinate_ref): x.value_digest for x in after}
    return tuple(
        GoalPhaseNativeScopeChangeV1(key[0], key[1], left.get(key), right.get(key))
        for key in sorted(set(left) | set(right))
        if left.get(key) != right.get(key)
    )


def _global_body(value: GoalGlobalDirectionAuthorityV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "goal_tag": value.goal_tag,
        "lifecycle_status": value.lifecycle_status,
        "owner_ref": value.owner_ref,
        "governance_authority_refs": list(value.governance_authority_refs),
        "hold_state": value.hold_state,
        "hold_authority_refs": list(value.hold_authority_refs),
        "execution_authority_ref": value.execution_authority_ref,
        "compatibility_guard_ref": value.compatibility_guard_ref,
        "source_revision_ref": value.source_revision_ref,
        "projector_ref": value.projector_ref,
        "projection_receipt_ref": value.projection_receipt_ref,
    }


def _lane_body(value: GoalLaneDirectionAuthorityV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "role": value.role,
        "owner_ref": value.owner_ref,
        "operational_state": value.operational_state,
        "state_detail": value.state_detail,
        "blocker_authority_refs": list(value.blocker_authority_refs),
        "current_issue_ref": value.current_issue_ref,
        "current_issue_authority_ref": value.current_issue_authority_ref,
        "compatibility_guard_ref": value.compatibility_guard_ref,
        "qualification": value.qualification,
        "ambiguity_reasons": list(value.ambiguity_reasons),
        "source_revision_ref": value.source_revision_ref,
        "projector_ref": value.projector_ref,
        "projection_receipt_ref": value.projection_receipt_ref,
    }


def _scope_body(value: GoalPhaseNativeScopeDescriptorV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "root": _coordinate_wire(value.root),
        "profile": value.profile.value,
        "consumer_authority_ref": value.consumer_authority_ref,
        "projector_ref": value.projector_ref,
    }


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, object]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def _coordinate_ref(value: GoalPhaseCoordinate) -> str:
    return f"{value.goal_tag}/{value.lane_key}/{value.phase_key}"


def _lane_ref(goal_tag: str, lane_key: str) -> str:
    return f"{goal_tag}/{lane_key}"


def _dependency_ref(goal_tag: str, key: str) -> str:
    return f"{goal_tag}/dependency/{key}"


def _definition_wire(
    document: dict[str, object], coordinate: GoalPhaseCoordinate
) -> object:
    return _find_coordinate(cast(list[object], document["definitions"]), coordinate)


def _phase_wire(bundle: dict[str, object], coordinate: GoalPhaseCoordinate) -> object:
    return _find_coordinate(cast(list[object], bundle["phases"]), coordinate)


def _find_coordinate(values: list[object], coordinate: GoalPhaseCoordinate) -> object:
    matches = [
        item
        for item in values
        if cast(dict[str, object], item)["coordinate"] == _coordinate_wire(coordinate)
    ]
    if len(matches) != 1:
        raise GoalPhaseNativeScopeError("coordinate projection is not unique")
    return matches[0]


def _dependency_wire(bundle: dict[str, object], owner: str, key: str) -> object:
    values = cast(list[object], bundle["dependencies"])
    matches = [
        item
        for item in values
        if cast(dict[str, object], item)["owner_goal_tag"] == owner
        and cast(dict[str, object], item)["dependency_key"] == key
    ]
    if len(matches) != 1:
        raise GoalPhaseNativeScopeError("dependency projection is not unique")
    return matches[0]


def _unresolved_wire(document: dict[str, object], owner: str, key: str) -> object:
    values = cast(list[object], document["unresolved_dependencies"])
    matches = [
        item
        for item in values
        if cast(dict[str, object], item)["owner_goal_tag"] == owner
        and cast(dict[str, object], item)["dependency_key"] == key
    ]
    if len(matches) != 1:
        raise GoalPhaseNativeScopeError("unresolved dependency is not unique")
    return matches[0]


def _tokens(values: tuple[str, ...], name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be tuple")
    normalized = tuple(required_token(item, name) for item in values)
    if normalized != tuple(sorted(set(normalized))):
        raise GoalPhaseNativeScopeError(f"{name} must be unique and sorted")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def _decode(payload: bytes) -> object:
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    try:
        return json.loads(payload.decode(), object_pairs_hook=_unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseNativeScopeError("payload is not canonical JSON") from error


def _unique(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise GoalPhaseNativeScopeError("duplicate JSON field")
        result[key] = value
    return result
