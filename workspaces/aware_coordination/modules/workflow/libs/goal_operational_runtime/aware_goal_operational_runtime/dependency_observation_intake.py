"""Strict intake for optional GoalDependency operational observations.

The intake boundary preserves evaluator-owned observations. It does not infer
evaluation from Markdown presence, reconstruct evidence, or authorize work.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .dependencies import GoalDependency, GoalDependencyRelation, GoalRowCoordinate
from .dependency_evaluation import (
    GoalDependencyGateObservation,
    GoalDependencyGateState,
    GoalDependencyObservation,
    GoalDependencySatisfaction,
    dependency_definition_digest,
    summarize_goal_dependency_gate,
)
from .identity import (
    normalize_goal_tag,
    optional_token,
    required_token,
    stable_ref,
    unique_tokens,
)

_OBSERVATION_SCHEMA = "aware.goal.dependency.observation.v0"
_GATE_SCHEMA = "aware.goal.dependency.gate.v0"
_INTAKE_SCHEMA = "aware.goal.dependency.observation_intake.v0"
_EFFECT_PROFILE = "read_only_non_authorizing"


class GoalDependencyObservationAvailability(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    EVALUATED = "evaluated"


@dataclass(frozen=True, slots=True)
class GoalDependencyObservationIntake:
    """Declaration-bound optional observation for transport consumers."""

    declaration_digest: str
    availability: GoalDependencyObservationAvailability
    observation: GoalDependencyObservation | None

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": _INTAKE_SCHEMA,
            "effect_profile": _EFFECT_PROFILE,
            "declaration_digest": self.declaration_digest,
            "availability": self.availability.value,
            "observation": (
                None if self.observation is None else self.observation.to_wire()
            ),
        }


def compose_goal_dependency_observation_intake(
    dependency: GoalDependency,
    observation: GoalDependencyObservation | None = None,
) -> GoalDependencyObservationIntake:
    """Bind an optional evaluator observation to one exact declaration."""

    if not isinstance(dependency, GoalDependency):
        raise TypeError("dependency must be GoalDependency")
    if observation is not None:
        validate_goal_dependency_observation(dependency, observation)
    return GoalDependencyObservationIntake(
        declaration_digest=dependency_definition_digest(dependency),
        availability=(
            GoalDependencyObservationAvailability.NOT_EVALUATED
            if observation is None
            else GoalDependencyObservationAvailability.EVALUATED
        ),
        observation=observation,
    )


def decode_goal_dependency_observation_intake(
    payload: Mapping[str, object],
    *,
    dependency: GoalDependency,
) -> GoalDependencyObservationIntake:
    """Decode a strict optional-observation envelope for one declaration."""

    values = _exact_object(
        payload,
        "observation intake",
        {
            "schema_id",
            "effect_profile",
            "declaration_digest",
            "availability",
            "observation",
        },
    )
    _exact_value(values["schema_id"], _INTAKE_SCHEMA, "schema_id")
    _exact_value(values["effect_profile"], _EFFECT_PROFILE, "effect_profile")
    expected_digest = dependency_definition_digest(dependency)
    _exact_value(
        required_token(values["declaration_digest"], "declaration_digest"),
        expected_digest,
        "declaration_digest",
    )
    availability = GoalDependencyObservationAvailability(values["availability"])
    raw_observation = values["observation"]
    if availability is GoalDependencyObservationAvailability.NOT_EVALUATED:
        if raw_observation is not None:
            raise ValueError("not_evaluated intake cannot carry an observation")
        observation = None
    else:
        if raw_observation is None:
            raise ValueError("evaluated intake requires an observation")
        observation = decode_goal_dependency_observation(
            _mapping(raw_observation, "observation"),
            dependency=dependency,
        )
    return GoalDependencyObservationIntake(
        declaration_digest=expected_digest,
        availability=availability,
        observation=observation,
    )


def decode_goal_dependency_observation(
    payload: Mapping[str, object],
    *,
    dependency: GoalDependency,
) -> GoalDependencyObservation:
    """Decode and validate one evaluator-owned observation without deriving it."""

    values = _exact_object(
        payload,
        "dependency observation",
        {
            "schema_id",
            "observation_ref",
            "effect_profile",
            "evaluator_ref",
            "owner_goal_tag",
            "dependency_key",
            "dependency_digest",
            "relation",
            "dependent",
            "prerequisite",
            "dependent_source_revision_ref",
            "prerequisite_source_revision_ref",
            "prerequisite_gate_digest",
            "satisfaction",
            "evidence_refs",
            "qualification_refs",
            "reasons",
        },
    )
    observation = GoalDependencyObservation(
        schema_id=required_token(values["schema_id"], "schema_id"),
        observation_ref=required_token(values["observation_ref"], "observation_ref"),
        effect_profile=required_token(values["effect_profile"], "effect_profile"),
        evaluator_ref=required_token(values["evaluator_ref"], "evaluator_ref"),
        owner_goal_tag=normalize_goal_tag(values["owner_goal_tag"]),
        dependency_key=required_token(values["dependency_key"], "dependency_key"),
        dependency_digest=required_token(
            values["dependency_digest"], "dependency_digest"
        ),
        relation=GoalDependencyRelation(values["relation"]),
        dependent=_decode_coordinate(values["dependent"], "dependent"),
        prerequisite=_decode_coordinate(values["prerequisite"], "prerequisite"),
        dependent_source_revision_ref=optional_token(
            values["dependent_source_revision_ref"],
            "dependent_source_revision_ref",
        ),
        prerequisite_source_revision_ref=optional_token(
            values["prerequisite_source_revision_ref"],
            "prerequisite_source_revision_ref",
        ),
        prerequisite_gate_digest=optional_token(
            values["prerequisite_gate_digest"], "prerequisite_gate_digest"
        ),
        satisfaction=GoalDependencySatisfaction(values["satisfaction"]),
        evidence_refs=_token_list(values["evidence_refs"], "evidence_refs"),
        qualification_refs=_token_list(
            values["qualification_refs"], "qualification_refs"
        ),
        reasons=_token_list(values["reasons"], "reasons"),
    )
    validate_goal_dependency_observation(dependency, observation)
    return observation


def validate_goal_dependency_observation(
    dependency: GoalDependency,
    observation: GoalDependencyObservation,
) -> None:
    """Require a canonical evaluator observation for the exact declaration."""

    if not isinstance(dependency, GoalDependency):
        raise TypeError("dependency must be GoalDependency")
    if not isinstance(observation, GoalDependencyObservation):
        raise TypeError("observation must be GoalDependencyObservation")
    _exact_value(observation.schema_id, _OBSERVATION_SCHEMA, "schema_id")
    _exact_value(observation.effect_profile, _EFFECT_PROFILE, "effect_profile")
    for field in (
        "observation_ref",
        "evaluator_ref",
        "owner_goal_tag",
        "dependency_key",
        "dependency_digest",
    ):
        required_token(getattr(observation, field), field)
    for field in (
        "dependent_source_revision_ref",
        "prerequisite_source_revision_ref",
        "prerequisite_gate_digest",
    ):
        optional_token(getattr(observation, field), field)
    for field in ("evidence_refs", "qualification_refs", "reasons"):
        values = getattr(observation, field)
        if not isinstance(values, tuple):
            raise TypeError(f"{field} must be a tuple")
        _exact_value(values, unique_tokens(values, field), field)
    if not isinstance(observation.satisfaction, GoalDependencySatisfaction):
        raise TypeError("satisfaction must be GoalDependencySatisfaction")
    expected = {
        "owner_goal_tag": dependency.owner_goal_tag,
        "dependency_key": dependency.dependency_key,
        "dependency_digest": dependency_definition_digest(dependency),
        "relation": dependency.relation,
        "dependent": dependency.dependent,
        "prerequisite": dependency.prerequisite,
    }
    for field, expected_value in expected.items():
        _exact_value(getattr(observation, field), expected_value, field)
    _validate_observation_shape(observation)
    expected_ref = stable_ref(
        kind="goal-dependency-observation",
        authority_ref=observation.evaluator_ref,
        coordinates=(
            observation.owner_goal_tag,
            observation.dependency_key,
            observation.dependency_digest,
            observation.satisfaction.value,
            observation.dependent_source_revision_ref or "none",
            observation.prerequisite_source_revision_ref or "none",
            observation.prerequisite_gate_digest or "none",
            *observation.evidence_refs,
            *observation.qualification_refs,
            *observation.reasons,
        ),
    )
    _exact_value(observation.observation_ref, expected_ref, "observation_ref")


def decode_goal_dependency_gate_observation(
    payload: Mapping[str, object],
    *,
    observations: tuple[GoalDependencyObservation, ...],
) -> GoalDependencyGateObservation:
    """Decode a gate and prove it is the canonical summary of observations."""

    if not isinstance(observations, tuple) or not all(
        isinstance(item, GoalDependencyObservation) for item in observations
    ):
        raise TypeError("observations must be a tuple of GoalDependencyObservation")
    values = _exact_object(
        payload,
        "dependency gate observation",
        {
            "schema_id",
            "gate_ref",
            "effect_profile",
            "evaluator_ref",
            "dependent",
            "state",
            "dependency_observation_refs",
            "blocking_dependency_keys",
            "reasons",
        },
    )
    gate = GoalDependencyGateObservation(
        schema_id=required_token(values["schema_id"], "schema_id"),
        gate_ref=required_token(values["gate_ref"], "gate_ref"),
        effect_profile=required_token(values["effect_profile"], "effect_profile"),
        evaluator_ref=required_token(values["evaluator_ref"], "evaluator_ref"),
        dependent=_decode_coordinate(values["dependent"], "dependent"),
        state=GoalDependencyGateState(values["state"]),
        dependency_observation_refs=_token_list(
            values["dependency_observation_refs"],
            "dependency_observation_refs",
        ),
        blocking_dependency_keys=_token_list(
            values["blocking_dependency_keys"], "blocking_dependency_keys"
        ),
        reasons=_token_list(values["reasons"], "reasons"),
    )
    _exact_value(gate.schema_id, _GATE_SCHEMA, "schema_id")
    _exact_value(gate.effect_profile, _EFFECT_PROFILE, "effect_profile")
    canonical = summarize_goal_dependency_gate(
        gate.dependent,
        observations,
        evaluator_ref=gate.evaluator_ref,
    )
    if gate != canonical:
        raise ValueError("dependency gate differs from canonical observation summary")
    return gate


def _validate_observation_shape(observation: GoalDependencyObservation) -> None:
    resolved = all(
        value is not None
        for value in (
            observation.dependent_source_revision_ref,
            observation.prerequisite_source_revision_ref,
            observation.prerequisite_gate_digest,
        )
    )
    if observation.satisfaction is GoalDependencySatisfaction.UNRESOLVED:
        if resolved:
            raise ValueError("unresolved observation must carry an unresolved source")
        if observation.evidence_refs or observation.qualification_refs:
            raise ValueError("unresolved observation cannot carry admitted evidence")
        if not observation.reasons:
            raise ValueError("unresolved observation requires reasons")
    elif not resolved:
        raise ValueError(
            "evaluated dependency result requires resolved source bindings"
        )
    elif observation.satisfaction is GoalDependencySatisfaction.SATISFIED:
        if not observation.evidence_refs or not observation.qualification_refs:
            raise ValueError("satisfied observation requires admitted evidence")
        if observation.reasons:
            raise ValueError("satisfied observation cannot carry reasons")
    elif observation.satisfaction is GoalDependencySatisfaction.PENDING:
        if observation.evidence_refs or observation.qualification_refs:
            raise ValueError("pending observation cannot carry admitted evidence")
        expected_reason = f"{_required_kind(observation.relation)}_evidence_missing"
        if observation.reasons != (expected_reason,):
            raise ValueError("pending observation has noncanonical reasons")
    elif not observation.evidence_refs or not observation.qualification_refs:
        raise ValueError("stale observation requires prior admitted evidence")
    elif not observation.reasons:
        raise ValueError("stale observation requires drift reasons")


def _required_kind(relation: GoalDependencyRelation) -> str:
    return {
        GoalDependencyRelation.REQUIRES_COMPLETION: "completion",
        GoalDependencyRelation.REQUIRES_ACCEPTANCE: "acceptance",
    }[relation]


def _decode_coordinate(value: object, field: str) -> GoalRowCoordinate:
    values = _exact_object(
        _mapping(value, field),
        field,
        {"goal_tag", "lane_key", "row_key"},
    )
    return GoalRowCoordinate(
        goal_tag=normalize_goal_tag(values["goal_tag"]),
        lane_key=required_token(values["lane_key"], f"{field}.lane_key"),
        row_key=required_token(values["row_key"], f"{field}.row_key"),
    )


def _token_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return unique_tokens(value, field)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field} keys must be strings")
    return value


def _exact_object(
    value: Mapping[str, object],
    field: str,
    expected_keys: set[str],
) -> Mapping[str, object]:
    values = _mapping(value, field)
    actual_keys = set(values)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unknown = sorted(actual_keys - expected_keys)
        raise ValueError(f"{field} fields differ; missing={missing}, unknown={unknown}")
    return values


def _exact_value(value: object, expected: object, field: str) -> None:
    if value != expected:
        raise ValueError(f"{field} differs from the required contract")
