"""Portable dependency fragment for the canonical Goal API View.

The fragment carries declaration and evaluator-owned observation truth. It does
not evaluate gates, resolve endpoints, infer currentness, or authorize work.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, cast

from aware_goal_operational_runtime.dependencies import (
    GoalDependency,
    GoalDependencyRelation,
    validate_dependency_set,
)
from aware_goal_operational_runtime.dependency_evaluation import (
    GoalDependencyObservation,
    dependency_definition_digest,
)
from aware_goal_operational_runtime.dependency_observation_intake import (
    decode_goal_dependency_observation,
)

class _DependencyDeclarationSource(Protocol):
    @property
    def dependencies(self) -> tuple[GoalDependency, ...]: ...


class _LandscapeDependencySource(Protocol):
    @property
    def projection(self) -> _DependencyDeclarationSource: ...

    def to_json(self) -> dict[str, object]: ...

_SCHEMA_ID = "aware.goal.dependency_view.v1"
_EFFECT_PROFILE = "read_only_non_authorizing"


class GoalDependencyPresentationState(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    PENDING = "pending"
    SATISFIED = "satisfied"
    STALE = "stale"
    UNRESOLVED = "unresolved"


class GoalDependencyEndpointPresence(StrEnum):
    PRESENT = "present"
    UNRESOLVED = "unresolved"
    EXTERNAL_UNRESOLVED = "external_unresolved"


@dataclass(frozen=True, slots=True)
class GoalDependencyViewSourceV1:
    authority_profile: str
    source_ref: str | None
    source_digest: str

    def __post_init__(self) -> None:
        _ = _required_text(self.authority_profile, "authority_profile")
        if self.source_ref is not None:
            _ = _required_text(self.source_ref, "source_ref")
        _ = _required_text(self.source_digest, "source_digest")

    def to_wire(self) -> dict[str, object]:
        return {
            "authority_profile": self.authority_profile,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyDocumentPresenceV1:
    dependent: GoalDependencyEndpointPresence
    prerequisite: GoalDependencyEndpointPresence

    def __post_init__(self) -> None:
        if self.dependent is GoalDependencyEndpointPresence.EXTERNAL_UNRESOLVED:
            raise ValueError("dependent endpoint belongs to the owning Goal")

    def to_wire(self) -> dict[str, str]:
        return {
            "dependent": self.dependent.value,
            "prerequisite": self.prerequisite.value,
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyViewItemV1:
    declaration: GoalDependency
    declaration_digest: str
    document_presence: GoalDependencyDocumentPresenceV1
    operational_observation: GoalDependencyObservation | None

    def __post_init__(self) -> None:
        expected_digest = dependency_definition_digest(self.declaration)
        if self.declaration_digest != expected_digest:
            raise ValueError("declaration_digest does not match declaration")
        if self.operational_observation is not None:
            _ = decode_goal_dependency_observation(
                self.operational_observation.to_wire(),
                dependency=self.declaration,
            )

    @property
    def presentation_state(self) -> GoalDependencyPresentationState:
        if self.operational_observation is None:
            return GoalDependencyPresentationState.NOT_EVALUATED
        return GoalDependencyPresentationState(
            self.operational_observation.satisfaction.value
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "declaration": self.declaration.to_wire(),
            "declaration_digest": self.declaration_digest,
            "document_presence": self.document_presence.to_wire(),
            "presentation_state": self.presentation_state.value,
            "operational_observation": (
                None
                if self.operational_observation is None
                else self.operational_observation.to_wire()
            ),
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyLaneRelationshipV1:
    prerequisite_goal_tag: str
    prerequisite_lane_key: str
    dependent_goal_tag: str
    dependent_lane_key: str
    dependency_keys: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "prerequisite_goal_tag": self.prerequisite_goal_tag,
            "prerequisite_lane_key": self.prerequisite_lane_key,
            "dependent_goal_tag": self.dependent_goal_tag,
            "dependent_lane_key": self.dependent_lane_key,
            "dependency_keys": list(self.dependency_keys),
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyCrossGoalRelationshipV1:
    prerequisite_goal_tag: str
    dependent_goal_tag: str
    dependency_keys: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "prerequisite_goal_tag": self.prerequisite_goal_tag,
            "dependent_goal_tag": self.dependent_goal_tag,
            "dependency_keys": list(self.dependency_keys),
        }


@dataclass(frozen=True, slots=True)
class GoalDependencyViewContractV1:
    goal_tag: str
    source: GoalDependencyViewSourceV1
    dependencies: tuple[GoalDependencyViewItemV1, ...]

    def __post_init__(self) -> None:
        _ = _required_text(self.goal_tag, "goal_tag")
        declarations = tuple(item.declaration for item in self.dependencies)
        if any(
            declaration.owner_goal_tag != self.goal_tag for declaration in declarations
        ):
            raise ValueError("every dependency must be owned by goal_tag")
        validate_dependency_set(declarations)

    @property
    def lane_relationships(self) -> tuple[GoalDependencyLaneRelationshipV1, ...]:
        grouped: dict[tuple[str, str, str, str], list[str]] = {}
        for item in self.dependencies:
            declaration = item.declaration
            key = (
                declaration.prerequisite_goal_tag,
                declaration.prerequisite_lane_key,
                declaration.owner_goal_tag,
                declaration.dependent_lane_key,
            )
            grouped.setdefault(key, []).append(declaration.dependency_key)
        return tuple(
            GoalDependencyLaneRelationshipV1(*key, tuple(sorted(values)))
            for key, values in sorted(grouped.items())
        )

    @property
    def cross_goal_relationships(
        self,
    ) -> tuple[GoalDependencyCrossGoalRelationshipV1, ...]:
        grouped: dict[tuple[str, str], list[str]] = {}
        for item in self.dependencies:
            declaration = item.declaration
            if declaration.prerequisite_goal_tag == declaration.owner_goal_tag:
                continue
            key = (declaration.prerequisite_goal_tag, declaration.owner_goal_tag)
            grouped.setdefault(key, []).append(declaration.dependency_key)
        return tuple(
            GoalDependencyCrossGoalRelationshipV1(*key, tuple(sorted(values)))
            for key, values in sorted(grouped.items())
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": _SCHEMA_ID,
            "effect_profile": _EFFECT_PROFILE,
            "goal_tag": self.goal_tag,
            "source": self.source.to_wire(),
            "dependencies": [item.to_wire() for item in self.dependencies],
            "lane_relationships": [
                relationship.to_wire() for relationship in self.lane_relationships
            ],
            "cross_goal_relationships": [
                relationship.to_wire() for relationship in self.cross_goal_relationships
            ],
        }


def compose_goal_dependency_view(
    projection: _LandscapeDependencySource,
) -> GoalDependencyViewContractV1:
    """Compose the V2 bridge into the future canonical API View fragment."""

    payload = projection.to_json()
    goal_view_payload = _mapping(payload["goal_view"], "goal_view")
    goal_tag = goal_view_payload.get("tag")
    if not isinstance(goal_tag, str) or not goal_tag:
        raise ValueError("goal_view.tag is required for dependency carriage")
    source_payload = _mapping(payload["snapshot"], "snapshot")
    source_ref = source_payload["source_path"]
    if source_ref is not None and not isinstance(source_ref, str):
        raise TypeError("snapshot.source_path must be text or null")
    source = GoalDependencyViewSourceV1(
        authority_profile=str(payload["authority_profile"]),
        source_ref=source_ref,
        source_digest=str(source_payload["source_sha256"]),
    )
    items: list[GoalDependencyViewItemV1] = []
    dependency_payloads = _list(payload["dependencies"], "dependencies")
    for declaration, item_payload in zip(
        projection.projection.dependencies,
        dependency_payloads,
        strict=True,
    ):
        item_values = _mapping(item_payload, "dependency item")
        raw_observation = item_values["operational_observation"]
        observation = (
            None
            if raw_observation is None
            else decode_goal_dependency_observation(
                _mapping(raw_observation, "operational_observation"),
                dependency=declaration,
            )
        )
        presence = _decode_document_presence(item_values["document_presence"])
        items.append(
            GoalDependencyViewItemV1(
                declaration=declaration,
                declaration_digest=str(item_values["declaration_digest"]),
                document_presence=presence,
                operational_observation=observation,
            )
        )
    return GoalDependencyViewContractV1(
        goal_tag=goal_tag,
        source=source,
        dependencies=tuple(items),
    )


def decode_goal_dependency_view(
    payload: Mapping[str, object],
) -> GoalDependencyViewContractV1:
    """Strictly decode a dependency View fragment and verify derived summaries."""

    values = _exact_object(
        payload,
        "dependency view",
        {
            "schema_id",
            "effect_profile",
            "goal_tag",
            "source",
            "dependencies",
            "lane_relationships",
            "cross_goal_relationships",
        },
    )
    _exact_value(values["schema_id"], _SCHEMA_ID, "schema_id")
    _exact_value(values["effect_profile"], _EFFECT_PROFILE, "effect_profile")
    source_values = _exact_object(
        _mapping(values["source"], "source"),
        "source",
        {"authority_profile", "source_ref", "source_digest"},
    )
    source_ref = source_values["source_ref"]
    if source_ref is not None and not isinstance(source_ref, str):
        raise TypeError("source_ref must be text or null")
    source = GoalDependencyViewSourceV1(
        authority_profile=_required_text(
            source_values["authority_profile"], "authority_profile"
        ),
        source_ref=source_ref,
        source_digest=_required_text(source_values["source_digest"], "source_digest"),
    )
    raw_dependencies = _list(values["dependencies"], "dependencies")
    items: list[GoalDependencyViewItemV1] = []
    for raw_item in raw_dependencies:
        item_values = _exact_object(
            _mapping(raw_item, "dependency item"),
            "dependency item",
            {
                "declaration",
                "declaration_digest",
                "document_presence",
                "presentation_state",
                "operational_observation",
            },
        )
        declaration = _decode_declaration(item_values["declaration"])
        raw_observation = item_values["operational_observation"]
        observation = (
            None
            if raw_observation is None
            else decode_goal_dependency_observation(
                _mapping(raw_observation, "operational_observation"),
                dependency=declaration,
            )
        )
        item = GoalDependencyViewItemV1(
            declaration=declaration,
            declaration_digest=_required_text(
                item_values["declaration_digest"], "declaration_digest"
            ),
            document_presence=_decode_document_presence(
                item_values["document_presence"]
            ),
            operational_observation=observation,
        )
        _exact_value(
            item_values["presentation_state"],
            item.presentation_state.value,
            "presentation_state",
        )
        items.append(item)
    contract = GoalDependencyViewContractV1(
        goal_tag=_required_text(values["goal_tag"], "goal_tag"),
        source=source,
        dependencies=tuple(items),
    )
    _exact_value(
        values["lane_relationships"],
        [relationship.to_wire() for relationship in contract.lane_relationships],
        "lane_relationships",
    )
    _exact_value(
        values["cross_goal_relationships"],
        [relationship.to_wire() for relationship in contract.cross_goal_relationships],
        "cross_goal_relationships",
    )
    return contract


def _decode_declaration(value: object) -> GoalDependency:
    values = _exact_object(
        _mapping(value, "declaration"),
        "declaration",
        {
            "owner_goal_tag",
            "dependency_key",
            "dependent_lane_key",
            "dependent_row_key",
            "prerequisite_goal_tag",
            "prerequisite_lane_key",
            "prerequisite_row_key",
            "relation",
            "reason",
            "evidence_refs",
        },
    )
    raw_evidence_refs = _list(values["evidence_refs"], "evidence_refs")
    if not all(isinstance(item, str) for item in raw_evidence_refs):
        raise TypeError("evidence_refs must contain text")
    evidence_refs = tuple(cast(str, item) for item in raw_evidence_refs)
    return GoalDependency(
        owner_goal_tag=_required_text(values["owner_goal_tag"], "owner_goal_tag"),
        dependency_key=_required_text(values["dependency_key"], "dependency_key"),
        dependent_lane_key=_required_text(
            values["dependent_lane_key"], "dependent_lane_key"
        ),
        dependent_row_key=_required_text(
            values["dependent_row_key"], "dependent_row_key"
        ),
        prerequisite_goal_tag=_required_text(
            values["prerequisite_goal_tag"], "prerequisite_goal_tag"
        ),
        prerequisite_lane_key=_required_text(
            values["prerequisite_lane_key"], "prerequisite_lane_key"
        ),
        prerequisite_row_key=_required_text(
            values["prerequisite_row_key"], "prerequisite_row_key"
        ),
        relation=GoalDependencyRelation(values["relation"]),
        reason=_required_text(values["reason"], "reason"),
        evidence_refs=evidence_refs,
    )


def _decode_document_presence(value: object) -> GoalDependencyDocumentPresenceV1:
    values = _exact_object(
        _mapping(value, "document_presence"),
        "document_presence",
        {"dependent", "prerequisite"},
    )
    return GoalDependencyDocumentPresenceV1(
        dependent=GoalDependencyEndpointPresence(values["dependent"]),
        prerequisite=GoalDependencyEndpointPresence(values["prerequisite"]),
    )


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be an object")
    untyped = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in untyped):
        raise TypeError(f"{field} keys must be text")
    return {cast(str, key): item for key, item in untyped.items()}


def _list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return cast(list[object], value).copy()


def _exact_object(
    value: Mapping[str, object],
    field: str,
    expected: set[str],
) -> dict[str, object]:
    supplied = set(value)
    if supplied != expected:
        raise ValueError(
            f"{field} fields differ: missing={sorted(expected - supplied)}, "
            + f"unknown={sorted(supplied - expected)}"
        )
    return deepcopy(dict(value))


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field} must be non-empty text")
    return value


def _exact_value(actual: object, expected: object, field: str) -> None:
    if actual != expected:
        raise ValueError(f"{field} does not match canonical value")
