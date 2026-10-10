"""Immutable Workspace semantic dependency graph and aggregate evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, cast

from aware_code_semantic_contract_runtime import (
    CodeSemanticContractMatch,
    CodeSemanticContractMatchAdmission,
    CodeSemanticMaterializationIntent,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticDependencyDemandSet,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)

from .materialization_membership_catalog import (
    WorkspaceSemanticMaterializationPackageEntry,
)
from .materialization_selection import (
    WorkspaceAdmittedPackageIntent,
    WorkspaceMaterializationSelectionResolution,
    _content_digest,
    _exact_tuple,
    _nonnegative,
    _ordered_tuple,
    _preflight_exact,
    _preflight_tuple,
    _token,
)
from .materialization_session import (
    WORKSPACE_MATERIALIZATION_SESSION_EVENT_REREAD_EVIDENCE_V3,
    WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT_V3,
    WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3,
    WorkspaceMaterializationSessionAppendRequestV3,
    WorkspaceMaterializationSessionEventRereadEvidenceV3,
    WorkspaceMaterializationSessionFanoutReceiptV3,
    WorkspaceMaterializationSessionSourceEvidenceV3,
)
from .semantic_materialization_publication import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3,
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3,
    WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3,
    WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3,
    WorkspaceMaterializationPackageOccurrenceV4,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationHeadV3,
    WorkspaceSemanticMaterializationPublicationReceiptV3,
    WorkspaceSemanticMaterializationRequestV3,
)

WORKSPACE_DEPENDENCY_TARGET_RESOLUTION = (
    "aware.workspace.dependency-target-resolution.v1"
)
WORKSPACE_SEMANTIC_PLANNED_DEPENDENCY_INPUT = (
    "aware.workspace.semantic-planned-dependency-input.v1"
)
WORKSPACE_SEMANTIC_PLANNING_DEMAND_CLOSURE = (
    "aware.workspace.semantic-planning-demand-closure.v1"
)
WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION = (
    "aware.workspace.semantic-package-head-observation.v1"
)
WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION_V2 = (
    "aware.workspace.semantic-package-head-observation.v2"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_LOCAL_ROOT_ASSOCIATION = (
    "aware.workspace.semantic-materialization-local-root-association.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_ADMISSION = (
    "aware.workspace.semantic-materialization-graph-plan-admission.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_RESULT = (
    "aware.workspace.semantic-materialization-graph-plan-result.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_EXECUTION_BINDING = (
    "aware.workspace.semantic-materialization-node-execution-binding.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EXECUTION_BINDING = (
    "aware.workspace.semantic-materialization-graph-execution-binding.v3"
)
WORKSPACE_FULFILLED_DEPENDENCY_PRODUCT_V3 = (
    "aware.workspace.fulfilled-dependency-product.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_RESULT_EVIDENCE_V3 = (
    "aware.workspace.semantic-materialization-node-result-evidence.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_FAILURE_EVIDENCE_ENTRY_V2 = (
    "aware.workspace.semantic-materialization-failure-evidence-entry.v2"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_FAILURE_V3 = (
    "aware.workspace.semantic-materialization-terminal-failure.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3 = (
    "aware.workspace.semantic-materialization-graph-result.v3"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE = (
    "aware.workspace.semantic-materialization-graph-node.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EDGE = (
    "aware.workspace.semantic-materialization-graph-edge.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH = (
    "aware.workspace.semantic-materialization-graph.v1"
)

WORKSPACE_OBSERVED_HEAD_CLASSIFICATIONS = ("current", "missing", "stale")
WORKSPACE_MATERIALIZATION_PLANNING_TIMING_STAGES = (
    "selection_expand",
    "provider_match",
    "dependency_plan",
    "graph_derive",
    "total",
)
WORKSPACE_MATERIALIZATION_PLANNING_COUNTERS = (
    "catalog_lookup_count",
    "provider_match_count",
    "demand_planner_invocation_count",
    "fan_in_context_count",
    "fan_in_iteration_count",
    "fan_in_lattice_addition_count",
    "fan_in_equal_context_reuse_count",
    "node_count",
    "edge_count",
    "head_read_count",
    "dependency_body_read_count",
)
WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_OBSERVATION_ROLES_V2 = (
    "dependency_h1",
    "dependency_h2",
    "package_result",
    "package_reuse",
)
WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2 = (
    "dependency_body_observation_count",
    "dependency_head_observation_count",
    "edge_count",
    "executed_count",
    "fulfilled_product_count",
    "node_count",
    "package_head_observation_count",
    "publication_count",
    "reused_count",
    "session_event_count",
)
WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_MATRIX_V2 = {
    ("binding_validation", "binding_invalid"): ("node_binding",),
    ("dependency_head_reread", "target_head_absent"): ("target_resolution",),
    ("dependency_head_reread", "target_head_mismatch"): (
        "head_h1",
        "target_resolution",
    ),
    ("dependency_head_reread", "target_head_disappeared"): (
        "body",
        "head_h1",
        "target_resolution",
    ),
    ("dependency_head_reread", "target_head_moved"): (
        "body",
        "head_h1",
        "head_h2",
        "target_resolution",
    ),
    ("dependency_body_read", "body_absent"): (
        "body_coordinate",
        "head_h1",
        "target_resolution",
    ),
    ("dependency_body_read", "body_invalid"): (
        "body_coordinate",
        "head_h1",
        "observed_body",
        "target_resolution",
    ),
    ("execution_input_admission", "closure_mismatch"): (
        "execution_input_closure",
        "operation_request",
    ),
    ("execution_input_admission", "operation_admission_rejected"): (
        "execution_input_closure",
        "operation_request",
    ),
    ("reuse_validation", "reuse_not_current"): (
        "execution_input_closure",
        "package_reuse",
    ),
    ("package_execution", "operation_failed"): ("operation_request",),
    ("publication_reread", "publication_absent"): (
        "operation_request",
        "operation_result",
    ),
    ("publication_reread", "publication_mismatch"): (
        "operation_request",
        "operation_result",
        "package_result",
        "publication_receipt",
    ),
    ("session_fanout", "executed_session_append_failed"): (
        "package_result",
        "publication_receipt",
        "session_append_request",
        "session_source",
    ),
    ("session_fanout", "reused_session_append_failed"): (
        "package_reuse",
        "session_append_request",
        "session_source",
    ),
    ("session_fanout", "executed_session_event_reread_failed"): (
        "package_result",
        "publication_receipt",
        "session_append_request",
        "session_source",
    ),
    ("session_fanout", "reused_session_event_reread_failed"): (
        "package_reuse",
        "session_append_request",
        "session_source",
    ),
    ("session_fanout", "executed_session_receipt_failed"): (
        "package_result",
        "publication_receipt",
        "session_append_request",
        "session_event_positive",
        "session_source",
    ),
    ("session_fanout", "reused_session_receipt_failed"): (
        "package_reuse",
        "session_append_request",
        "session_event_positive",
        "session_source",
    ),
    ("session_fanout", "executed_session_fanout_mismatch"): (
        "package_result",
        "publication_receipt",
        "session_append_request",
        "session_event_positive",
        "session_fanout_receipt",
        "session_source",
    ),
    ("session_fanout", "reused_session_fanout_mismatch"): (
        "package_reuse",
        "session_append_request",
        "session_event_positive",
        "session_fanout_receipt",
        "session_source",
    ),
}
_INTERNAL_JSON_ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
)


def _digest(contract: str, payload: Mapping[str, object]) -> ContentDigest:
    value = (
        "sha256:"
        + hashlib.sha256(
            _INTERNAL_JSON_ENCODER.encode({"contract": contract, **payload}).encode(
                "utf-8"
            )
        ).hexdigest()
    )
    return _frozen_value(ContentDigest, value=value)


def _frozen_value[T](expected: type[T], **fields: object) -> T:
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _optional_token(value: object, path: str) -> str | None:
    return None if value is None else _token(value, path)


def _digest_tuple(
    value: object, path: str, *, nonempty: bool = False
) -> tuple[ContentDigest, ...]:
    values = _exact_tuple(value, ContentDigest, path)
    if nonempty and not values:
        raise ContractViolation(f"{path} must not be empty")
    wires = tuple(item.value.encode() for item in values)
    if wires != tuple(sorted(set(wires))):
        raise ContractViolation(f"{path} must be unique and digest ordered")
    return values


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPlannedDependencyInput:
    demand_digest: ContentDigest
    target_resolution_digest: ContentDigest
    required_result_role: str
    result_product_contract: SemanticContractRef
    planned_input_digest: ContentDigest

    @classmethod
    def create(cls, **values: object) -> WorkspaceSemanticPlannedDependencyInput:
        payload = _planned_input_payload(**values)
        return _frozen_value(
            cls,
            **values,
            planned_input_digest=_digest(
                WORKSPACE_SEMANTIC_PLANNED_DEPENDENCY_INPUT, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _planned_input_payload(
            demand_digest=self.demand_digest,
            target_resolution_digest=self.target_resolution_digest,
            required_result_role=self.required_result_role,
            result_product_contract=self.result_product_contract,
        )
        if _content_digest(
            self.planned_input_digest, "planned_input.digest"
        ) != _digest(WORKSPACE_SEMANTIC_PLANNED_DEPENDENCY_INPUT, payload):
            raise ContractViolation("planned dependency input digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_PLANNED_DEPENDENCY_INPUT,
            **_planned_input_payload(
                demand_digest=self.demand_digest,
                target_resolution_digest=self.target_resolution_digest,
                required_result_role=self.required_result_role,
                result_product_contract=self.result_product_contract,
            ),
            "planned_input_digest": self.planned_input_digest.to_wire(),
        }


def _planned_input_payload(**values: object) -> dict[str, object]:
    contract = _preflight_exact(
        values["result_product_contract"], SemanticContractRef, "planned_input.contract"
    )
    contract.__post_init__()
    return {
        "demand_digest": _content_digest(
            values["demand_digest"], "planned_input.demand_digest"
        ).to_wire(),
        "required_result_role": _token(
            values["required_result_role"], "planned_input.required_result_role"
        ),
        "result_product_contract": contract.to_wire(),
        "target_resolution_digest": _content_digest(
            values["target_resolution_digest"],
            "planned_input.target_resolution_digest",
        ).to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPlanningDemandClosure:
    consumer_package: SemanticPackageCoordinate
    planned_dependency_inputs: tuple[WorkspaceSemanticPlannedDependencyInput, ...]
    planning_demand_closure_digest: ContentDigest

    @classmethod
    def create(cls, **values: object) -> WorkspaceSemanticPlanningDemandClosure:
        payload = _planning_closure_payload(**values)
        return _frozen_value(
            cls,
            **values,
            planning_demand_closure_digest=_digest(
                WORKSPACE_SEMANTIC_PLANNING_DEMAND_CLOSURE, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _planning_closure_payload(
            consumer_package=self.consumer_package,
            planned_dependency_inputs=self.planned_dependency_inputs,
        )
        if _content_digest(
            self.planning_demand_closure_digest, "planning_closure.digest"
        ) != _digest(WORKSPACE_SEMANTIC_PLANNING_DEMAND_CLOSURE, payload):
            raise ContractViolation("planning demand closure digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_PLANNING_DEMAND_CLOSURE,
            **_planning_closure_payload(
                consumer_package=self.consumer_package,
                planned_dependency_inputs=self.planned_dependency_inputs,
            ),
            "planning_demand_closure_digest": self.planning_demand_closure_digest.to_wire(),
        }


def _planning_closure_payload(**values: object) -> dict[str, object]:
    package = _preflight_exact(
        values["consumer_package"],
        SemanticPackageCoordinate,
        "planning_closure.package",
    )
    package.__post_init__()
    inputs = _ordered_tuple(
        values["planned_dependency_inputs"],
        WorkspaceSemanticPlannedDependencyInput,
        "planning_closure.inputs",
    )
    demands = tuple(item.demand_digest for item in inputs)
    if demands != tuple(sorted(set(demands), key=lambda item: item.value)):
        raise ContractViolation("planned inputs must be demand-digest ordered")
    return {
        "consumer_package": package.to_wire(),
        "planned_dependency_inputs": [item.to_wire() for item in inputs],
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPackageHeadObservation:
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    profile_binding_digest: ContentDigest
    state: str
    predecessor_head_revision: int | None
    predecessor_head_digest: ContentDigest | None
    historical_execution_input_closure_digest: ContentDigest | None
    expected_post_revision: int
    expected_post_head_digest: ContentDigest | None
    observation_digest: ContentDigest
    stored_head_contract: str | None = None
    stored_package_occurrence: WorkspaceMaterializationPackageOccurrenceV4 | None = None

    @classmethod
    def create(cls, **values: object) -> WorkspaceSemanticPackageHeadObservation:
        values.setdefault("stored_head_contract", None)
        values.setdefault("stored_package_occurrence", None)
        payload = _head_observation_payload(**values)
        return _frozen_value(
            cls,
            **values,
            observation_digest=_digest(
                _head_observation_contract(values["stored_head_contract"]), payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _head_observation_payload(
            package=self.package,
            source_identity_digest=self.source_identity_digest,
            profile_binding_digest=self.profile_binding_digest,
            state=self.state,
            predecessor_head_revision=self.predecessor_head_revision,
            predecessor_head_digest=self.predecessor_head_digest,
            historical_execution_input_closure_digest=self.historical_execution_input_closure_digest,
            expected_post_revision=self.expected_post_revision,
            expected_post_head_digest=self.expected_post_head_digest,
            stored_head_contract=self.stored_head_contract,
            stored_package_occurrence=self.stored_package_occurrence,
        )
        if _content_digest(
            self.observation_digest, "head.observation_digest"
        ) != _digest(_head_observation_contract(self.stored_head_contract), payload):
            raise ContractViolation("head observation digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": _head_observation_contract(self.stored_head_contract),
            **_head_observation_payload(
                package=self.package,
                source_identity_digest=self.source_identity_digest,
                profile_binding_digest=self.profile_binding_digest,
                state=self.state,
                predecessor_head_revision=self.predecessor_head_revision,
                predecessor_head_digest=self.predecessor_head_digest,
                historical_execution_input_closure_digest=self.historical_execution_input_closure_digest,
                expected_post_revision=self.expected_post_revision,
                expected_post_head_digest=self.expected_post_head_digest,
                stored_head_contract=self.stored_head_contract,
                stored_package_occurrence=self.stored_package_occurrence,
            ),
            "observation_digest": self.observation_digest.to_wire(),
        }


def _optional_digest(value: object, path: str) -> ContentDigest | None:
    return None if value is None else _content_digest(value, path)


def _optional_revision(value: object, path: str) -> int | None:
    return None if value is None else _nonnegative(value, path)


def _head_observation_contract(stored_head_contract: object) -> str:
    if stored_head_contract is None:
        return WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION
    if (
        type(stored_head_contract) is not str
        or stored_head_contract != WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4
    ):
        raise ContractViolation("stored graph head contract unsupported")
    return WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION_V2


def _head_observation_payload(**values: object) -> dict[str, object]:
    stored_head_contract = values.get("stored_head_contract")
    _head_observation_contract(stored_head_contract)
    stored_package_occurrence = values.get("stored_package_occurrence")
    if stored_head_contract is None:
        if stored_package_occurrence is not None:
            raise ContractViolation("V1 graph head cannot carry a V4 occurrence")
    else:
        if type(stored_package_occurrence) is not WorkspaceMaterializationPackageOccurrenceV4:
            raise ContractViolation("V4 graph head requires its exact package occurrence")
        stored_package_occurrence.__post_init__()
    package = _preflight_exact(
        values["package"], SemanticPackageCoordinate, "head.package"
    )
    package.__post_init__()
    state = _token(values["state"], "head.state")
    if state not in WORKSPACE_OBSERVED_HEAD_CLASSIFICATIONS:
        raise ContractViolation("head state unsupported")
    if stored_head_contract is not None and state != "stale":
        raise ContractViolation("V4 graph head requires stale execution")
    predecessor_revision = _optional_revision(
        values["predecessor_head_revision"], "head.predecessor_revision"
    )
    predecessor_digest = _optional_digest(
        values["predecessor_head_digest"], "head.predecessor_digest"
    )
    historical = _optional_digest(
        values["historical_execution_input_closure_digest"], "head.historical_closure"
    )
    expected_revision = _nonnegative(
        values["expected_post_revision"], "head.expected_revision"
    )
    expected_digest = _optional_digest(
        values["expected_post_head_digest"], "head.expected_digest"
    )
    if state == "missing":
        if (
            predecessor_revision is not None
            or predecessor_digest is not None
            or historical is not None
        ):
            raise ContractViolation("missing head requires typed-empty predecessor")
        if expected_revision != 1 or expected_digest is not None:
            raise ContractViolation(
                "missing head must plan initial unresolved publication"
            )
    elif predecessor_revision is None or predecessor_digest is None:
        raise ContractViolation(
            "existing head requires predecessor revision and digest"
        )
    elif state == "current":
        if historical is None:
            raise ContractViolation("current head requires historical input closure")
        if (
            expected_revision != predecessor_revision
            or expected_digest != predecessor_digest
        ):
            raise ContractViolation("current head must preserve predecessor")
    elif expected_revision != predecessor_revision + 1 or expected_digest is not None:
        raise ContractViolation("stale head must plan one unresolved revision advance")
    payload: dict[str, object] = {
        "expected_post_head_digest": None
        if expected_digest is None
        else expected_digest.to_wire(),
        "expected_post_revision": expected_revision,
        "historical_execution_input_closure_digest": None
        if historical is None
        else historical.to_wire(),
        "package": package.to_wire(),
        "predecessor_head_digest": None
        if predecessor_digest is None
        else predecessor_digest.to_wire(),
        "predecessor_head_revision": predecessor_revision,
        "profile_binding_digest": _content_digest(
            values["profile_binding_digest"], "head.profile_binding_digest"
        ).to_wire(),
        "source_identity_digest": _content_digest(
            values["source_identity_digest"], "head.source_identity_digest"
        ).to_wire(),
        "state": state,
    }
    if stored_head_contract is not None:
        if (
            type(stored_package_occurrence)
            is not WorkspaceMaterializationPackageOccurrenceV4
        ):
            raise ContractViolation(
                "V4 graph head requires its exact package occurrence"
            )
        payload["stored_head_contract"] = stored_head_contract
        payload["stored_package_occurrence"] = stored_package_occurrence.to_wire()
    return payload


@dataclass(frozen=True, slots=True)
class WorkspaceDependencyTargetResolution:
    demand_digest: ContentDigest
    target_package_entry_digest: ContentDigest
    target_local_code_match_digest: ContentDigest
    composed_target_intent_digest: ContentDigest
    participation_policy_digest: ContentDigest
    required_result_role: str
    result_product_contract: SemanticContractRef
    head_observation: WorkspaceSemanticPackageHeadObservation
    resolution_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        demand_digest: ContentDigest,
        target_package_entry_digest: ContentDigest,
        target_local_code_match_digest: ContentDigest,
        composed_target_intent_digest: ContentDigest,
        participation_policy_digest: ContentDigest,
        required_result_role: str,
        result_product_contract: SemanticContractRef,
        head_observation: WorkspaceSemanticPackageHeadObservation,
    ) -> WorkspaceDependencyTargetResolution:
        for value, path in (
            (demand_digest, "target.demand_digest"),
            (target_package_entry_digest, "target.target_package_entry_digest"),
            (target_local_code_match_digest, "target.target_local_code_match_digest"),
            (composed_target_intent_digest, "target.composed_target_intent_digest"),
            (participation_policy_digest, "target.participation_policy_digest"),
        ):
            _preflight_exact(value, ContentDigest, path)
        payload = _target_resolution_payload(
            demand_digest=demand_digest,
            target_package_entry_digest=target_package_entry_digest,
            target_local_code_match_digest=target_local_code_match_digest,
            composed_target_intent_digest=composed_target_intent_digest,
            participation_policy_digest=participation_policy_digest,
            required_result_role=required_result_role,
            result_product_contract=result_product_contract,
            head_observation=head_observation,
        )
        return cls(
            demand_digest=demand_digest,
            target_package_entry_digest=target_package_entry_digest,
            target_local_code_match_digest=target_local_code_match_digest,
            composed_target_intent_digest=composed_target_intent_digest,
            participation_policy_digest=participation_policy_digest,
            required_result_role=required_result_role,
            result_product_contract=result_product_contract,
            head_observation=head_observation,
            resolution_digest=_digest(WORKSPACE_DEPENDENCY_TARGET_RESOLUTION, payload),
        )

    def __post_init__(self) -> None:
        payload = _target_resolution_payload(
            demand_digest=self.demand_digest,
            target_package_entry_digest=self.target_package_entry_digest,
            target_local_code_match_digest=self.target_local_code_match_digest,
            composed_target_intent_digest=self.composed_target_intent_digest,
            participation_policy_digest=self.participation_policy_digest,
            required_result_role=self.required_result_role,
            result_product_contract=self.result_product_contract,
            head_observation=self.head_observation,
        )
        if _content_digest(
            self.resolution_digest, "target.resolution_digest"
        ) != _digest(WORKSPACE_DEPENDENCY_TARGET_RESOLUTION, payload):
            raise ContractViolation("target resolution digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_DEPENDENCY_TARGET_RESOLUTION,
            **_target_resolution_payload(
                demand_digest=self.demand_digest,
                target_package_entry_digest=self.target_package_entry_digest,
                target_local_code_match_digest=self.target_local_code_match_digest,
                composed_target_intent_digest=self.composed_target_intent_digest,
                participation_policy_digest=self.participation_policy_digest,
                required_result_role=self.required_result_role,
                result_product_contract=self.result_product_contract,
                head_observation=self.head_observation,
            ),
            "resolution_digest": self.resolution_digest.to_wire(),
        }


def _target_resolution_payload(**values: object) -> dict[str, object]:
    result_contract = _preflight_exact(
        values["result_product_contract"], SemanticContractRef, "target.result_contract"
    )
    head = _preflight_exact(
        values["head_observation"],
        WorkspaceSemanticPackageHeadObservation,
        "target.head",
    )
    result_contract.__post_init__()
    head.__post_init__()
    return {
        "composed_target_intent_digest": _content_digest(
            values["composed_target_intent_digest"],
            "target.composed_target_intent_digest",
        ).to_wire(),
        "demand_digest": _content_digest(
            values["demand_digest"], "target.demand_digest"
        ).to_wire(),
        "head_observation": head.to_wire(),
        "participation_policy_digest": _content_digest(
            values["participation_policy_digest"], "target.participation_policy_digest"
        ).to_wire(),
        "required_result_role": _token(
            values["required_result_role"], "target.required_result_role"
        ),
        "result_product_contract": result_contract.to_wire(),
        "target_local_code_match_digest": _content_digest(
            values["target_local_code_match_digest"],
            "target.target_local_code_match_digest",
        ).to_wire(),
        "target_package_entry_digest": _content_digest(
            values["target_package_entry_digest"], "target.target_package_entry_digest"
        ).to_wire(),
    }


def _create_planner_target_resolution(
    *,
    demand_digest: ContentDigest,
    target_package_entry_digest: ContentDigest,
    target_local_code_match_digest: ContentDigest,
    composed_target_intent_digest: ContentDigest,
    participation_policy_digest: ContentDigest,
    required_result_role: str,
    result_product_contract: SemanticContractRef,
    head_observation: WorkspaceSemanticPackageHeadObservation,
    head_observation_wire: dict[str, object],
) -> tuple[WorkspaceDependencyTargetResolution, bytes]:
    for value, path in (
        (demand_digest, "target.demand_digest"),
        (target_package_entry_digest, "target.target_package_entry_digest"),
        (target_local_code_match_digest, "target.target_local_code_match_digest"),
        (composed_target_intent_digest, "target.composed_target_intent_digest"),
        (participation_policy_digest, "target.participation_policy_digest"),
    ):
        _preflight_exact(value, ContentDigest, path)
    contract = _preflight_exact(
        result_product_contract, SemanticContractRef, "target.result_contract"
    )
    head = _preflight_exact(
        head_observation, WorkspaceSemanticPackageHeadObservation, "target.head"
    )
    if (
        type(head_observation_wire) is not dict
        or head_observation_wire.get("contract")
        != _head_observation_contract(head.stored_head_contract)
        or head_observation_wire.get("observation_digest")
        != head.observation_digest.to_wire()
    ):
        raise ContractViolation("planner target head wire differs")
    payload = {
        "composed_target_intent_digest": composed_target_intent_digest.to_wire(),
        "demand_digest": demand_digest.to_wire(),
        "head_observation": head_observation_wire,
        "participation_policy_digest": participation_policy_digest.to_wire(),
        "required_result_role": _token(
            required_result_role, "target.required_result_role"
        ),
        "result_product_contract": contract.to_wire(),
        "target_local_code_match_digest": target_local_code_match_digest.to_wire(),
        "target_package_entry_digest": target_package_entry_digest.to_wire(),
    }
    resolution_digest = _digest(WORKSPACE_DEPENDENCY_TARGET_RESOLUTION, payload)
    result = _frozen_value(
        WorkspaceDependencyTargetResolution,
        demand_digest=demand_digest,
        target_package_entry_digest=target_package_entry_digest,
        target_local_code_match_digest=target_local_code_match_digest,
        composed_target_intent_digest=composed_target_intent_digest,
        participation_policy_digest=participation_policy_digest,
        required_result_role=required_result_role,
        result_product_contract=contract,
        head_observation=head,
        resolution_digest=resolution_digest,
    )
    wire = _INTERNAL_JSON_ENCODER.encode(
        {
            "contract": WORKSPACE_DEPENDENCY_TARGET_RESOLUTION,
            **payload,
            "resolution_digest": resolution_digest.value,
        }
    ).encode("utf-8")
    return result, wire


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraphNode:
    package: SemanticPackageCoordinate
    package_entry_digest: ContentDigest
    participation_policy_digest: ContentDigest
    source_identity_digest: ContentDigest
    local_code_match_digest: ContentDigest
    composed_intent_digest: ContentDigest
    demand_set_digest: ContentDigest
    planning_demand_closure_digest: ContentDigest
    head_observation: WorkspaceSemanticPackageHeadObservation
    node_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        package: SemanticPackageCoordinate,
        package_entry_digest: ContentDigest,
        participation_policy_digest: ContentDigest,
        source_identity_digest: ContentDigest,
        local_code_match_digest: ContentDigest,
        composed_intent_digest: ContentDigest,
        demand_set_digest: ContentDigest,
        planning_demand_closure_digest: ContentDigest,
        head_observation: WorkspaceSemanticPackageHeadObservation,
    ) -> WorkspaceSemanticMaterializationGraphNode:
        for value, path in (
            (
                package_entry_digest,
                "node.package_entry_digest",
            ),
            (participation_policy_digest, "node.participation_policy_digest"),
            (source_identity_digest, "node.source_identity_digest"),
            (local_code_match_digest, "node.local_code_match_digest"),
            (composed_intent_digest, "node.composed_intent_digest"),
            (demand_set_digest, "node.demand_set_digest"),
            (planning_demand_closure_digest, "node.planning_demand_closure_digest"),
        ):
            _preflight_exact(value, ContentDigest, path)
        payload = _node_payload(
            package=package,
            package_entry_digest=package_entry_digest,
            participation_policy_digest=participation_policy_digest,
            source_identity_digest=source_identity_digest,
            local_code_match_digest=local_code_match_digest,
            composed_intent_digest=composed_intent_digest,
            demand_set_digest=demand_set_digest,
            planning_demand_closure_digest=planning_demand_closure_digest,
            head_observation=head_observation,
        )
        return cls(
            package=package,
            package_entry_digest=package_entry_digest,
            participation_policy_digest=participation_policy_digest,
            source_identity_digest=source_identity_digest,
            local_code_match_digest=local_code_match_digest,
            composed_intent_digest=composed_intent_digest,
            demand_set_digest=demand_set_digest,
            planning_demand_closure_digest=planning_demand_closure_digest,
            head_observation=head_observation,
            node_digest=_digest(WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE, payload),
        )

    def __post_init__(self) -> None:
        payload = _node_payload(
            package=self.package,
            package_entry_digest=self.package_entry_digest,
            participation_policy_digest=self.participation_policy_digest,
            source_identity_digest=self.source_identity_digest,
            local_code_match_digest=self.local_code_match_digest,
            composed_intent_digest=self.composed_intent_digest,
            demand_set_digest=self.demand_set_digest,
            planning_demand_closure_digest=self.planning_demand_closure_digest,
            head_observation=self.head_observation,
        )
        if _content_digest(self.node_digest, "node.node_digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE, payload
        ):
            raise ContractViolation("graph node digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE,
            **_node_payload(
                package=self.package,
                package_entry_digest=self.package_entry_digest,
                participation_policy_digest=self.participation_policy_digest,
                source_identity_digest=self.source_identity_digest,
                local_code_match_digest=self.local_code_match_digest,
                composed_intent_digest=self.composed_intent_digest,
                demand_set_digest=self.demand_set_digest,
                planning_demand_closure_digest=self.planning_demand_closure_digest,
                head_observation=self.head_observation,
            ),
            "node_digest": self.node_digest.to_wire(),
        }


def _node_payload(**values: object) -> dict[str, object]:
    package = _preflight_exact(
        values["package"], SemanticPackageCoordinate, "node.package"
    )
    head = _preflight_exact(
        values["head_observation"], WorkspaceSemanticPackageHeadObservation, "node.head"
    )
    package.__post_init__()
    head.__post_init__()
    if head.package != package:
        raise ContractViolation("node head package differs")
    return {
        "composed_intent_digest": _content_digest(
            values["composed_intent_digest"], "node.composed_intent_digest"
        ).to_wire(),
        "demand_set_digest": _content_digest(
            values["demand_set_digest"], "node.demand_set_digest"
        ).to_wire(),
        "head_observation": head.to_wire(),
        "local_code_match_digest": _content_digest(
            values["local_code_match_digest"], "node.local_code_match_digest"
        ).to_wire(),
        "package": package.to_wire(),
        "package_entry_digest": _content_digest(
            values["package_entry_digest"], "node.package_entry_digest"
        ).to_wire(),
        "participation_policy_digest": _content_digest(
            values["participation_policy_digest"], "node.participation_policy_digest"
        ).to_wire(),
        "planning_demand_closure_digest": _content_digest(
            values["planning_demand_closure_digest"],
            "node.planning_demand_closure_digest",
        ).to_wire(),
        "source_identity_digest": _content_digest(
            values["source_identity_digest"], "node.source_identity_digest"
        ).to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraphEdge:
    consumer_node_digest: ContentDigest
    target_node_digest: ContentDigest
    demand_digest: ContentDigest
    target_resolution_digest: ContentDigest
    edge_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        consumer_node_digest: ContentDigest,
        target_node_digest: ContentDigest,
        demand_digest: ContentDigest,
        target_resolution_digest: ContentDigest,
    ) -> WorkspaceSemanticMaterializationGraphEdge:
        for value, path in (
            (consumer_node_digest, "edge.consumer_node_digest"),
            (target_node_digest, "edge.target_node_digest"),
            (demand_digest, "edge.demand_digest"),
            (target_resolution_digest, "edge.target_resolution_digest"),
        ):
            _preflight_exact(value, ContentDigest, path)
        payload = _edge_payload(
            consumer_node_digest=consumer_node_digest,
            target_node_digest=target_node_digest,
            demand_digest=demand_digest,
            target_resolution_digest=target_resolution_digest,
        )
        return cls(
            consumer_node_digest=consumer_node_digest,
            target_node_digest=target_node_digest,
            demand_digest=demand_digest,
            target_resolution_digest=target_resolution_digest,
            edge_digest=_digest(WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EDGE, payload),
        )

    def __post_init__(self) -> None:
        payload = _edge_payload(
            consumer_node_digest=self.consumer_node_digest,
            target_node_digest=self.target_node_digest,
            demand_digest=self.demand_digest,
            target_resolution_digest=self.target_resolution_digest,
        )
        if _content_digest(self.edge_digest, "edge.edge_digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EDGE, payload
        ):
            raise ContractViolation("graph edge digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EDGE,
            **_edge_payload(
                consumer_node_digest=self.consumer_node_digest,
                target_node_digest=self.target_node_digest,
                demand_digest=self.demand_digest,
                target_resolution_digest=self.target_resolution_digest,
            ),
            "edge_digest": self.edge_digest.to_wire(),
        }


def _edge_payload(**values: object) -> dict[str, object]:
    return {
        "consumer_node_digest": _content_digest(
            values["consumer_node_digest"], "edge.consumer_node_digest"
        ).to_wire(),
        "demand_digest": _content_digest(
            values["demand_digest"], "edge.demand_digest"
        ).to_wire(),
        "target_node_digest": _content_digest(
            values["target_node_digest"], "edge.target_node_digest"
        ).to_wire(),
        "target_resolution_digest": _content_digest(
            values["target_resolution_digest"], "edge.target_resolution_digest"
        ).to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationLocalRootAssociation:
    package_entry_digest: ContentDigest
    participation_policy_digest: ContentDigest
    code_intent_digest: ContentDigest
    required_result_product_digests: tuple[ContentDigest, ...]
    node_digest: ContentDigest
    association_digest: ContentDigest

    @classmethod
    def create(
        cls, **values: object
    ) -> WorkspaceSemanticMaterializationLocalRootAssociation:
        payload = _local_root_payload(**values)
        return _frozen_value(
            cls,
            **values,
            association_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_LOCAL_ROOT_ASSOCIATION, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _local_root_payload(
            package_entry_digest=self.package_entry_digest,
            participation_policy_digest=self.participation_policy_digest,
            code_intent_digest=self.code_intent_digest,
            required_result_product_digests=self.required_result_product_digests,
            node_digest=self.node_digest,
        )
        if _content_digest(
            self.association_digest, "root.association_digest"
        ) != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_LOCAL_ROOT_ASSOCIATION, payload
        ):
            raise ContractViolation("local root association digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_LOCAL_ROOT_ASSOCIATION,
            **_local_root_payload(
                package_entry_digest=self.package_entry_digest,
                participation_policy_digest=self.participation_policy_digest,
                code_intent_digest=self.code_intent_digest,
                required_result_product_digests=self.required_result_product_digests,
                node_digest=self.node_digest,
            ),
            "association_digest": self.association_digest.to_wire(),
        }


def _local_root_payload(**values: object) -> dict[str, object]:
    return {
        "code_intent_digest": _content_digest(
            values["code_intent_digest"], "root.code_intent_digest"
        ).to_wire(),
        "node_digest": _content_digest(
            values["node_digest"], "root.node_digest"
        ).to_wire(),
        "package_entry_digest": _content_digest(
            values["package_entry_digest"], "root.package_entry_digest"
        ).to_wire(),
        "participation_policy_digest": _content_digest(
            values["participation_policy_digest"], "root.participation_policy_digest"
        ).to_wire(),
        "required_result_product_digests": [
            item.to_wire()
            for item in _digest_tuple(
                values["required_result_product_digests"],
                "root.required_result_product_digests",
                nonempty=True,
            )
        ],
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraph:
    local_root_association_digests: tuple[ContentDigest, ...]
    nodes: tuple[WorkspaceSemanticMaterializationGraphNode, ...]
    edges: tuple[WorkspaceSemanticMaterializationGraphEdge, ...]
    topological_layers: tuple[tuple[ContentDigest, ...], ...]
    graph_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        local_root_associations: tuple[
            WorkspaceSemanticMaterializationLocalRootAssociation, ...
        ],
        nodes: tuple[WorkspaceSemanticMaterializationGraphNode, ...],
        edges: tuple[WorkspaceSemanticMaterializationGraphEdge, ...],
    ) -> WorkspaceSemanticMaterializationGraph:
        _preflight_tuple(
            local_root_associations,
            WorkspaceSemanticMaterializationLocalRootAssociation,
            "graph.local_root_associations",
        )
        _preflight_tuple(
            nodes, WorkspaceSemanticMaterializationGraphNode, "graph.nodes"
        )
        _preflight_tuple(
            edges, WorkspaceSemanticMaterializationGraphEdge, "graph.edges"
        )
        associations = tuple(
            association.association_digest for association in local_root_associations
        )
        layers = _derive_layers(nodes=nodes, edges=edges)
        payload = _graph_payload(
            local_root_association_digests=associations,
            nodes=nodes,
            edges=edges,
            topological_layers=layers,
        )
        result = object.__new__(cls)
        object.__setattr__(result, "local_root_association_digests", associations)
        object.__setattr__(result, "nodes", nodes)
        object.__setattr__(result, "edges", edges)
        object.__setattr__(result, "topological_layers", layers)
        object.__setattr__(
            result,
            "graph_digest",
            _digest(WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH, payload),
        )
        _validate_graph_local_associations(result, local_root_associations)
        return result

    def __post_init__(self) -> None:
        expected_layers = _derive_layers(nodes=self.nodes, edges=self.edges)
        if self.topological_layers != expected_layers:
            raise ContractViolation("graph topological layers differ")
        payload = _graph_payload(
            local_root_association_digests=self.local_root_association_digests,
            nodes=self.nodes,
            edges=self.edges,
            topological_layers=self.topological_layers,
        )
        if _content_digest(self.graph_digest, "graph.graph_digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH, payload
        ):
            raise ContractViolation("graph digest mismatched")

    def validate_local_root_context(
        self,
        local_root_associations: tuple[
            WorkspaceSemanticMaterializationLocalRootAssociation, ...
        ],
    ) -> None:
        _validate_graph_local_associations(self, local_root_associations)

    def to_wire(self) -> dict[str, object]:
        expected_layers = _derive_layers(nodes=self.nodes, edges=self.edges)
        if self.topological_layers != expected_layers:
            raise ContractViolation("graph topological layers differ")
        payload = _graph_payload(
            local_root_association_digests=self.local_root_association_digests,
            nodes=self.nodes,
            edges=self.edges,
            topological_layers=self.topological_layers,
        )
        if _content_digest(self.graph_digest, "graph.graph_digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH, payload
        ):
            raise ContractViolation("graph digest mismatched")
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH,
            **payload,
            "graph_digest": self.graph_digest.to_wire(),
        }


def _validate_graph_local_associations(
    graph: WorkspaceSemanticMaterializationGraph,
    associations: tuple[WorkspaceSemanticMaterializationLocalRootAssociation, ...],
) -> None:
    values = _ordered_tuple(
        associations,
        WorkspaceSemanticMaterializationLocalRootAssociation,
        "graph.local_root_associations",
    )
    if graph.local_root_association_digests != tuple(
        item.association_digest for item in values
    ):
        raise ContractViolation("graph differs from local root context")
    nodes_by_digest = {node.node_digest: node for node in graph.nodes}
    for association in associations:
        node = nodes_by_digest.get(association.node_digest)
        if (
            node is None
            or node.package_entry_digest != association.package_entry_digest
        ):
            raise ContractViolation("graph root association differs from node")


def _graph_payload(**values: object) -> dict[str, object]:
    nodes = _ordered_tuple(
        values["nodes"], WorkspaceSemanticMaterializationGraphNode, "graph.nodes"
    )
    if not nodes:
        raise ContractViolation("graph nodes must not be empty")
    edges = _ordered_tuple(
        values["edges"], WorkspaceSemanticMaterializationGraphEdge, "graph.edges"
    )
    association_digests = _digest_tuple(
        values["local_root_association_digests"],
        "graph.local_root_association_digests",
    )
    layers = _layers(values["topological_layers"])
    return {
        "edges": [item.to_wire() for item in edges],
        "local_root_association_digests": [
            item.to_wire() for item in association_digests
        ],
        "nodes": [item.to_wire() for item in nodes],
        "topological_layers": [[item.to_wire() for item in layer] for layer in layers],
    }


def _derive_layers(
    *,
    nodes: object,
    edges: object,
) -> tuple[tuple[ContentDigest, ...], ...]:
    node_values = _ordered_tuple(
        nodes, WorkspaceSemanticMaterializationGraphNode, "graph.nodes"
    )
    edge_values = _ordered_tuple(
        edges, WorkspaceSemanticMaterializationGraphEdge, "graph.edges"
    )
    node_digests = {node.node_digest for node in node_values}
    indegree = {digest: 0 for digest in node_digests}
    consumers: dict[ContentDigest, set[ContentDigest]] = {
        digest: set() for digest in node_digests
    }
    for edge in edge_values:
        if (
            edge.consumer_node_digest not in node_digests
            or edge.target_node_digest not in node_digests
        ):
            raise ContractViolation("graph edge endpoint absent")
        if edge.consumer_node_digest == edge.target_node_digest:
            raise ContractViolation("graph self edge unsupported")
        if edge.consumer_node_digest not in consumers[edge.target_node_digest]:
            consumers[edge.target_node_digest].add(edge.consumer_node_digest)
            indegree[edge.consumer_node_digest] += 1
    remaining = set(node_digests)
    layers: list[tuple[ContentDigest, ...]] = []
    while remaining:
        layer = tuple(
            sorted(
                (digest for digest in remaining if indegree[digest] == 0),
                key=lambda item: item.value.encode(),
            )
        )
        if not layer:
            raise ContractViolation("graph contains active cycle")
        layers.append(layer)
        for target in layer:
            remaining.remove(target)
            for consumer in consumers[target]:
                indegree[consumer] -= 1
    return tuple(layers)


def _create_planner_graph(
    *,
    local_root_associations: tuple[
        WorkspaceSemanticMaterializationLocalRootAssociation, ...
    ],
    local_root_association_wires: tuple[dict[str, object], ...],
    local_root_association_wire_bytes: tuple[bytes, ...],
    nodes: tuple[WorkspaceSemanticMaterializationGraphNode, ...],
    node_wires: tuple[dict[str, object], ...],
    node_wire_bytes: tuple[bytes, ...],
    edges: tuple[WorkspaceSemanticMaterializationGraphEdge, ...],
    edge_wires: tuple[dict[str, object], ...],
    edge_wire_bytes: tuple[bytes, ...],
) -> WorkspaceSemanticMaterializationGraph:
    """Create a graph from exact values freshly issued by the resident planner.

    The public ``WorkspaceSemanticMaterializationGraph.create`` entrance remains the
    strict context-independent factory. The planner has already constructed every
    nested value through that value's public factory, so this module-private entrance
    validates each nested value and its canonical ordering exactly once instead of
    recursively repeating the same work while deriving layers and the aggregate.
    """

    associations = _preflight_tuple(
        local_root_associations,
        WorkspaceSemanticMaterializationLocalRootAssociation,
        "graph.local_root_associations",
    )
    node_values = _preflight_tuple(
        nodes, WorkspaceSemanticMaterializationGraphNode, "graph.nodes"
    )
    edge_values = _preflight_tuple(
        edges, WorkspaceSemanticMaterializationGraphEdge, "graph.edges"
    )
    if not node_values:
        raise ContractViolation("graph nodes must not be empty")

    if type(local_root_association_wires) is not tuple or len(
        local_root_association_wires
    ) != len(associations):
        raise TypeError("planner root association wires must align")
    if type(edge_wires) is not tuple or len(edge_wires) != len(edge_values):
        raise TypeError("planner edge wires must align")
    associations, _association_wires, _association_wire_bytes = _planner_ordered_values(
        associations,
        local_root_association_wires,
        local_root_association_wire_bytes,
        "graph.local_root_associations",
    )
    if type(node_wires) is not tuple or len(node_wires) != len(node_values):
        raise TypeError("planner graph node wires must align with nodes")
    for node, wire in zip(node_values, node_wires, strict=True):
        if (
            type(wire) is not dict
            or wire.get("contract") != WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE
            or wire.get("node_digest") != node.node_digest.to_wire()
        ):
            raise ContractViolation("planner graph node wire differs from node")
    node_values, node_wires, node_wire_bytes = _planner_ordered_values(
        node_values,
        node_wires,
        node_wire_bytes,
        "graph.nodes",
    )
    edge_values, edge_wires, edge_wire_bytes = _planner_ordered_values(
        edge_values,
        edge_wires,
        edge_wire_bytes,
        "graph.edges",
    )

    layers = _derive_layers_from_exact(nodes=node_values, edges=edge_values)
    association_digests = tuple(item.association_digest for item in associations)
    association_digest_bytes = _INTERNAL_JSON_ENCODER.encode(
        [item.to_wire() for item in association_digests]
    ).encode("utf-8")
    layer_bytes = _INTERNAL_JSON_ENCODER.encode(
        [[item.to_wire() for item in layer] for layer in layers]
    ).encode("utf-8")
    graph_body = (
        b'{"contract":'
        + _INTERNAL_JSON_ENCODER.encode(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH
        ).encode("utf-8")
        + b',"edges":['
        + b",".join(edge_wire_bytes)
        + b'],"local_root_association_digests":'
        + association_digest_bytes
        + b',"nodes":['
        + b",".join(node_wire_bytes)
        + b'],"topological_layers":'
        + layer_bytes
        + b"}"
    )
    graph = _frozen_value(
        WorkspaceSemanticMaterializationGraph,
        local_root_association_digests=association_digests,
        nodes=node_values,
        edges=edge_values,
        topological_layers=layers,
        graph_digest=_frozen_value(
            ContentDigest,
            value="sha256:" + hashlib.sha256(graph_body).hexdigest(),
        ),
    )
    nodes_by_digest = {node.node_digest: node for node in node_values}
    for association in associations:
        node = nodes_by_digest.get(association.node_digest)
        if (
            node is None
            or node.package_entry_digest != association.package_entry_digest
        ):
            raise ContractViolation("graph root association differs from node")
    return graph


def _create_planner_graph_edge(
    *,
    consumer_node_digest: ContentDigest,
    target_node_digest: ContentDigest,
    demand_digest: ContentDigest,
    target_resolution_digest: ContentDigest,
) -> tuple[WorkspaceSemanticMaterializationGraphEdge, dict[str, object], bytes]:
    payload = _edge_payload(
        consumer_node_digest=consumer_node_digest,
        target_node_digest=target_node_digest,
        demand_digest=demand_digest,
        target_resolution_digest=target_resolution_digest,
    )
    edge_digest = _digest(WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EDGE, payload)
    edge = _frozen_value(
        WorkspaceSemanticMaterializationGraphEdge,
        consumer_node_digest=consumer_node_digest,
        target_node_digest=target_node_digest,
        demand_digest=demand_digest,
        target_resolution_digest=target_resolution_digest,
        edge_digest=edge_digest,
    )
    wire: dict[str, object] = {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EDGE,
        **payload,
        "edge_digest": edge_digest.to_wire(),
    }
    return edge, wire, _INTERNAL_JSON_ENCODER.encode(wire).encode("utf-8")


def _create_planner_local_root_association(
    *,
    package_entry_digest: ContentDigest,
    participation_policy_digest: ContentDigest,
    code_intent_digest: ContentDigest,
    required_result_product_digests: tuple[ContentDigest, ...],
    node_digest: ContentDigest,
) -> tuple[
    WorkspaceSemanticMaterializationLocalRootAssociation,
    dict[str, object],
    bytes,
]:
    payload = _local_root_payload(
        package_entry_digest=package_entry_digest,
        participation_policy_digest=participation_policy_digest,
        code_intent_digest=code_intent_digest,
        required_result_product_digests=required_result_product_digests,
        node_digest=node_digest,
    )
    association_digest = _digest(
        WORKSPACE_SEMANTIC_MATERIALIZATION_LOCAL_ROOT_ASSOCIATION, payload
    )
    association = _frozen_value(
        WorkspaceSemanticMaterializationLocalRootAssociation,
        package_entry_digest=package_entry_digest,
        participation_policy_digest=participation_policy_digest,
        code_intent_digest=code_intent_digest,
        required_result_product_digests=required_result_product_digests,
        node_digest=node_digest,
        association_digest=association_digest,
    )
    wire: dict[str, object] = {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_LOCAL_ROOT_ASSOCIATION,
        **payload,
        "association_digest": association_digest.to_wire(),
    }
    return association, wire, _INTERNAL_JSON_ENCODER.encode(wire).encode("utf-8")


def _create_planner_graph_node(
    *,
    package: SemanticPackageCoordinate,
    package_entry_digest: ContentDigest,
    participation_policy_digest: ContentDigest,
    source_identity_digest: ContentDigest,
    local_code_match_digest: ContentDigest,
    composed_intent_digest: ContentDigest,
    demand_set_digest: ContentDigest,
    planning_demand_closure_digest: ContentDigest,
    head_observation: WorkspaceSemanticPackageHeadObservation,
    head_observation_wire: dict[str, object],
) -> tuple[WorkspaceSemanticMaterializationGraphNode, dict[str, object], bytes]:
    package_value = _preflight_exact(package, SemanticPackageCoordinate, "node.package")
    head = _preflight_exact(
        head_observation, WorkspaceSemanticPackageHeadObservation, "node.head"
    )
    for value, path in (
        (package_entry_digest, "node.package_entry_digest"),
        (participation_policy_digest, "node.participation_policy_digest"),
        (source_identity_digest, "node.source_identity_digest"),
        (local_code_match_digest, "node.local_code_match_digest"),
        (composed_intent_digest, "node.composed_intent_digest"),
        (demand_set_digest, "node.demand_set_digest"),
        (planning_demand_closure_digest, "node.planning_demand_closure_digest"),
    ):
        _preflight_exact(value, ContentDigest, path)
    if type(head_observation_wire) is not dict:
        raise TypeError("planner head observation wire must be exact dict")
    if (
        head.package != package_value
        or head_observation_wire.get("contract")
        != _head_observation_contract(head.stored_head_contract)
        or head_observation_wire.get("observation_digest")
        != head.observation_digest.to_wire()
    ):
        raise ContractViolation("planner head observation differs from node package")
    payload = {
        "composed_intent_digest": composed_intent_digest.to_wire(),
        "demand_set_digest": demand_set_digest.to_wire(),
        "head_observation": head_observation_wire,
        "local_code_match_digest": local_code_match_digest.to_wire(),
        "package": package_value.to_wire(),
        "package_entry_digest": package_entry_digest.to_wire(),
        "participation_policy_digest": participation_policy_digest.to_wire(),
        "planning_demand_closure_digest": planning_demand_closure_digest.to_wire(),
        "source_identity_digest": source_identity_digest.to_wire(),
    }
    node_digest = _digest(WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE, payload)
    node = _frozen_value(
        WorkspaceSemanticMaterializationGraphNode,
        package=package_value,
        package_entry_digest=package_entry_digest,
        participation_policy_digest=participation_policy_digest,
        source_identity_digest=source_identity_digest,
        local_code_match_digest=local_code_match_digest,
        composed_intent_digest=composed_intent_digest,
        demand_set_digest=demand_set_digest,
        planning_demand_closure_digest=planning_demand_closure_digest,
        head_observation=head,
        node_digest=node_digest,
    )
    wire: dict[str, object] = {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE,
        **payload,
        "node_digest": node_digest.to_wire(),
    }
    return node, wire, _INTERNAL_JSON_ENCODER.encode(wire).encode("utf-8")


def _planner_ordered_values[T](
    values: tuple[T, ...],
    wires: tuple[dict[str, object], ...],
    wire_bytes: tuple[bytes, ...],
    path: str,
) -> tuple[tuple[T, ...], tuple[dict[str, object], ...], tuple[bytes, ...]]:
    if type(wire_bytes) is not tuple or len(wire_bytes) != len(values):
        raise TypeError(f"{path} planner wire bytes must align")
    if any(type(item) is not bytes for item in wire_bytes):
        raise TypeError(f"{path} planner wire bytes must be exact bytes")
    pairs = sorted(
        zip(wire_bytes, values, wires, strict=True),
        key=lambda item: item[0],
    )
    encoded = tuple(item[0] for item in pairs)
    if len(encoded) != len(set(encoded)):
        raise ContractViolation(f"{path} must be unique")
    return (
        tuple(item[1] for item in pairs),
        tuple(item[2] for item in pairs),
        encoded,
    )


def _derive_layers_from_exact(
    *,
    nodes: tuple[WorkspaceSemanticMaterializationGraphNode, ...],
    edges: tuple[WorkspaceSemanticMaterializationGraphEdge, ...],
) -> tuple[tuple[ContentDigest, ...], ...]:
    node_digests = {node.node_digest for node in nodes}
    indegree = {digest: 0 for digest in node_digests}
    consumers: dict[ContentDigest, set[ContentDigest]] = {
        digest: set() for digest in node_digests
    }
    for edge in edges:
        if (
            edge.consumer_node_digest not in node_digests
            or edge.target_node_digest not in node_digests
        ):
            raise ContractViolation("graph edge endpoint absent")
        if edge.consumer_node_digest == edge.target_node_digest:
            raise ContractViolation("graph self edge unsupported")
        if edge.consumer_node_digest not in consumers[edge.target_node_digest]:
            consumers[edge.target_node_digest].add(edge.consumer_node_digest)
            indegree[edge.consumer_node_digest] += 1
    remaining = set(node_digests)
    layers: list[tuple[ContentDigest, ...]] = []
    while remaining:
        layer = tuple(
            sorted(
                (digest for digest in remaining if indegree[digest] == 0),
                key=lambda item: item.value.encode(),
            )
        )
        if not layer:
            raise ContractViolation("graph contains active cycle")
        layers.append(layer)
        for target in layer:
            remaining.remove(target)
            for consumer in consumers[target]:
                indegree[consumer] -= 1
    return tuple(layers)


def _layers(value: object) -> tuple[tuple[ContentDigest, ...], ...]:
    if type(value) is not tuple:
        raise TypeError("graph.topological_layers must be exact tuple")
    raw_layers = cast(tuple[object, ...], value)
    layers = tuple(
        _digest_tuple(layer, f"graph.topological_layers[{index}]", nonempty=True)
        for index, layer in enumerate(raw_layers)
    )
    flat = tuple(item for layer in layers for item in layer)
    if len(flat) != len(set(flat)):
        raise ContractViolation("graph layers repeat nodes")
    return layers


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraphPlanAdmission:
    selection_resolution_digest: ContentDigest
    workspace_catalog_ref: str
    workspace_catalog_generation: int
    workspace_catalog_root_digest: ContentDigest
    code_catalog_ref: str
    code_catalog_generation: int
    code_catalog_root_digest: ContentDigest
    code_catalog_match_admission_digests: tuple[ContentDigest, ...]
    graph_digest: ContentDigest
    admission_digest: ContentDigest

    @classmethod
    def create(
        cls, **values: object
    ) -> WorkspaceSemanticMaterializationGraphPlanAdmission:
        payload = _graph_plan_admission_payload(**values)
        return _frozen_value(
            cls,
            **values,
            admission_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_ADMISSION, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _graph_plan_admission_payload(
            selection_resolution_digest=self.selection_resolution_digest,
            workspace_catalog_ref=self.workspace_catalog_ref,
            workspace_catalog_generation=self.workspace_catalog_generation,
            workspace_catalog_root_digest=self.workspace_catalog_root_digest,
            code_catalog_ref=self.code_catalog_ref,
            code_catalog_generation=self.code_catalog_generation,
            code_catalog_root_digest=self.code_catalog_root_digest,
            code_catalog_match_admission_digests=self.code_catalog_match_admission_digests,
            graph_digest=self.graph_digest,
        )
        if _content_digest(self.admission_digest, "plan_admission.digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_ADMISSION, payload
        ):
            raise ContractViolation("graph plan admission digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_ADMISSION,
            **_graph_plan_admission_payload(
                selection_resolution_digest=self.selection_resolution_digest,
                workspace_catalog_ref=self.workspace_catalog_ref,
                workspace_catalog_generation=self.workspace_catalog_generation,
                workspace_catalog_root_digest=self.workspace_catalog_root_digest,
                code_catalog_ref=self.code_catalog_ref,
                code_catalog_generation=self.code_catalog_generation,
                code_catalog_root_digest=self.code_catalog_root_digest,
                code_catalog_match_admission_digests=self.code_catalog_match_admission_digests,
                graph_digest=self.graph_digest,
            ),
            "admission_digest": self.admission_digest.to_wire(),
        }


def _graph_plan_admission_payload(**values: object) -> dict[str, object]:
    return {
        "code_catalog_generation": _nonnegative(
            values["code_catalog_generation"], "plan_admission.code_catalog_generation"
        ),
        "code_catalog_match_admission_digests": [
            item.to_wire()
            for item in _digest_tuple(
                values["code_catalog_match_admission_digests"],
                "plan_admission.code_catalog_match_admission_digests",
                nonempty=True,
            )
        ],
        "code_catalog_ref": _token(
            values["code_catalog_ref"], "plan_admission.code_catalog_ref"
        ),
        "code_catalog_root_digest": _content_digest(
            values["code_catalog_root_digest"],
            "plan_admission.code_catalog_root_digest",
        ).to_wire(),
        "graph_digest": _content_digest(
            values["graph_digest"], "plan_admission.graph_digest"
        ).to_wire(),
        "selection_resolution_digest": _content_digest(
            values["selection_resolution_digest"],
            "plan_admission.selection_resolution_digest",
        ).to_wire(),
        "workspace_catalog_generation": _nonnegative(
            values["workspace_catalog_generation"],
            "plan_admission.workspace_catalog_generation",
        ),
        "workspace_catalog_ref": _token(
            values["workspace_catalog_ref"], "plan_admission.workspace_catalog_ref"
        ),
        "workspace_catalog_root_digest": _content_digest(
            values["workspace_catalog_root_digest"],
            "plan_admission.workspace_catalog_root_digest",
        ).to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationPlanningTimingEntry:
    stage: str
    elapsed_ns: int

    def __post_init__(self) -> None:
        if (
            _token(self.stage, "planning_timing.stage")
            not in WORKSPACE_MATERIALIZATION_PLANNING_TIMING_STAGES
        ):
            raise ContractViolation("planning timing stage unsupported")
        _nonnegative(self.elapsed_ns, "planning_timing.elapsed_ns")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"elapsed_ns": self.elapsed_ns, "stage": self.stage}


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationPlanningCounterEntry:
    counter: str
    value: int

    def __post_init__(self) -> None:
        if (
            _token(self.counter, "planning_counter.counter")
            not in WORKSPACE_MATERIALIZATION_PLANNING_COUNTERS
        ):
            raise ContractViolation("planning counter key unsupported")
        _nonnegative(self.value, "planning_counter.value")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"counter": self.counter, "value": self.value}


def _canonical_wire(value: object) -> bytes:
    return _INTERNAL_JSON_ENCODER.encode(value).encode("utf-8")


def _graph_execution_order(
    graph: WorkspaceSemanticMaterializationGraph,
) -> tuple[ContentDigest, ...]:
    _preflight_exact(graph, WorkspaceSemanticMaterializationGraph, "execution.graph")
    graph.__post_init__()
    result = tuple(item for layer in graph.topological_layers for item in layer)
    node_digests = tuple(item.node_digest for item in graph.nodes)
    if len(result) != len(node_digests) or set(result) != set(node_digests):
        raise ContractViolation("graph execution order differs from nodes")
    return result


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationNodeExecutionBinding:
    node_digest: ContentDigest
    package: SemanticPackageCoordinate
    package_entry: WorkspaceSemanticMaterializationPackageEntry
    code_intent: CodeSemanticMaterializationIntent
    workspace_admitted_intent: WorkspaceAdmittedPackageIntent
    planning_context: CodeSemanticPackagePlanningContext
    code_match: CodeSemanticContractMatch
    code_match_admission: CodeSemanticContractMatchAdmission
    planning_input_digest: ContentDigest
    dependency_demand_set: SemanticDependencyDemandSet
    planning_demand_closure: WorkspaceSemanticPlanningDemandClosure
    incoming_target_resolutions: tuple[WorkspaceDependencyTargetResolution, ...]
    required_result_products: tuple[CodeSemanticRequiredResultProduct, ...]
    binding_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        graph: WorkspaceSemanticMaterializationGraph,
        node_digest: ContentDigest,
        package: SemanticPackageCoordinate,
        package_entry: WorkspaceSemanticMaterializationPackageEntry,
        code_intent: CodeSemanticMaterializationIntent,
        workspace_admitted_intent: WorkspaceAdmittedPackageIntent,
        planning_context: CodeSemanticPackagePlanningContext,
        code_match: CodeSemanticContractMatch,
        code_match_admission: CodeSemanticContractMatchAdmission,
        dependency_demand_set: SemanticDependencyDemandSet,
        planning_input_digest: ContentDigest,
        planning_demand_closure: WorkspaceSemanticPlanningDemandClosure,
        incoming_target_resolutions: tuple[WorkspaceDependencyTargetResolution, ...],
        required_result_products: tuple[CodeSemanticRequiredResultProduct, ...],
    ) -> WorkspaceSemanticMaterializationNodeExecutionBinding:
        _node_execution_binding_payload(
            graph=graph,
            node_digest=node_digest,
            package=package,
            package_entry=package_entry,
            code_intent=code_intent,
            workspace_admitted_intent=workspace_admitted_intent,
            planning_context=planning_context,
            code_match=code_match,
            code_match_admission=code_match_admission,
            dependency_demand_set=dependency_demand_set,
            planning_input_digest=planning_input_digest,
            planning_demand_closure=planning_demand_closure,
            incoming_target_resolutions=incoming_target_resolutions,
            required_result_products=required_result_products,
        )
        return _frozen_value(
            cls,
            node_digest=node_digest,
            package=package,
            package_entry=package_entry,
            code_intent=code_intent,
            workspace_admitted_intent=workspace_admitted_intent,
            planning_context=planning_context,
            code_match=code_match,
            code_match_admission=code_match_admission,
            dependency_demand_set=dependency_demand_set,
            planning_input_digest=planning_input_digest,
            planning_demand_closure=planning_demand_closure,
            incoming_target_resolutions=incoming_target_resolutions,
            required_result_products=required_result_products,
            binding_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_EXECUTION_BINDING,
                _node_execution_binding_identity_payload(
                    node_digest=node_digest,
                    package_entry=package_entry,
                    code_intent=code_intent,
                    workspace_admitted_intent=workspace_admitted_intent,
                    planning_context=planning_context,
                    code_match=code_match,
                    code_match_admission=code_match_admission,
                    dependency_demand_set=dependency_demand_set,
                    planning_input_digest=planning_input_digest,
                    planning_demand_closure=planning_demand_closure,
                    incoming_target_resolutions=incoming_target_resolutions,
                    required_result_products=required_result_products,
                ),
            ),
        )

    def __post_init__(self) -> None:
        _node_execution_binding_payload(
            graph=None,
            node_digest=self.node_digest,
            package=self.package,
            package_entry=self.package_entry,
            code_intent=self.code_intent,
            workspace_admitted_intent=self.workspace_admitted_intent,
            planning_context=self.planning_context,
            code_match=self.code_match,
            code_match_admission=self.code_match_admission,
            dependency_demand_set=self.dependency_demand_set,
            planning_input_digest=self.planning_input_digest,
            planning_demand_closure=self.planning_demand_closure,
            incoming_target_resolutions=self.incoming_target_resolutions,
            required_result_products=self.required_result_products,
        )
        if _content_digest(self.binding_digest, "node_binding.digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_EXECUTION_BINDING,
            _node_execution_binding_identity_payload(
                node_digest=self.node_digest,
                package_entry=self.package_entry,
                code_intent=self.code_intent,
                workspace_admitted_intent=self.workspace_admitted_intent,
                planning_context=self.planning_context,
                code_match=self.code_match,
                code_match_admission=self.code_match_admission,
                dependency_demand_set=self.dependency_demand_set,
                planning_input_digest=self.planning_input_digest,
                planning_demand_closure=self.planning_demand_closure,
                incoming_target_resolutions=self.incoming_target_resolutions,
                required_result_products=self.required_result_products,
            ),
        ):
            raise ContractViolation("node execution binding digest mismatched")

    def validate_graph_context(
        self, graph: WorkspaceSemanticMaterializationGraph
    ) -> None:
        _node_execution_binding_payload(
            graph=graph,
            node_digest=self.node_digest,
            package=self.package,
            package_entry=self.package_entry,
            code_intent=self.code_intent,
            workspace_admitted_intent=self.workspace_admitted_intent,
            planning_context=self.planning_context,
            code_match=self.code_match,
            code_match_admission=self.code_match_admission,
            dependency_demand_set=self.dependency_demand_set,
            planning_input_digest=self.planning_input_digest,
            planning_demand_closure=self.planning_demand_closure,
            incoming_target_resolutions=self.incoming_target_resolutions,
            required_result_products=self.required_result_products,
        )
        self.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_EXECUTION_BINDING,
            **_node_execution_binding_payload(
                graph=None,
                node_digest=self.node_digest,
                package=self.package,
                package_entry=self.package_entry,
                code_intent=self.code_intent,
                workspace_admitted_intent=self.workspace_admitted_intent,
                planning_context=self.planning_context,
                code_match=self.code_match,
                code_match_admission=self.code_match_admission,
                dependency_demand_set=self.dependency_demand_set,
                planning_input_digest=self.planning_input_digest,
                planning_demand_closure=self.planning_demand_closure,
                incoming_target_resolutions=self.incoming_target_resolutions,
                required_result_products=self.required_result_products,
            ),
            "binding_digest": self.binding_digest.to_wire(),
        }


def _node_execution_binding_payload(
    *, graph: object, **values: object
) -> dict[str, object]:
    exact_inputs: tuple[tuple[str, type[object]], ...] = (
        ("node_digest", cast(type[object], ContentDigest)),
        ("planning_input_digest", cast(type[object], ContentDigest)),
        ("package", cast(type[object], SemanticPackageCoordinate)),
        (
            "package_entry",
            cast(type[object], WorkspaceSemanticMaterializationPackageEntry),
        ),
        ("code_intent", cast(type[object], CodeSemanticMaterializationIntent)),
        (
            "workspace_admitted_intent",
            cast(type[object], WorkspaceAdmittedPackageIntent),
        ),
        (
            "planning_context",
            cast(type[object], CodeSemanticPackagePlanningContext),
        ),
        ("code_match", cast(type[object], CodeSemanticContractMatch)),
        (
            "code_match_admission",
            cast(type[object], CodeSemanticContractMatchAdmission),
        ),
        (
            "dependency_demand_set",
            cast(type[object], SemanticDependencyDemandSet),
        ),
        (
            "planning_demand_closure",
            cast(type[object], WorkspaceSemanticPlanningDemandClosure),
        ),
    )
    for name, expected in exact_inputs:
        if type(values[name]) is not expected:
            raise TypeError(f"node_binding.{name} must be exact {expected.__name__}")
    resolutions = _preflight_tuple(
        values["incoming_target_resolutions"],
        WorkspaceDependencyTargetResolution,
        "node_binding.incoming_target_resolutions",
    )
    requirements = _preflight_tuple(
        values["required_result_products"],
        CodeSemanticRequiredResultProduct,
        "node_binding.required_result_products",
    )
    if graph is not None and type(graph) is not WorkspaceSemanticMaterializationGraph:
        raise TypeError("node_binding.graph must be exact graph")

    node_digest = cast(ContentDigest, values["node_digest"])
    package = cast(SemanticPackageCoordinate, values["package"])
    entry = cast(WorkspaceSemanticMaterializationPackageEntry, values["package_entry"])
    intent = cast(CodeSemanticMaterializationIntent, values["code_intent"])
    workspace_admission = cast(
        WorkspaceAdmittedPackageIntent, values["workspace_admitted_intent"]
    )
    context = cast(CodeSemanticPackagePlanningContext, values["planning_context"])
    match = cast(CodeSemanticContractMatch, values["code_match"])
    match_admission = cast(
        CodeSemanticContractMatchAdmission, values["code_match_admission"]
    )
    demand_set = cast(SemanticDependencyDemandSet, values["dependency_demand_set"])
    closure = cast(
        WorkspaceSemanticPlanningDemandClosure,
        values["planning_demand_closure"],
    )
    for item in (
        node_digest,
        package,
        entry,
        intent,
        workspace_admission,
        context,
        match,
        match_admission,
        demand_set,
        closure,
        *resolutions,
        *requirements,
    ):
        item.__post_init__()

    if (
        entry.package != package
        or workspace_admission.package_ref != package.package_ref
        or workspace_admission.code_intent_body != intent
        or workspace_admission.code_intent_digest != intent.intent_digest
        or workspace_admission.participation_policy_body != entry.participation_policy
        or workspace_admission.participation_policy_digest
        != entry.participation_policy.policy_digest
        or context.package != package
        or context.package_family != entry.package_family
        or context.package_role != entry.package_role
        or context.manifest_contract != entry.manifest_contract
        or context.code_intent != intent
        or context.required_result_products != requirements
        or match.context_digest != context.context_digest
        or match_admission.match_digest != match.match_digest
        or demand_set.package != package
        or demand_set.intent_digest != intent.intent_digest
        or demand_set.contract_profile_binding_digest != match.selected_entry_digest
        or closure.consumer_package != package
    ):
        raise ContractViolation("node execution binding bodies do not close")
    resolution_wires = tuple(_canonical_wire(item.to_wire()) for item in resolutions)
    if resolution_wires != tuple(sorted(set(resolution_wires))):
        raise ContractViolation(
            "incoming target resolutions must be unique and ordered"
        )
    requirement_wires = tuple(_canonical_wire(item.to_wire()) for item in requirements)
    if requirement_wires != tuple(sorted(set(requirement_wires))):
        raise ContractViolation("required result products must be unique and ordered")
    planned = closure.planned_dependency_inputs
    planned_by_resolution = {
        item.target_resolution_digest: (
            item.required_result_role,
            item.result_product_contract,
        )
        for item in planned
    }
    resolution_requirements = {
        item.resolution_digest: (
            item.required_result_role,
            item.result_product_contract,
        )
        for item in resolutions
    }
    if planned_by_resolution.keys() != resolution_requirements.keys():
        raise ContractViolation("target resolutions differ from planning closure")
    if planned_by_resolution != resolution_requirements:
        raise ContractViolation(
            "target result requirements differ from planning closure"
        )

    if graph is not None:
        graph_value = cast(WorkspaceSemanticMaterializationGraph, graph)
        graph_value.__post_init__()
        nodes = tuple(
            item for item in graph_value.nodes if item.node_digest == node_digest
        )
        if len(nodes) != 1:
            raise ContractViolation("node execution binding node absent from graph")
        node = nodes[0]
        if (
            node.package != package
            or node.package_entry_digest != entry.entry_digest
            or node.participation_policy_digest
            != entry.participation_policy.policy_digest
            or node.source_identity_digest != entry.source_identity_digest
            or node.local_code_match_digest != match.match_digest
            or node.composed_intent_digest != intent.intent_digest
            or node.demand_set_digest != demand_set.demand_set_digest
            or node.planning_demand_closure_digest
            != closure.planning_demand_closure_digest
        ):
            raise ContractViolation("node execution binding differs from graph node")
        incoming_edges = tuple(
            item
            for item in graph_value.edges
            if item.consumer_node_digest == node_digest
        )
        if {item.target_resolution_digest for item in incoming_edges} != {
            item.resolution_digest for item in resolutions
        }:
            raise ContractViolation("node execution binding differs from graph edges")

    return {
        "code_intent": intent.to_wire(),
        "code_match": match.to_wire(),
        "code_match_admission": match_admission.to_wire(),
        "dependency_demand_set": demand_set.to_wire(),
        "planning_input_digest": _content_digest(
            values["planning_input_digest"], "node_binding.planning_input_digest"
        ).to_wire(),
        "incoming_target_resolutions": [item.to_wire() for item in resolutions],
        "node_digest": node_digest.to_wire(),
        "package": package.to_wire(),
        "package_entry": entry.to_wire(),
        "planning_context": context.to_wire(),
        "planning_demand_closure": closure.to_wire(),
        "required_result_products": [item.to_wire() for item in requirements],
        "workspace_admitted_intent": workspace_admission.to_wire(),
    }


def _node_execution_binding_identity_payload(**values: object) -> dict[str, object]:
    return {
        "code_intent_digest": cast(
            CodeSemanticMaterializationIntent, values["code_intent"]
        ).intent_digest.value,
        "code_match_admission_digest": cast(
            CodeSemanticContractMatchAdmission,
            values["code_match_admission"],
        ).admission_digest.value,
        "code_match_digest": cast(
            CodeSemanticContractMatch, values["code_match"]
        ).match_digest.value,
        "planning_input_digest": cast(
            ContentDigest, values["planning_input_digest"]
        ).value,
        "dependency_demand_set_digest": cast(
            SemanticDependencyDemandSet, values["dependency_demand_set"]
        ).demand_set_digest.value,
        "incoming_target_resolution_digests": [
            item.resolution_digest.value
            for item in cast(
                tuple[WorkspaceDependencyTargetResolution, ...],
                values["incoming_target_resolutions"],
            )
        ],
        "node_digest": cast(ContentDigest, values["node_digest"]).value,
        "package_entry_digest": cast(
            WorkspaceSemanticMaterializationPackageEntry, values["package_entry"]
        ).entry_digest.value,
        "planning_context_digest": cast(
            CodeSemanticPackagePlanningContext, values["planning_context"]
        ).context_digest.value,
        "planning_demand_closure_digest": cast(
            WorkspaceSemanticPlanningDemandClosure,
            values["planning_demand_closure"],
        ).planning_demand_closure_digest.value,
        "required_result_product_digests": [
            item.requirement_digest.value
            for item in cast(
                tuple[CodeSemanticRequiredResultProduct, ...],
                values["required_result_products"],
            )
        ],
        "workspace_admitted_intent_digest": cast(
            WorkspaceAdmittedPackageIntent,
            values["workspace_admitted_intent"],
        ).admission_digest.value,
    }


def _create_planner_node_execution_binding(
    *,
    binding_digest: ContentDigest | None = None,
    **values: object,
) -> WorkspaceSemanticMaterializationNodeExecutionBinding:
    """Retain already-validated planner bodies without catalog or body rereads."""

    if binding_digest is None:
        binding_digest = _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_EXECUTION_BINDING,
            _node_execution_binding_identity_payload(**values),
        )
    else:
        _preflight_exact(
            binding_digest, ContentDigest, "planner_node_binding.binding_digest"
        )
    return _frozen_value(
        WorkspaceSemanticMaterializationNodeExecutionBinding,
        **values,
        binding_digest=binding_digest,
    )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraphExecutionBinding:
    graph_digest: ContentDigest
    ordered_node_bindings: tuple[
        WorkspaceSemanticMaterializationNodeExecutionBinding, ...
    ]
    binding_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        graph: WorkspaceSemanticMaterializationGraph,
        ordered_node_bindings: tuple[
            WorkspaceSemanticMaterializationNodeExecutionBinding, ...
        ],
    ) -> WorkspaceSemanticMaterializationGraphExecutionBinding:
        _graph_execution_binding_payload(
            graph=graph,
            graph_digest=graph.graph_digest
            if type(graph) is WorkspaceSemanticMaterializationGraph
            else None,
            ordered_node_bindings=ordered_node_bindings,
        )
        return _frozen_value(
            cls,
            graph_digest=graph.graph_digest,
            ordered_node_bindings=ordered_node_bindings,
            binding_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EXECUTION_BINDING,
                _graph_execution_binding_identity_payload(
                    graph_digest=graph.graph_digest,
                    ordered_node_bindings=ordered_node_bindings,
                ),
            ),
        )

    def __post_init__(self) -> None:
        _graph_execution_binding_payload(
            graph=None,
            graph_digest=self.graph_digest,
            ordered_node_bindings=self.ordered_node_bindings,
        )
        if _content_digest(self.binding_digest, "graph_binding.digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EXECUTION_BINDING,
            _graph_execution_binding_identity_payload(
                graph_digest=self.graph_digest,
                ordered_node_bindings=self.ordered_node_bindings,
            ),
        ):
            raise ContractViolation("graph execution binding digest mismatched")

    def validate_graph_context(
        self, graph: WorkspaceSemanticMaterializationGraph
    ) -> None:
        _graph_execution_binding_payload(
            graph=graph,
            graph_digest=self.graph_digest,
            ordered_node_bindings=self.ordered_node_bindings,
        )
        self.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EXECUTION_BINDING,
            **_graph_execution_binding_payload(
                graph=None,
                graph_digest=self.graph_digest,
                ordered_node_bindings=self.ordered_node_bindings,
            ),
            "binding_digest": self.binding_digest.to_wire(),
        }


def _graph_execution_binding_payload(
    *, graph: object, **values: object
) -> dict[str, object]:
    graph_digest = _preflight_exact(
        values["graph_digest"], ContentDigest, "graph_binding.graph_digest"
    )
    bindings = _preflight_tuple(
        values["ordered_node_bindings"],
        WorkspaceSemanticMaterializationNodeExecutionBinding,
        "graph_binding.ordered_node_bindings",
    )
    if not bindings:
        raise ContractViolation("graph execution binding must not be empty")
    for item in (graph_digest, *bindings):
        item.__post_init__()
    if graph is not None:
        graph_value = _preflight_exact(
            graph, WorkspaceSemanticMaterializationGraph, "graph_binding.graph"
        )
        graph_value.__post_init__()
        if graph_digest != graph_value.graph_digest:
            raise ContractViolation("graph execution binding graph differs")
        execution_order = _graph_execution_order(graph_value)
        if tuple(item.node_digest for item in bindings) != execution_order:
            raise ContractViolation("node bindings differ from graph execution order")
        nodes_by_digest = {item.node_digest: item for item in graph_value.nodes}
        incoming_by_consumer: dict[ContentDigest, set[ContentDigest]] = {}
        for edge in graph_value.edges:
            incoming_by_consumer.setdefault(edge.consumer_node_digest, set()).add(
                edge.target_resolution_digest
            )
        for item in bindings:
            node = nodes_by_digest[item.node_digest]
            if (
                node.package != item.package
                or node.package_entry_digest != item.package_entry.entry_digest
                or node.participation_policy_digest
                != item.package_entry.participation_policy.policy_digest
                or node.source_identity_digest
                != item.package_entry.source_identity_digest
                or node.local_code_match_digest != item.code_match.match_digest
                or node.composed_intent_digest != item.code_intent.intent_digest
                or node.demand_set_digest
                != item.dependency_demand_set.demand_set_digest
                or node.planning_demand_closure_digest
                != item.planning_demand_closure.planning_demand_closure_digest
                or incoming_by_consumer.get(item.node_digest, set())
                != {
                    resolution.resolution_digest
                    for resolution in item.incoming_target_resolutions
                }
            ):
                raise ContractViolation("node execution binding differs from graph")
    elif len({item.node_digest for item in bindings}) != len(bindings):
        raise ContractViolation("graph execution node bindings must be unique")
    return {
        "graph_digest": graph_digest.to_wire(),
        "ordered_node_bindings": [item.to_wire() for item in bindings],
    }


def _graph_execution_binding_identity_payload(**values: object) -> dict[str, object]:
    return {
        "graph_digest": cast(ContentDigest, values["graph_digest"]).value,
        "ordered_node_binding_digests": [
            item.binding_digest.value
            for item in cast(
                tuple[WorkspaceSemanticMaterializationNodeExecutionBinding, ...],
                values["ordered_node_bindings"],
            )
        ],
    }


def _create_planner_graph_execution_binding(
    *,
    graph: WorkspaceSemanticMaterializationGraph,
    ordered_node_bindings: tuple[
        WorkspaceSemanticMaterializationNodeExecutionBinding, ...
    ],
    binding_digest: ContentDigest | None = None,
) -> WorkspaceSemanticMaterializationGraphExecutionBinding:
    if binding_digest is None:
        binding_digest = _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EXECUTION_BINDING,
            _graph_execution_binding_identity_payload(
                graph_digest=graph.graph_digest,
                ordered_node_bindings=ordered_node_bindings,
            ),
        )
    else:
        _preflight_exact(
            binding_digest, ContentDigest, "planner_graph_binding.binding_digest"
        )
    return _frozen_value(
        WorkspaceSemanticMaterializationGraphExecutionBinding,
        graph_digest=graph.graph_digest,
        ordered_node_bindings=ordered_node_bindings,
        binding_digest=binding_digest,
    )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraphPlanResult:
    selection_resolution: WorkspaceMaterializationSelectionResolution
    graph: WorkspaceSemanticMaterializationGraph
    graph_plan_admission: WorkspaceSemanticMaterializationGraphPlanAdmission
    graph_execution_binding: WorkspaceSemanticMaterializationGraphExecutionBinding
    timing_entries: tuple[WorkspaceMaterializationPlanningTimingEntry, ...]
    counter_entries: tuple[WorkspaceMaterializationPlanningCounterEntry, ...]
    planning_result_digest: ContentDigest

    @classmethod
    def create(
        cls, **values: object
    ) -> WorkspaceSemanticMaterializationGraphPlanResult:
        _graph_plan_result_payload(**values)
        return _frozen_value(
            cls,
            **values,
            planning_result_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_RESULT,
                _graph_plan_result_identity_payload(**values),
            ),
        )

    def __post_init__(self) -> None:
        _graph_plan_result_payload(
            selection_resolution=self.selection_resolution,
            graph=self.graph,
            graph_plan_admission=self.graph_plan_admission,
            graph_execution_binding=self.graph_execution_binding,
            timing_entries=self.timing_entries,
            counter_entries=self.counter_entries,
        )
        if _content_digest(
            self.planning_result_digest, "plan_result.digest"
        ) != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_RESULT,
            _graph_plan_result_identity_payload(
                selection_resolution=self.selection_resolution,
                graph=self.graph,
                graph_plan_admission=self.graph_plan_admission,
                graph_execution_binding=self.graph_execution_binding,
                timing_entries=self.timing_entries,
                counter_entries=self.counter_entries,
            ),
        ):
            raise ContractViolation("graph plan result digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_RESULT,
            **_graph_plan_result_payload(
                selection_resolution=self.selection_resolution,
                graph=self.graph,
                graph_plan_admission=self.graph_plan_admission,
                graph_execution_binding=self.graph_execution_binding,
                timing_entries=self.timing_entries,
                counter_entries=self.counter_entries,
            ),
            "planning_result_digest": self.planning_result_digest.to_wire(),
        }


def _validate_graph_plan_execution_catalog_context(
    *,
    admission: WorkspaceSemanticMaterializationGraphPlanAdmission,
    execution_binding: WorkspaceSemanticMaterializationGraphExecutionBinding,
) -> None:
    _preflight_exact(
        admission,
        WorkspaceSemanticMaterializationGraphPlanAdmission,
        "plan_result.admission",
    )
    _preflight_exact(
        execution_binding,
        WorkspaceSemanticMaterializationGraphExecutionBinding,
        "plan_result.execution_binding",
    )
    expected_match_admission_digests = tuple(
        sorted(
            {
                item.code_match_admission.admission_digest
                for item in execution_binding.ordered_node_bindings
            },
            key=lambda item: item.value.encode("utf-8"),
        )
    )
    if (
        admission.code_catalog_match_admission_digests
        != expected_match_admission_digests
    ):
        raise ContractViolation(
            "plan result Code match-admission closure differs from node bindings"
        )
    if any(
        item.workspace_admitted_intent.catalog_root_digest
        != admission.workspace_catalog_root_digest
        or item.workspace_admitted_intent.catalog_generation
        != admission.workspace_catalog_generation
        or item.code_match_admission.catalog_ref != admission.code_catalog_ref
        or item.code_match_admission.catalog_generation
        != admission.code_catalog_generation
        or item.code_match_admission.catalog_root_digest
        != admission.code_catalog_root_digest
        for item in execution_binding.ordered_node_bindings
    ):
        raise ContractViolation("plan result catalog coordinates differ")


def _graph_plan_result_payload(**values: object) -> dict[str, object]:
    selection = _preflight_exact(
        values["selection_resolution"],
        WorkspaceMaterializationSelectionResolution,
        "plan_result.selection",
    )
    graph = _preflight_exact(
        values["graph"], WorkspaceSemanticMaterializationGraph, "plan_result.graph"
    )
    admission = _preflight_exact(
        values["graph_plan_admission"],
        WorkspaceSemanticMaterializationGraphPlanAdmission,
        "plan_result.admission",
    )
    execution_binding = _preflight_exact(
        values["graph_execution_binding"],
        WorkspaceSemanticMaterializationGraphExecutionBinding,
        "plan_result.execution_binding",
    )
    for item in (selection, graph, admission, execution_binding):
        item.__post_init__()
    if (
        admission.selection_resolution_digest != selection.resolution_digest
        or admission.graph_digest != graph.graph_digest
    ):
        raise ContractViolation("plan result admission differs from selection or graph")
    execution_binding.validate_graph_context(graph)
    if execution_binding.graph_digest != graph.graph_digest:
        raise ContractViolation("plan result execution binding differs from graph")
    _validate_graph_plan_execution_catalog_context(
        admission=admission,
        execution_binding=execution_binding,
    )
    timings = _exact_tuple(
        values["timing_entries"],
        WorkspaceMaterializationPlanningTimingEntry,
        "plan_result.timing_entries",
    )
    if (
        tuple(item.stage for item in timings)
        != WORKSPACE_MATERIALIZATION_PLANNING_TIMING_STAGES
    ):
        raise ContractViolation("planning timing stages differ")
    total = timings[-1].elapsed_ns
    if any(item.elapsed_ns > total for item in timings[:-1]):
        raise ContractViolation("planning component timing exceeds total")
    counters = _exact_tuple(
        values["counter_entries"],
        WorkspaceMaterializationPlanningCounterEntry,
        "plan_result.counter_entries",
    )
    if (
        tuple(item.counter for item in counters)
        != WORKSPACE_MATERIALIZATION_PLANNING_COUNTERS
    ):
        raise ContractViolation("planning counter keys differ")
    counter_values = {item.counter: item.value for item in counters}
    if counter_values["node_count"] != len(graph.nodes) or counter_values[
        "edge_count"
    ] != len(graph.edges):
        raise ContractViolation("planning graph counters differ")
    if counter_values["head_read_count"] != len(graph.nodes):
        raise ContractViolation("planning head reads differ from nodes")
    if counter_values["dependency_body_read_count"] != 0:
        raise ContractViolation("planning dependency body reads must be zero")
    if (
        counter_values["demand_planner_invocation_count"]
        != counter_values["fan_in_context_count"]
    ):
        raise ContractViolation("planning context and planner invocation counts differ")
    return {
        "counter_entries": [item.to_wire() for item in counters],
        "graph": graph.to_wire(),
        "graph_execution_binding": execution_binding.to_wire(),
        "graph_plan_admission": admission.to_wire(),
        "selection_resolution": selection.to_wire(),
        "timing_entries": [item.to_wire() for item in timings],
    }


def _graph_plan_result_identity_payload(**values: object) -> dict[str, object]:
    return {
        "counter_entries": [
            item.to_wire()
            for item in cast(
                tuple[WorkspaceMaterializationPlanningCounterEntry, ...],
                values["counter_entries"],
            )
        ],
        "graph_digest": cast(
            WorkspaceSemanticMaterializationGraph, values["graph"]
        ).graph_digest.to_wire(),
        "graph_execution_binding_digest": cast(
            WorkspaceSemanticMaterializationGraphExecutionBinding,
            values["graph_execution_binding"],
        ).binding_digest.to_wire(),
        "graph_plan_admission_digest": cast(
            WorkspaceSemanticMaterializationGraphPlanAdmission,
            values["graph_plan_admission"],
        ).admission_digest.to_wire(),
        "selection_resolution_digest": cast(
            WorkspaceMaterializationSelectionResolution,
            values["selection_resolution"],
        ).resolution_digest.to_wire(),
        "timing_entries": [
            item.to_wire()
            for item in cast(
                tuple[WorkspaceMaterializationPlanningTimingEntry, ...],
                values["timing_entries"],
            )
        ],
    }


def _create_planner_graph_plan_result(
    *,
    selection_resolution: WorkspaceMaterializationSelectionResolution,
    graph: WorkspaceSemanticMaterializationGraph,
    graph_plan_admission: WorkspaceSemanticMaterializationGraphPlanAdmission,
    graph_execution_binding: WorkspaceSemanticMaterializationGraphExecutionBinding,
    timing_entries: tuple[WorkspaceMaterializationPlanningTimingEntry, ...],
    counter_entries: tuple[WorkspaceMaterializationPlanningCounterEntry, ...],
) -> WorkspaceSemanticMaterializationGraphPlanResult:
    """Bind planner-issued aggregates without recursively revalidating the graph."""

    selection = _preflight_exact(
        selection_resolution,
        WorkspaceMaterializationSelectionResolution,
        "plan_result.selection",
    )
    graph_value = _preflight_exact(
        graph, WorkspaceSemanticMaterializationGraph, "plan_result.graph"
    )
    admission = _preflight_exact(
        graph_plan_admission,
        WorkspaceSemanticMaterializationGraphPlanAdmission,
        "plan_result.admission",
    )
    execution_binding = _preflight_exact(
        graph_execution_binding,
        WorkspaceSemanticMaterializationGraphExecutionBinding,
        "plan_result.execution_binding",
    )
    if (
        admission.selection_resolution_digest != selection.resolution_digest
        or admission.graph_digest != graph_value.graph_digest
    ):
        raise ContractViolation("plan result admission differs from selection or graph")
    if execution_binding.graph_digest != graph_value.graph_digest or tuple(
        item.node_digest for item in execution_binding.ordered_node_bindings
    ) != tuple(item for layer in graph_value.topological_layers for item in layer):
        raise ContractViolation("plan result execution binding differs from graph")
    _validate_graph_plan_execution_catalog_context(
        admission=admission,
        execution_binding=execution_binding,
    )
    timings = _exact_tuple(
        timing_entries,
        WorkspaceMaterializationPlanningTimingEntry,
        "plan_result.timing_entries",
    )
    if (
        tuple(item.stage for item in timings)
        != WORKSPACE_MATERIALIZATION_PLANNING_TIMING_STAGES
    ):
        raise ContractViolation("planning timing stages differ")
    total = timings[-1].elapsed_ns
    if any(item.elapsed_ns > total for item in timings[:-1]):
        raise ContractViolation("planning component timing exceeds total")
    counters = _exact_tuple(
        counter_entries,
        WorkspaceMaterializationPlanningCounterEntry,
        "plan_result.counter_entries",
    )
    if (
        tuple(item.counter for item in counters)
        != WORKSPACE_MATERIALIZATION_PLANNING_COUNTERS
    ):
        raise ContractViolation("planning counter keys differ")
    counter_values = {item.counter: item.value for item in counters}
    if counter_values["node_count"] != len(graph_value.nodes) or counter_values[
        "edge_count"
    ] != len(graph_value.edges):
        raise ContractViolation("planning graph counters differ")
    if counter_values["head_read_count"] != len(graph_value.nodes):
        raise ContractViolation("planning head reads differ from nodes")
    if counter_values["dependency_body_read_count"] != 0:
        raise ContractViolation("planning dependency body reads must be zero")
    if (
        counter_values["demand_planner_invocation_count"]
        != counter_values["fan_in_context_count"]
    ):
        raise ContractViolation("planning context and planner invocation counts differ")
    payload = _graph_plan_result_identity_payload(
        selection_resolution=selection,
        graph=graph_value,
        graph_plan_admission=admission,
        graph_execution_binding=execution_binding,
        timing_entries=timings,
        counter_entries=counters,
    )
    return _frozen_value(
        WorkspaceSemanticMaterializationGraphPlanResult,
        selection_resolution=selection,
        graph=graph_value,
        graph_plan_admission=admission,
        graph_execution_binding=execution_binding,
        timing_entries=timings,
        counter_entries=counters,
        planning_result_digest=_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_RESULT, payload
        ),
    )


class _PortableWireValue(Protocol):
    def __post_init__(self) -> None: ...

    def to_wire(self) -> dict[str, object]: ...


def _canonical_exact_tuple[T](
    value: object,
    expected: type[T],
    path: str,
) -> tuple[T, ...]:
    items = _preflight_tuple(value, expected, path)
    wires: list[bytes] = []
    for item in items:
        portable = cast(_PortableWireValue, item)
        post_init = getattr(portable, "__post_init__", None)
        to_wire = getattr(portable, "to_wire", None)
        if type(post_init).__name__ != "method" or type(to_wire).__name__ != "method":
            raise TypeError(f"{path} members must expose exact portable behavior")
        portable.__post_init__()
        wires.append(_canonical_wire(portable.to_wire()))
    if tuple(wires) != tuple(sorted(set(wires))):
        raise ContractViolation(f"{path} must be unique and canonically ordered")
    return items


@dataclass(frozen=True, slots=True)
class WorkspaceFulfilledDependencyProductV3:
    graph_digest: ContentDigest
    consumer_node_digest: ContentDigest
    target_node_digest: ContentDigest
    target_resolution: WorkspaceDependencyTargetResolution
    head_h1_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3
    head_h2_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3
    head_h1_reread_evidence_digest: ContentDigest
    head_h2_reread_evidence_digest: ContentDigest
    result_head_revision: int
    result_head_digest: ContentDigest
    result_execution_input_closure_digest: ContentDigest
    consumed_body_coordinate: SemanticValueCoordinate
    fulfillment_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
        consumer_node_digest: ContentDigest,
        target_node_digest: ContentDigest,
        target_resolution: WorkspaceDependencyTargetResolution,
        head_h1: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        head_h2: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        consumed_body_coordinate: SemanticValueCoordinate,
    ) -> WorkspaceFulfilledDependencyProductV3:
        values = {
            "graph_digest": plan_result.graph.graph_digest
            if type(plan_result) is WorkspaceSemanticMaterializationGraphPlanResult
            else None,
            "consumer_node_digest": consumer_node_digest,
            "target_node_digest": target_node_digest,
            "target_resolution": target_resolution,
            "head_h1_reread_evidence": head_h1,
            "head_h2_reread_evidence": head_h2,
            "head_h1_reread_evidence_digest": head_h1.reread_evidence_digest
            if type(head_h1) is WorkspaceSemanticMaterializationHeadRereadEvidenceV3
            else None,
            "head_h2_reread_evidence_digest": head_h2.reread_evidence_digest
            if type(head_h2) is WorkspaceSemanticMaterializationHeadRereadEvidenceV3
            else None,
            "result_head_revision": head_h1.materialization_head_revision
            if type(head_h1) is WorkspaceSemanticMaterializationHeadRereadEvidenceV3
            else None,
            "result_head_digest": head_h1.materialization_head_digest
            if type(head_h1) is WorkspaceSemanticMaterializationHeadRereadEvidenceV3
            else None,
            "result_execution_input_closure_digest": head_h1.execution_input_closure_digest
            if type(head_h1) is WorkspaceSemanticMaterializationHeadRereadEvidenceV3
            else None,
            "consumed_body_coordinate": consumed_body_coordinate,
        }
        _validate_fulfilled_product_context(
            plan_result=plan_result,
            head_h1=head_h1,
            head_h2=head_h2,
            **values,
        )
        payload = _fulfilled_product_v2_payload(**values)
        return _frozen_value(
            cls,
            **values,
            fulfillment_digest=_digest(
                WORKSPACE_FULFILLED_DEPENDENCY_PRODUCT_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        _validate_fulfilled_head_pair(
            head_h1=self.head_h1_reread_evidence,
            head_h2=self.head_h2_reread_evidence,
            head_h1_reread_evidence_digest=self.head_h1_reread_evidence_digest,
            head_h2_reread_evidence_digest=self.head_h2_reread_evidence_digest,
            result_head_revision=self.result_head_revision,
            result_head_digest=self.result_head_digest,
            result_execution_input_closure_digest=self.result_execution_input_closure_digest,
            consumed_body_coordinate=self.consumed_body_coordinate,
        )
        payload = _fulfilled_product_v2_payload(
            graph_digest=self.graph_digest,
            consumer_node_digest=self.consumer_node_digest,
            target_node_digest=self.target_node_digest,
            target_resolution=self.target_resolution,
            head_h1_reread_evidence_digest=self.head_h1_reread_evidence_digest,
            head_h2_reread_evidence_digest=self.head_h2_reread_evidence_digest,
            result_head_revision=self.result_head_revision,
            result_head_digest=self.result_head_digest,
            result_execution_input_closure_digest=self.result_execution_input_closure_digest,
            consumed_body_coordinate=self.consumed_body_coordinate,
        )
        if _content_digest(
            self.fulfillment_digest, "fulfillment_v2.fulfillment_digest"
        ) != _digest(WORKSPACE_FULFILLED_DEPENDENCY_PRODUCT_V3, payload):
            raise ContractViolation("fulfilled dependency product V2 digest mismatched")

    def validate_context(
        self,
        *,
        plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    ) -> None:
        _validate_fulfilled_product_context(
            plan_result=plan_result,
            head_h1=self.head_h1_reread_evidence,
            head_h2=self.head_h2_reread_evidence,
            graph_digest=self.graph_digest,
            consumer_node_digest=self.consumer_node_digest,
            target_node_digest=self.target_node_digest,
            target_resolution=self.target_resolution,
            head_h1_reread_evidence_digest=self.head_h1_reread_evidence_digest,
            head_h2_reread_evidence_digest=self.head_h2_reread_evidence_digest,
            result_head_revision=self.result_head_revision,
            result_head_digest=self.result_head_digest,
            result_execution_input_closure_digest=self.result_execution_input_closure_digest,
            consumed_body_coordinate=self.consumed_body_coordinate,
        )
        self.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_FULFILLED_DEPENDENCY_PRODUCT_V3,
            **_fulfilled_product_v2_payload(
                graph_digest=self.graph_digest,
                consumer_node_digest=self.consumer_node_digest,
                target_node_digest=self.target_node_digest,
                target_resolution=self.target_resolution,
                head_h1_reread_evidence_digest=self.head_h1_reread_evidence_digest,
                head_h2_reread_evidence_digest=self.head_h2_reread_evidence_digest,
                result_head_revision=self.result_head_revision,
                result_head_digest=self.result_head_digest,
                result_execution_input_closure_digest=self.result_execution_input_closure_digest,
                consumed_body_coordinate=self.consumed_body_coordinate,
            ),
            "fulfillment_digest": self.fulfillment_digest.to_wire(),
        }


def _fulfilled_product_v2_payload(**values: object) -> dict[str, object]:
    resolution = _preflight_exact(
        values["target_resolution"],
        WorkspaceDependencyTargetResolution,
        "fulfillment_v2.target_resolution",
    )
    coordinate = _preflight_exact(
        values["consumed_body_coordinate"],
        SemanticValueCoordinate,
        "fulfillment_v2.consumed_body_coordinate",
    )
    resolution.__post_init__()
    coordinate.__post_init__()
    if (
        coordinate.role != resolution.required_result_role
        or coordinate.contract != resolution.result_product_contract
    ):
        raise ContractViolation("fulfilled coordinate differs from target demand")
    return {
        "consumed_body_coordinate": coordinate.to_wire(),
        "consumer_node_digest": _content_digest(
            values["consumer_node_digest"], "fulfillment_v2.consumer_node_digest"
        ).to_wire(),
        "graph_digest": _content_digest(
            values["graph_digest"], "fulfillment_v2.graph_digest"
        ).to_wire(),
        "head_h1_reread_evidence_digest": _content_digest(
            values["head_h1_reread_evidence_digest"],
            "fulfillment_v2.head_h1_reread_evidence_digest",
        ).to_wire(),
        "head_h2_reread_evidence_digest": _content_digest(
            values["head_h2_reread_evidence_digest"],
            "fulfillment_v2.head_h2_reread_evidence_digest",
        ).to_wire(),
        "result_execution_input_closure_digest": _content_digest(
            values["result_execution_input_closure_digest"],
            "fulfillment_v2.result_execution_input_closure_digest",
        ).to_wire(),
        "result_head_digest": _content_digest(
            values["result_head_digest"], "fulfillment_v2.result_head_digest"
        ).to_wire(),
        "result_head_revision": _nonnegative(
            values["result_head_revision"], "fulfillment_v2.result_head_revision"
        ),
        "target_node_digest": _content_digest(
            values["target_node_digest"], "fulfillment_v2.target_node_digest"
        ).to_wire(),
        "target_resolution": resolution.to_wire(),
    }


def _validate_fulfilled_product_context(
    *,
    plan_result: object,
    head_h1: object,
    head_h2: object,
    **values: object,
) -> None:
    plan = _preflight_exact(
        plan_result,
        WorkspaceSemanticMaterializationGraphPlanResult,
        "fulfillment_v2.plan_result",
    )
    h1 = _preflight_exact(
        head_h1,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        "fulfillment_v2.head_h1",
    )
    h2 = _preflight_exact(
        head_h2,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        "fulfillment_v2.head_h2",
    )
    plan.__post_init__()
    h1.__post_init__()
    h2.__post_init__()
    _fulfilled_product_v2_payload(**values)
    consumer = _content_digest(
        values["consumer_node_digest"], "fulfillment_v2.consumer_node_digest"
    )
    target = _content_digest(
        values["target_node_digest"], "fulfillment_v2.target_node_digest"
    )
    resolution = cast(WorkspaceDependencyTargetResolution, values["target_resolution"])
    matching_edges = tuple(
        item
        for item in plan.graph.edges
        if item.consumer_node_digest == consumer
        and item.target_node_digest == target
        and item.target_resolution_digest == resolution.resolution_digest
    )
    if len(matching_edges) != 1:
        raise ContractViolation("fulfilled product does not bind one graph edge")
    consumer_bindings = tuple(
        item
        for item in plan.graph_execution_binding.ordered_node_bindings
        if item.node_digest == consumer
    )
    target_bindings = tuple(
        item
        for item in plan.graph_execution_binding.ordered_node_bindings
        if item.node_digest == target
    )
    if len(consumer_bindings) != 1 or len(target_bindings) != 1:
        raise ContractViolation("fulfilled product node binding absent")
    retained_resolutions = tuple(
        item
        for item in consumer_bindings[0].incoming_target_resolutions
        if item.resolution_digest == resolution.resolution_digest
    )
    if len(retained_resolutions) != 1 or _canonical_wire(
        retained_resolutions[0].to_wire()
    ) != _canonical_wire(resolution.to_wire()):
        raise ContractViolation("fulfilled target resolution differs from plan")
    if h1.observation_role != "dependency_h1" or h2.observation_role != "dependency_h2":
        raise ContractViolation("fulfilled head observation roles differ")
    if (
        h1.package != target_bindings[0].package
        or h2.package != target_bindings[0].package
        or h1.source_identity_digest
        != target_bindings[0].package_entry.source_identity_digest
        or h2.source_identity_digest
        != target_bindings[0].package_entry.source_identity_digest
        or h1.code_intent_digest != target_bindings[0].code_intent.intent_digest
        or h2.code_intent_digest != target_bindings[0].code_intent.intent_digest
        or h1.code_match_digest != target_bindings[0].code_match.match_digest
        or h1.planning_input_digest != target_bindings[0].planning_input_digest
        or h2.code_match_digest != target_bindings[0].code_match.match_digest
        or h2.planning_input_digest != target_bindings[0].planning_input_digest
        or _canonical_wire(h1.result_coordinate.to_wire())
        != _canonical_wire(h2.result_coordinate.to_wire())
        or h1.materialization_head_revision != h2.materialization_head_revision
        or h1.materialization_head_digest != h2.materialization_head_digest
        or h1.canonical_head_wire_digest != h2.canonical_head_wire_digest
        or h1.execution_input_closure_digest != h2.execution_input_closure_digest
        or h1.reread_evidence_digest != values["head_h1_reread_evidence_digest"]
        or h2.reread_evidence_digest != values["head_h2_reread_evidence_digest"]
        or h1.materialization_head_revision != values["result_head_revision"]
        or h1.materialization_head_digest != values["result_head_digest"]
        or h1.execution_input_closure_digest
        != values["result_execution_input_closure_digest"]
        or _canonical_wire(h1.result_coordinate.to_wire())
        != _canonical_wire(
            cast(SemanticValueCoordinate, values["consumed_body_coordinate"]).to_wire()
        )
        or plan.graph.graph_digest != values["graph_digest"]
    ):
        raise ContractViolation("fulfilled head stability window differs")


def _validate_fulfilled_head_pair(
    *, head_h1: object, head_h2: object, **values: object
) -> None:
    h1 = _preflight_exact(
        head_h1,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        "fulfillment_v2.head_h1",
    )
    h2 = _preflight_exact(
        head_h2,
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        "fulfillment_v2.head_h2",
    )
    coordinate = _preflight_exact(
        values["consumed_body_coordinate"],
        SemanticValueCoordinate,
        "fulfillment_v2.consumed_body_coordinate",
    )
    h1.__post_init__()
    h2.__post_init__()
    coordinate.__post_init__()
    if (
        h1.observation_role != "dependency_h1"
        or h2.observation_role != "dependency_h2"
        or h1.package != h2.package
        or _canonical_wire(h1.result_coordinate.to_wire())
        != _canonical_wire(h2.result_coordinate.to_wire())
        or h1.source_identity_digest != h2.source_identity_digest
        or h1.code_intent_digest != h2.code_intent_digest
        or h1.code_match_digest != h2.code_match_digest
        or h1.planning_input_digest != h2.planning_input_digest
        or h1.materialization_head_revision != h2.materialization_head_revision
        or h1.materialization_head_digest != h2.materialization_head_digest
        or h1.canonical_head_wire_digest != h2.canonical_head_wire_digest
        or h1.execution_input_closure_digest != h2.execution_input_closure_digest
        or h1.reread_evidence_digest != values["head_h1_reread_evidence_digest"]
        or h2.reread_evidence_digest != values["head_h2_reread_evidence_digest"]
        or h1.materialization_head_revision != values["result_head_revision"]
        or h1.materialization_head_digest != values["result_head_digest"]
        or h1.execution_input_closure_digest
        != values["result_execution_input_closure_digest"]
        or _canonical_wire(h1.result_coordinate.to_wire())
        != _canonical_wire(coordinate.to_wire())
    ):
        raise ContractViolation("fulfilled head evidence pair differs")


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationFailureEvidenceEntryV2:
    evidence_kind: str
    evidence_digest: ContentDigest
    entry_digest: ContentDigest

    @classmethod
    def create(
        cls, *, evidence_kind: str, evidence_digest: ContentDigest
    ) -> WorkspaceSemanticMaterializationFailureEvidenceEntryV2:
        payload = _failure_entry_payload(
            evidence_kind=evidence_kind, evidence_digest=evidence_digest
        )
        return _frozen_value(
            cls,
            evidence_kind=evidence_kind,
            evidence_digest=evidence_digest,
            entry_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_FAILURE_EVIDENCE_ENTRY_V2,
                payload,
            ),
        )

    def __post_init__(self) -> None:
        payload = _failure_entry_payload(
            evidence_kind=self.evidence_kind,
            evidence_digest=self.evidence_digest,
        )
        if _content_digest(self.entry_digest, "failure_entry.entry_digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_FAILURE_EVIDENCE_ENTRY_V2,
            payload,
        ):
            raise ContractViolation("failure evidence entry digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_FAILURE_EVIDENCE_ENTRY_V2,
            **_failure_entry_payload(
                evidence_kind=self.evidence_kind,
                evidence_digest=self.evidence_digest,
            ),
            "entry_digest": self.entry_digest.to_wire(),
        }


def _failure_entry_payload(**values: object) -> dict[str, object]:
    kind = _token(values["evidence_kind"], "failure_entry.evidence_kind")
    allowed = {
        item
        for required in WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_MATRIX_V2.values()
        for item in required
    }
    if kind not in allowed:
        raise ContractViolation("failure evidence kind unsupported")
    return {
        "evidence_digest": _content_digest(
            values["evidence_digest"], "failure_entry.evidence_digest"
        ).to_wire(),
        "evidence_kind": kind,
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationTerminalEvidenceContextV3:
    target_resolution: WorkspaceDependencyTargetResolution | None = None
    head_h1: WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None = None
    head_h2: WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None = None
    body_coordinate: SemanticValueCoordinate | None = None
    body: bytes | None = None
    observed_body: bytes | None = None
    execution_input_closure_digest: ContentDigest | None = None
    operation_request: WorkspaceSemanticMaterializationRequestV3 | None = None
    publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3 | None = (
        None
    )
    package_head_reread_evidence: (
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None
    ) = None
    session_source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3 | None = (
        None
    )
    session_append_request: WorkspaceMaterializationSessionAppendRequestV3 | None = None
    session_event_reread_evidence: (
        WorkspaceMaterializationSessionEventRereadEvidenceV3 | None
    ) = None
    session_fanout_receipt: WorkspaceMaterializationSessionFanoutReceiptV3 | None = None

    def __post_init__(self) -> None:
        exact_optional = (
            ("target_resolution", WorkspaceDependencyTargetResolution),
            ("head_h1", WorkspaceSemanticMaterializationHeadRereadEvidenceV3),
            ("head_h2", WorkspaceSemanticMaterializationHeadRereadEvidenceV3),
            ("body_coordinate", SemanticValueCoordinate),
            ("execution_input_closure_digest", ContentDigest),
            ("operation_request", WorkspaceSemanticMaterializationRequestV3),
            (
                "publication_receipt",
                WorkspaceSemanticMaterializationPublicationReceiptV3,
            ),
            (
                "package_head_reread_evidence",
                WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
            ),
            (
                "session_source_evidence",
                WorkspaceMaterializationSessionSourceEvidenceV3,
            ),
            ("session_append_request", WorkspaceMaterializationSessionAppendRequestV3),
            (
                "session_event_reread_evidence",
                WorkspaceMaterializationSessionEventRereadEvidenceV3,
            ),
            ("session_fanout_receipt", WorkspaceMaterializationSessionFanoutReceiptV3),
        )
        for name, expected in exact_optional:
            value = getattr(self, name)
            if value is not None and type(value) is not expected:
                raise TypeError(
                    f"terminal evidence context {name} must be exact or null"
                )
        for name in ("body", "observed_body"):
            value = getattr(self, name)
            if value is not None and type(value) is not bytes:
                raise TypeError(
                    f"terminal evidence context {name} must be exact bytes or null"
                )
        for name, _ in exact_optional:
            value = getattr(self, name)
            if value is not None:
                cast(_PortableWireValue, value).__post_init__()
        _validate_terminal_evidence_context_relations(self)


def _validate_terminal_evidence_context_relations(
    context: WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
) -> None:
    operation = context.operation_request
    publication = context.publication_receipt
    package_head = context.package_head_reread_evidence
    source = context.session_source_evidence
    append = context.session_append_request
    event = context.session_event_reread_evidence
    fanout = context.session_fanout_receipt
    closure = context.execution_input_closure_digest
    if (
        operation is not None
        and closure is not None
        and operation.execution_input_closure_digest != closure
    ):
        raise ContractViolation(
            "terminal operation request differs from closure evidence"
        )
    if publication is not None and (
        operation is None
        or publication.request.request_digest != operation.request_digest
    ):
        raise ContractViolation("terminal publication differs from operation request")
    if (
        package_head is not None
        and publication is not None
        and (
            package_head.observation_role != "package_result"
            or package_head.materialization_head_revision != publication.head_revision
            or package_head.canonical_head_wire_digest
            != publication.canonical_head_wire_digest
        )
    ):
        raise ContractViolation(
            "terminal package-result evidence differs from publication"
        )
    if (
        source is not None
        and package_head is not None
        and (
            source.head_reread_evidence.reread_evidence_digest
            != package_head.reread_evidence_digest
            or (source.publication_receipt is None and publication is not None)
            or (
                source.publication_receipt is not None
                and publication is not None
                and source.publication_receipt.receipt_digest
                != publication.receipt_digest
            )
        )
    ):
        raise ContractViolation("terminal session source differs from package evidence")
    if append is not None and (
        source is None
        or append.source_evidence.source_evidence_digest
        != source.source_evidence_digest
    ):
        raise ContractViolation("terminal session append differs from source evidence")
    if event is not None and (
        append is None
        or event.event.append_request.request_digest != append.request_digest
    ):
        raise ContractViolation("terminal positive event differs from append request")
    if fanout is not None and (
        append is None
        or event is None
        or fanout.append_request.request_digest != append.request_digest
        or fanout.event_reread_evidence.reread_evidence_digest
        != event.reread_evidence_digest
    ):
        raise ContractViolation("terminal fanout receipt differs from positive event")


def _derive_terminal_evidence_entries(
    *,
    required_kinds: tuple[str, ...],
    node_execution_binding_digest: ContentDigest,
    context: WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
) -> tuple[WorkspaceSemanticMaterializationFailureEvidenceEntryV2, ...]:
    if type(context) is not WorkspaceSemanticMaterializationTerminalEvidenceContextV3:
        raise TypeError("terminal evidence context must be exact")
    context.__post_init__()
    values: dict[str, ContentDigest | None] = {
        "node_binding": node_execution_binding_digest,
        "target_resolution": (
            None
            if context.target_resolution is None
            else context.target_resolution.resolution_digest
        ),
        "head_h1": None
        if context.head_h1 is None
        else context.head_h1.reread_evidence_digest,
        "head_h2": None
        if context.head_h2 is None
        else context.head_h2.reread_evidence_digest,
        "body_coordinate": (
            None
            if context.body_coordinate is None
            else ContentDigest.of_bytes(
                _canonical_wire(context.body_coordinate.to_wire())
            )
        ),
        "body": None if context.body is None else ContentDigest.of_bytes(context.body),
        "observed_body": (
            None
            if context.observed_body is None
            else ContentDigest.of_bytes(context.observed_body)
        ),
        "execution_input_closure": context.execution_input_closure_digest,
        "operation_request": (
            None
            if context.operation_request is None
            else context.operation_request.request_digest
        ),
        "operation_result": (
            None
            if context.operation_request is None
            else context.operation_request.operation_result_digest
        ),
        "publication_receipt": (
            None
            if context.publication_receipt is None
            else context.publication_receipt.receipt_digest
        ),
        "package_result": (
            None
            if context.package_head_reread_evidence is None
            or context.package_head_reread_evidence.observation_role != "package_result"
            else context.package_head_reread_evidence.reread_evidence_digest
        ),
        "package_reuse": (
            None
            if context.package_head_reread_evidence is None
            or context.package_head_reread_evidence.observation_role != "package_reuse"
            else context.package_head_reread_evidence.reread_evidence_digest
        ),
        "session_source": (
            None
            if context.session_source_evidence is None
            else context.session_source_evidence.source_evidence_digest
        ),
        "session_append_request": (
            None
            if context.session_append_request is None
            else context.session_append_request.request_digest
        ),
        "session_event_positive": (
            None
            if context.session_event_reread_evidence is None
            else context.session_event_reread_evidence.reread_evidence_digest
        ),
        "session_fanout_receipt": (
            None
            if context.session_fanout_receipt is None
            else context.session_fanout_receipt.receipt_digest
        ),
    }
    if any(values.get(kind) is None for kind in required_kinds):
        raise ContractViolation("terminal exact evidence context is incomplete")
    return tuple(
        WorkspaceSemanticMaterializationFailureEvidenceEntryV2.create(
            evidence_kind=kind,
            evidence_digest=cast(ContentDigest, values[kind]),
        )
        for kind in required_kinds
    )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationTerminalFailureV3:
    graph_digest: ContentDigest
    execution_binding_digest: ContentDigest
    terminal_node_digest: ContentDigest
    node_execution_binding_digest: ContentDigest
    terminal_stage: str
    failure_code: str
    ordered_completed_fulfilled_products: tuple[
        WorkspaceFulfilledDependencyProductV3, ...
    ]
    ordered_evidence_entries: tuple[
        WorkspaceSemanticMaterializationFailureEvidenceEntryV2, ...
    ]
    evidence_context: WorkspaceSemanticMaterializationTerminalEvidenceContextV3
    failure_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
        terminal_node_digest: ContentDigest,
        terminal_stage: str,
        failure_code: str,
        ordered_completed_fulfilled_products: tuple[
            WorkspaceFulfilledDependencyProductV3, ...
        ],
        evidence_context: WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
    ) -> WorkspaceSemanticMaterializationTerminalFailureV3:
        binding = _plan_node_binding(plan_result, terminal_node_digest)
        required = WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_MATRIX_V2.get(
            (terminal_stage, failure_code)
        )
        if required is None:
            raise ContractViolation("terminal failure stage/code unsupported")
        entries = _derive_terminal_evidence_entries(
            required_kinds=required,
            node_execution_binding_digest=binding.binding_digest,
            context=evidence_context,
        )
        values = {
            "graph_digest": plan_result.graph.graph_digest,
            "execution_binding_digest": plan_result.graph_execution_binding.binding_digest,
            "terminal_node_digest": terminal_node_digest,
            "node_execution_binding_digest": binding.binding_digest,
            "terminal_stage": terminal_stage,
            "failure_code": failure_code,
            "ordered_completed_fulfilled_products": ordered_completed_fulfilled_products,
            "ordered_evidence_entries": entries,
            "evidence_context": evidence_context,
        }
        _validate_terminal_failure_context(plan_result=plan_result, **values)
        payload = _terminal_failure_payload(**values)
        return _frozen_value(
            cls,
            **values,
            failure_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_FAILURE_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _terminal_failure_payload(
            graph_digest=self.graph_digest,
            execution_binding_digest=self.execution_binding_digest,
            terminal_node_digest=self.terminal_node_digest,
            node_execution_binding_digest=self.node_execution_binding_digest,
            terminal_stage=self.terminal_stage,
            failure_code=self.failure_code,
            ordered_completed_fulfilled_products=self.ordered_completed_fulfilled_products,
            ordered_evidence_entries=self.ordered_evidence_entries,
            evidence_context=self.evidence_context,
        )
        if _content_digest(
            self.failure_digest, "terminal_failure.failure_digest"
        ) != _digest(WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_FAILURE_V3, payload):
            raise ContractViolation("terminal failure digest mismatched")

    def validate_context(
        self, plan_result: WorkspaceSemanticMaterializationGraphPlanResult
    ) -> None:
        _validate_terminal_failure_context(
            plan_result=plan_result,
            graph_digest=self.graph_digest,
            execution_binding_digest=self.execution_binding_digest,
            terminal_node_digest=self.terminal_node_digest,
            node_execution_binding_digest=self.node_execution_binding_digest,
            terminal_stage=self.terminal_stage,
            failure_code=self.failure_code,
            ordered_completed_fulfilled_products=self.ordered_completed_fulfilled_products,
            ordered_evidence_entries=self.ordered_evidence_entries,
            evidence_context=self.evidence_context,
        )
        self.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_FAILURE_V3,
            **_terminal_failure_payload(
                graph_digest=self.graph_digest,
                execution_binding_digest=self.execution_binding_digest,
                terminal_node_digest=self.terminal_node_digest,
                node_execution_binding_digest=self.node_execution_binding_digest,
                terminal_stage=self.terminal_stage,
                failure_code=self.failure_code,
                ordered_completed_fulfilled_products=self.ordered_completed_fulfilled_products,
                ordered_evidence_entries=self.ordered_evidence_entries,
                evidence_context=self.evidence_context,
            ),
            "failure_digest": self.failure_digest.to_wire(),
        }


def _terminal_failure_payload(**values: object) -> dict[str, object]:
    products = _preflight_tuple(
        values["ordered_completed_fulfilled_products"],
        WorkspaceFulfilledDependencyProductV3,
        "terminal_failure.completed_products",
    )
    product_wires = tuple(_canonical_wire(item.to_wire()) for item in products)
    if len(set(product_wires)) != len(product_wires):
        raise ContractViolation("terminal fulfilled products must be unique")
    entries = _preflight_tuple(
        values["ordered_evidence_entries"],
        WorkspaceSemanticMaterializationFailureEvidenceEntryV2,
        "terminal_failure.evidence_entries",
    )
    for item in entries:
        item.__post_init__()
    kinds = tuple(item.evidence_kind for item in entries)
    if kinds != tuple(sorted(set(kinds), key=lambda item: item.encode("utf-8"))):
        raise ContractViolation("terminal failure evidence entries differ in order")
    stage = _token(values["terminal_stage"], "terminal_failure.terminal_stage")
    code = _token(values["failure_code"], "terminal_failure.failure_code")
    required = WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_MATRIX_V2.get((stage, code))
    if required is None or kinds != required:
        raise ContractViolation("terminal failure stage/code evidence set differs")
    context = _preflight_exact(
        values["evidence_context"],
        WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
        "terminal_failure.evidence_context",
    )
    expected_entries = _derive_terminal_evidence_entries(
        required_kinds=required,
        node_execution_binding_digest=_content_digest(
            values["node_execution_binding_digest"],
            "terminal_failure.node_execution_binding_digest",
        ),
        context=context,
    )
    if tuple(_canonical_wire(item.to_wire()) for item in entries) != tuple(
        _canonical_wire(item.to_wire()) for item in expected_entries
    ):
        raise ContractViolation("terminal evidence entries differ from exact context")
    return {
        "execution_binding_digest": _content_digest(
            values["execution_binding_digest"],
            "terminal_failure.execution_binding_digest",
        ).to_wire(),
        "failure_code": code,
        "graph_digest": _content_digest(
            values["graph_digest"], "terminal_failure.graph_digest"
        ).to_wire(),
        "node_execution_binding_digest": _content_digest(
            values["node_execution_binding_digest"],
            "terminal_failure.node_execution_binding_digest",
        ).to_wire(),
        "ordered_completed_fulfilled_products": [item.to_wire() for item in products],
        "ordered_evidence_entries": [item.to_wire() for item in entries],
        "terminal_node_digest": _content_digest(
            values["terminal_node_digest"],
            "terminal_failure.terminal_node_digest",
        ).to_wire(),
        "terminal_stage": stage,
    }


def _plan_node_binding(
    plan_result: object, node_digest: object
) -> WorkspaceSemanticMaterializationNodeExecutionBinding:
    plan = _preflight_exact(
        plan_result,
        WorkspaceSemanticMaterializationGraphPlanResult,
        "execution_evidence.plan_result",
    )
    node = _content_digest(node_digest, "execution_evidence.node_digest")
    plan.__post_init__()
    matches = tuple(
        item
        for item in plan.graph_execution_binding.ordered_node_bindings
        if item.node_digest == node
    )
    if len(matches) != 1:
        raise ContractViolation("execution evidence node binding absent")
    return matches[0]


def _validate_terminal_failure_context(
    *, plan_result: object, **values: object
) -> None:
    plan = _preflight_exact(
        plan_result,
        WorkspaceSemanticMaterializationGraphPlanResult,
        "terminal_failure.plan_result",
    )
    binding = _plan_node_binding(plan, values["terminal_node_digest"])
    _terminal_failure_payload(**values)
    if (
        values["graph_digest"] != plan.graph.graph_digest
        or values["execution_binding_digest"]
        != plan.graph_execution_binding.binding_digest
        or values["node_execution_binding_digest"] != binding.binding_digest
    ):
        raise ContractViolation("terminal failure differs from plan context")
    products = cast(
        tuple[WorkspaceFulfilledDependencyProductV3, ...],
        values["ordered_completed_fulfilled_products"],
    )
    for product in products:
        product.validate_context(plan_result=plan)
    expected_resolutions = binding.incoming_target_resolutions
    product_resolutions = tuple(item.target_resolution for item in products)
    if product_resolutions != expected_resolutions[: len(product_resolutions)]:
        raise ContractViolation("terminal fulfilled products are not incoming prefix")
    stage = cast(str, values["terminal_stage"])
    if stage == "binding_validation" and products:
        raise ContractViolation("binding failure cannot have fulfilled products")
    if stage not in {
        "binding_validation",
        "dependency_head_reread",
        "dependency_body_read",
    } and len(products) != len(expected_resolutions):
        raise ContractViolation("late terminal failure lacks complete fulfillment")
    entries = cast(
        tuple[WorkspaceSemanticMaterializationFailureEvidenceEntryV2, ...],
        values["ordered_evidence_entries"],
    )
    entry_by_kind = {item.evidence_kind: item.evidence_digest for item in entries}
    if (
        "node_binding" in entry_by_kind
        and entry_by_kind["node_binding"] != binding.binding_digest
    ):
        raise ContractViolation("terminal node-binding evidence differs")
    if "target_resolution" in entry_by_kind and (
        len(products) >= len(expected_resolutions)
        or entry_by_kind["target_resolution"]
        != expected_resolutions[len(products)].resolution_digest
    ):
        raise ContractViolation("terminal target-resolution evidence differs")
    context = cast(
        WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
        values["evidence_context"],
    )
    if "target_resolution" in entry_by_kind and (
        context.target_resolution is None
        or _canonical_wire(context.target_resolution.to_wire())
        != _canonical_wire(expected_resolutions[len(products)].to_wire())
    ):
        raise ContractViolation("terminal exact target resolution differs from plan")
    if context.package_head_reread_evidence is not None and (
        context.package_head_reread_evidence.package != binding.package
    ):
        raise ContractViolation("terminal package head differs from plan binding")
    for dependency_head in (context.head_h1, context.head_h2):
        if dependency_head is not None and (
            context.target_resolution is None
            or dependency_head.package
            != context.target_resolution.head_observation.package
        ):
            raise ContractViolation("terminal dependency head differs from plan target")
    if context.operation_request is not None and (
        context.operation_request.package != binding.package
        or context.operation_request.source_identity_digest
        != binding.package_entry.source_identity_digest
        or context.operation_request.code_intent_digest
        != binding.code_intent.intent_digest
        or context.operation_request.code_match_digest
        != binding.code_match.match_digest
        or context.operation_request.planning_input_digest
        != binding.planning_input_digest
    ):
        raise ContractViolation("terminal operation request differs from plan binding")


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationNodeResultEvidenceV3:
    graph_digest: ContentDigest
    execution_binding_digest: ContentDigest
    node_digest: ContentDigest
    outcome: str
    execution_input_closure_digest: ContentDigest
    ordered_fulfilled_products: tuple[WorkspaceFulfilledDependencyProductV3, ...]
    result_head_revision: int
    result_head_digest: ContentDigest
    result_coordinate: SemanticValueCoordinate
    package_head_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3
    publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3 | None
    session_source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3
    session_event_reread_evidence: WorkspaceMaterializationSessionEventRereadEvidenceV3
    session_fanout_receipt: WorkspaceMaterializationSessionFanoutReceiptV3
    session_source_evidence_digest: ContentDigest
    session_event_reread_evidence_digest: ContentDigest
    operation_result_digest: ContentDigest | None
    publication_request_digest: ContentDigest | None
    publication_receipt_digest: ContentDigest | None
    session_fanout_receipt_digest: ContentDigest
    node_result_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
        node_digest: ContentDigest,
        outcome: str,
        execution_input_closure_digest: ContentDigest,
        ordered_fulfilled_products: tuple[WorkspaceFulfilledDependencyProductV3, ...],
        package_head_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3
        | None,
        session_source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3,
        session_event_reread_evidence: WorkspaceMaterializationSessionEventRereadEvidenceV3,
        session_fanout_receipt: WorkspaceMaterializationSessionFanoutReceiptV3,
    ) -> WorkspaceSemanticMaterializationNodeResultEvidenceV3:
        head = _preflight_exact(
            package_head_reread_evidence,
            WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
            "node_result.package_head_reread_evidence",
        )
        source = _preflight_exact(
            session_source_evidence,
            WorkspaceMaterializationSessionSourceEvidenceV3,
            "node_result.session_source_evidence",
        )
        event_reread = _preflight_exact(
            session_event_reread_evidence,
            WorkspaceMaterializationSessionEventRereadEvidenceV3,
            "node_result.session_event_reread_evidence",
        )
        fanout = _preflight_exact(
            session_fanout_receipt,
            WorkspaceMaterializationSessionFanoutReceiptV3,
            "node_result.session_fanout_receipt",
        )
        if (
            publication_receipt is not None
            and type(publication_receipt)
            is not WorkspaceSemanticMaterializationPublicationReceiptV3
        ):
            raise TypeError("node result publication receipt must be exact or null")
        receipt = cast(
            WorkspaceSemanticMaterializationPublicationReceiptV3 | None,
            publication_receipt,
        )
        values = {
            "graph_digest": plan_result.graph.graph_digest
            if type(plan_result) is WorkspaceSemanticMaterializationGraphPlanResult
            else None,
            "execution_binding_digest": plan_result.graph_execution_binding.binding_digest
            if type(plan_result) is WorkspaceSemanticMaterializationGraphPlanResult
            else None,
            "node_digest": node_digest,
            "outcome": outcome,
            "execution_input_closure_digest": execution_input_closure_digest,
            "ordered_fulfilled_products": ordered_fulfilled_products,
            "result_head_revision": head.materialization_head_revision,
            "result_head_digest": head.materialization_head_digest,
            "result_coordinate": head.result_coordinate,
            "package_head_reread_evidence": head,
            "publication_receipt": receipt,
            "session_source_evidence": source,
            "session_event_reread_evidence": event_reread,
            "session_fanout_receipt": fanout,
            "session_source_evidence_digest": source.source_evidence_digest,
            "session_event_reread_evidence_digest": event_reread.reread_evidence_digest,
            "operation_result_digest": (
                None if receipt is None else receipt.request.operation_result_digest
            ),
            "publication_request_digest": (
                None if receipt is None else receipt.request.request_digest
            ),
            "publication_receipt_digest": (
                None if receipt is None else receipt.receipt_digest
            ),
            "session_fanout_receipt_digest": fanout.receipt_digest,
        }
        _validate_node_result_context(plan_result=plan_result, **values)
        payload = _node_result_v2_payload(**values)
        return _frozen_value(
            cls,
            **values,
            node_result_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_RESULT_EVIDENCE_V3,
                payload,
            ),
        )

    def __post_init__(self) -> None:
        payload = _node_result_v2_payload(
            graph_digest=self.graph_digest,
            execution_binding_digest=self.execution_binding_digest,
            node_digest=self.node_digest,
            outcome=self.outcome,
            execution_input_closure_digest=self.execution_input_closure_digest,
            ordered_fulfilled_products=self.ordered_fulfilled_products,
            result_head_revision=self.result_head_revision,
            result_head_digest=self.result_head_digest,
            result_coordinate=self.result_coordinate,
            package_head_reread_evidence=self.package_head_reread_evidence,
            publication_receipt=self.publication_receipt,
            session_source_evidence=self.session_source_evidence,
            session_event_reread_evidence=self.session_event_reread_evidence,
            session_fanout_receipt=self.session_fanout_receipt,
            session_source_evidence_digest=self.session_source_evidence_digest,
            session_event_reread_evidence_digest=self.session_event_reread_evidence_digest,
            operation_result_digest=self.operation_result_digest,
            publication_request_digest=self.publication_request_digest,
            publication_receipt_digest=self.publication_receipt_digest,
            session_fanout_receipt_digest=self.session_fanout_receipt_digest,
        )
        if _content_digest(
            self.node_result_digest, "node_result.node_result_digest"
        ) != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_RESULT_EVIDENCE_V3,
            payload,
        ):
            raise ContractViolation("node result evidence digest mismatched")

    def validate_context(
        self, plan_result: WorkspaceSemanticMaterializationGraphPlanResult
    ) -> None:
        _validate_node_result_context(
            plan_result=plan_result,
            graph_digest=self.graph_digest,
            execution_binding_digest=self.execution_binding_digest,
            node_digest=self.node_digest,
            outcome=self.outcome,
            execution_input_closure_digest=self.execution_input_closure_digest,
            ordered_fulfilled_products=self.ordered_fulfilled_products,
            result_head_revision=self.result_head_revision,
            result_head_digest=self.result_head_digest,
            result_coordinate=self.result_coordinate,
            package_head_reread_evidence=self.package_head_reread_evidence,
            publication_receipt=self.publication_receipt,
            session_source_evidence=self.session_source_evidence,
            session_event_reread_evidence=self.session_event_reread_evidence,
            session_fanout_receipt=self.session_fanout_receipt,
            session_source_evidence_digest=self.session_source_evidence_digest,
            session_event_reread_evidence_digest=self.session_event_reread_evidence_digest,
            operation_result_digest=self.operation_result_digest,
            publication_request_digest=self.publication_request_digest,
            publication_receipt_digest=self.publication_receipt_digest,
            session_fanout_receipt_digest=self.session_fanout_receipt_digest,
        )
        self.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_RESULT_EVIDENCE_V3,
            **_node_result_v2_payload(
                graph_digest=self.graph_digest,
                execution_binding_digest=self.execution_binding_digest,
                node_digest=self.node_digest,
                outcome=self.outcome,
                execution_input_closure_digest=self.execution_input_closure_digest,
                ordered_fulfilled_products=self.ordered_fulfilled_products,
                result_head_revision=self.result_head_revision,
                result_head_digest=self.result_head_digest,
                result_coordinate=self.result_coordinate,
                package_head_reread_evidence=self.package_head_reread_evidence,
                publication_receipt=self.publication_receipt,
                session_source_evidence=self.session_source_evidence,
                session_event_reread_evidence=self.session_event_reread_evidence,
                session_fanout_receipt=self.session_fanout_receipt,
                session_source_evidence_digest=self.session_source_evidence_digest,
                session_event_reread_evidence_digest=self.session_event_reread_evidence_digest,
                operation_result_digest=self.operation_result_digest,
                publication_request_digest=self.publication_request_digest,
                publication_receipt_digest=self.publication_receipt_digest,
                session_fanout_receipt_digest=self.session_fanout_receipt_digest,
            ),
            "node_result_digest": self.node_result_digest.to_wire(),
        }


def _node_result_v2_payload(**values: object) -> dict[str, object]:
    products = _preflight_tuple(
        values["ordered_fulfilled_products"],
        WorkspaceFulfilledDependencyProductV3,
        "node_result.fulfilled_products",
    )
    product_wires = tuple(_canonical_wire(item.to_wire()) for item in products)
    if len(set(product_wires)) != len(product_wires):
        raise ContractViolation("node result fulfilled products must be unique")
    head = _preflight_exact(
        values["package_head_reread_evidence"],
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        "node_result.package_head_reread_evidence",
    )
    coordinate = _preflight_exact(
        values["result_coordinate"],
        SemanticValueCoordinate,
        "node_result.result_coordinate",
    )
    head.__post_init__()
    coordinate.__post_init__()
    source = _preflight_exact(
        values["session_source_evidence"],
        WorkspaceMaterializationSessionSourceEvidenceV3,
        "node_result.session_source_evidence",
    )
    event_reread = _preflight_exact(
        values["session_event_reread_evidence"],
        WorkspaceMaterializationSessionEventRereadEvidenceV3,
        "node_result.session_event_reread_evidence",
    )
    fanout = _preflight_exact(
        values["session_fanout_receipt"],
        WorkspaceMaterializationSessionFanoutReceiptV3,
        "node_result.session_fanout_receipt",
    )
    source.__post_init__()
    event_reread.__post_init__()
    fanout.__post_init__()
    receipt_value = values["publication_receipt"]
    if (
        receipt_value is not None
        and type(receipt_value)
        is not WorkspaceSemanticMaterializationPublicationReceiptV3
    ):
        raise TypeError("node result publication receipt must be exact or null")
    publication = cast(
        WorkspaceSemanticMaterializationPublicationReceiptV3 | None,
        receipt_value,
    )
    if publication is not None:
        publication.__post_init__()
    outcome = _token(values["outcome"], "node_result.outcome")
    if outcome not in {"executed", "reused"}:
        raise ContractViolation("node result outcome unsupported")
    operation = _optional_digest(
        values["operation_result_digest"], "node_result.operation_result_digest"
    )
    request = _optional_digest(
        values["publication_request_digest"],
        "node_result.publication_request_digest",
    )
    receipt = _optional_digest(
        values["publication_receipt_digest"],
        "node_result.publication_receipt_digest",
    )
    if outcome == "executed":
        if (
            head.observation_role != "package_result"
            or publication is None
            or None in {operation, request, receipt}
        ):
            raise ContractViolation("executed node result evidence is incomplete")
    elif (
        head.observation_role != "package_reuse"
        or publication is not None
        or operation is not None
        or request is not None
        or receipt is not None
    ):
        raise ContractViolation("reused node result carries publication evidence")
    if (
        head.execution_input_closure_digest != values["execution_input_closure_digest"]
        or head.materialization_head_revision != values["result_head_revision"]
        or head.materialization_head_digest != values["result_head_digest"]
        or _canonical_wire(head.result_coordinate.to_wire())
        != _canonical_wire(coordinate.to_wire())
        or _canonical_wire(source.head_reread_evidence.to_wire())
        != _canonical_wire(head.to_wire())
        or _canonical_wire(event_reread.event.source_evidence.to_wire())
        != _canonical_wire(source.to_wire())
        or _canonical_wire(fanout.append_request.source_evidence.to_wire())
        != _canonical_wire(source.to_wire())
        or _canonical_wire(fanout.event_reread_evidence.to_wire())
        != _canonical_wire(event_reread.to_wire())
        or source.disposition != outcome
        or event_reread.event.disposition != outcome
        or values["session_source_evidence_digest"] != source.source_evidence_digest
        or values["session_event_reread_evidence_digest"]
        != event_reread.reread_evidence_digest
        or values["session_fanout_receipt_digest"] != fanout.receipt_digest
    ):
        raise ContractViolation("node result differs from positive package head")
    if publication is not None and (
        publication.canonical_head_wire_digest != head.canonical_head_wire_digest
        or publication.head_revision != head.materialization_head_revision
        or operation != publication.request.operation_result_digest
        or request != publication.request.request_digest
        or receipt != publication.receipt_digest
        or source.publication_receipt is None
        or source.publication_receipt.receipt_digest != publication.receipt_digest
    ):
        raise ContractViolation("node result publication evidence differs")
    return {
        "execution_binding_digest": _content_digest(
            values["execution_binding_digest"],
            "node_result.execution_binding_digest",
        ).to_wire(),
        "execution_input_closure_digest": _content_digest(
            values["execution_input_closure_digest"],
            "node_result.execution_input_closure_digest",
        ).to_wire(),
        "graph_digest": _content_digest(
            values["graph_digest"], "node_result.graph_digest"
        ).to_wire(),
        "node_digest": _content_digest(
            values["node_digest"], "node_result.node_digest"
        ).to_wire(),
        "operation_result_digest": None if operation is None else operation.to_wire(),
        "ordered_fulfilled_products": [item.to_wire() for item in products],
        "outcome": outcome,
        "package_head_reread_evidence": head.to_wire(),
        "publication_receipt": (None if publication is None else publication.to_wire()),
        "publication_receipt_digest": None if receipt is None else receipt.to_wire(),
        "publication_request_digest": None if request is None else request.to_wire(),
        "result_coordinate": coordinate.to_wire(),
        "result_head_digest": _content_digest(
            values["result_head_digest"], "node_result.result_head_digest"
        ).to_wire(),
        "result_head_revision": _nonnegative(
            values["result_head_revision"], "node_result.result_head_revision"
        ),
        "session_event_reread_evidence_digest": _content_digest(
            values["session_event_reread_evidence_digest"],
            "node_result.session_event_reread_evidence_digest",
        ).to_wire(),
        "session_event_reread_evidence": event_reread.to_wire(),
        "session_fanout_receipt_digest": _content_digest(
            values["session_fanout_receipt_digest"],
            "node_result.session_fanout_receipt_digest",
        ).to_wire(),
        "session_fanout_receipt": fanout.to_wire(),
        "session_source_evidence_digest": _content_digest(
            values["session_source_evidence_digest"],
            "node_result.session_source_evidence_digest",
        ).to_wire(),
        "session_source_evidence": source.to_wire(),
    }


def _validate_node_result_context(*, plan_result: object, **values: object) -> None:
    plan = _preflight_exact(
        plan_result,
        WorkspaceSemanticMaterializationGraphPlanResult,
        "node_result.plan_result",
    )
    binding = _plan_node_binding(plan, values["node_digest"])
    _node_result_v2_payload(**values)
    products = cast(
        tuple[WorkspaceFulfilledDependencyProductV3, ...],
        values["ordered_fulfilled_products"],
    )
    for product in products:
        product.validate_context(plan_result=plan)
    head = cast(
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        values["package_head_reread_evidence"],
    )
    result_coordinate = cast(SemanticValueCoordinate, values["result_coordinate"])
    required_results = {
        (item.role, item.contract) for item in binding.required_result_products
    }
    if (
        values["graph_digest"] != plan.graph.graph_digest
        or values["execution_binding_digest"]
        != plan.graph_execution_binding.binding_digest
        or tuple(item.target_resolution for item in products)
        != binding.incoming_target_resolutions
        or any(item.consumer_node_digest != binding.node_digest for item in products)
        or head.package != binding.package
        or head.source_identity_digest != binding.package_entry.source_identity_digest
        or head.code_intent_digest != binding.code_intent.intent_digest
        or head.code_match_digest != binding.code_match.match_digest
        or head.planning_input_digest != binding.planning_input_digest
        or head.execution_input_closure_digest
        != values["execution_input_closure_digest"]
        or (result_coordinate.role, result_coordinate.contract) not in required_results
        or cast(
            WorkspaceMaterializationSessionSourceEvidenceV3,
            values["session_source_evidence"],
        ).head_reread_evidence.reread_evidence_digest
        != head.reread_evidence_digest
        or cast(
            WorkspaceMaterializationSessionFanoutReceiptV3,
            values["session_fanout_receipt"],
        ).append_request.package_ref
        != binding.package.package_ref
    ):
        raise ContractViolation("node result differs from plan context")


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationResultCounterEntryV2:
    counter: str
    value: int

    def __post_init__(self) -> None:
        counter = _token(self.counter, "result_counter.counter")
        if counter not in WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2:
            raise ContractViolation("result counter unsupported")
        _nonnegative(self.value, "result_counter.value")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"counter": self.counter, "value": self.value}


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraphResultV3:
    graph_digest: ContentDigest
    execution_binding_digest: ContentDigest
    status: str
    ordered_node_results: tuple[
        WorkspaceSemanticMaterializationNodeResultEvidenceV3, ...
    ]
    terminal_failure: WorkspaceSemanticMaterializationTerminalFailureV3 | None
    ordered_fulfilled_products: tuple[WorkspaceFulfilledDependencyProductV3, ...]
    counter_entries: tuple[WorkspaceSemanticMaterializationResultCounterEntryV2, ...]
    result_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
        status: str,
        ordered_node_results: tuple[
            WorkspaceSemanticMaterializationNodeResultEvidenceV3, ...
        ],
        terminal_failure: WorkspaceSemanticMaterializationTerminalFailureV3 | None,
        ordered_fulfilled_products: tuple[WorkspaceFulfilledDependencyProductV3, ...],
        counter_entries: tuple[
            WorkspaceSemanticMaterializationResultCounterEntryV2, ...
        ],
    ) -> WorkspaceSemanticMaterializationGraphResultV3:
        values = {
            "graph_digest": plan_result.graph.graph_digest
            if type(plan_result) is WorkspaceSemanticMaterializationGraphPlanResult
            else None,
            "execution_binding_digest": plan_result.graph_execution_binding.binding_digest
            if type(plan_result) is WorkspaceSemanticMaterializationGraphPlanResult
            else None,
            "status": status,
            "ordered_node_results": ordered_node_results,
            "terminal_failure": terminal_failure,
            "ordered_fulfilled_products": ordered_fulfilled_products,
            "counter_entries": counter_entries,
        }
        _validate_graph_result_v2_context(plan_result=plan_result, **values)
        payload = _graph_result_v2_payload(**values)
        return _frozen_value(
            cls,
            **values,
            result_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _graph_result_v2_payload(
            graph_digest=self.graph_digest,
            execution_binding_digest=self.execution_binding_digest,
            status=self.status,
            ordered_node_results=self.ordered_node_results,
            terminal_failure=self.terminal_failure,
            ordered_fulfilled_products=self.ordered_fulfilled_products,
            counter_entries=self.counter_entries,
        )
        if _content_digest(
            self.result_digest, "graph_result_v2.result_digest"
        ) != _digest(WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3, payload):
            raise ContractViolation("graph result V2 digest mismatched")

    def validate_context(
        self, plan_result: WorkspaceSemanticMaterializationGraphPlanResult
    ) -> None:
        _validate_graph_result_v2_context(
            plan_result=plan_result,
            graph_digest=self.graph_digest,
            execution_binding_digest=self.execution_binding_digest,
            status=self.status,
            ordered_node_results=self.ordered_node_results,
            terminal_failure=self.terminal_failure,
            ordered_fulfilled_products=self.ordered_fulfilled_products,
            counter_entries=self.counter_entries,
        )
        self.__post_init__()

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3,
            **_graph_result_v2_payload(
                graph_digest=self.graph_digest,
                execution_binding_digest=self.execution_binding_digest,
                status=self.status,
                ordered_node_results=self.ordered_node_results,
                terminal_failure=self.terminal_failure,
                ordered_fulfilled_products=self.ordered_fulfilled_products,
                counter_entries=self.counter_entries,
            ),
            "result_digest": self.result_digest.to_wire(),
        }


def _graph_result_v2_payload(**values: object) -> dict[str, object]:
    node_results = _preflight_tuple(
        values["ordered_node_results"],
        WorkspaceSemanticMaterializationNodeResultEvidenceV3,
        "graph_result_v2.node_results",
    )
    products = _preflight_tuple(
        values["ordered_fulfilled_products"],
        WorkspaceFulfilledDependencyProductV3,
        "graph_result_v2.fulfilled_products",
    )
    counters = _preflight_tuple(
        values["counter_entries"],
        WorkspaceSemanticMaterializationResultCounterEntryV2,
        "graph_result_v2.counter_entries",
    )
    for item in (*node_results, *products, *counters):
        item.__post_init__()
    if (
        tuple(item.counter for item in counters)
        != WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2
    ):
        raise ContractViolation("graph result V2 counter keys differ")
    terminal_value = values["terminal_failure"]
    if (
        terminal_value is not None
        and type(terminal_value)
        is not WorkspaceSemanticMaterializationTerminalFailureV3
    ):
        raise TypeError("graph result V2 terminal failure must be exact or null")
    terminal = cast(
        WorkspaceSemanticMaterializationTerminalFailureV3 | None, terminal_value
    )
    if terminal is not None:
        terminal.__post_init__()
    status = _token(values["status"], "graph_result_v2.status")
    if status not in {"succeeded", "failed"}:
        raise ContractViolation("graph result V2 status unsupported")
    if (status == "succeeded") != (terminal is None):
        raise ContractViolation("graph result V2 terminal failure presence differs")
    return {
        "counter_entries": [item.to_wire() for item in counters],
        "execution_binding_digest": _content_digest(
            values["execution_binding_digest"],
            "graph_result_v2.execution_binding_digest",
        ).to_wire(),
        "graph_digest": _content_digest(
            values["graph_digest"], "graph_result_v2.graph_digest"
        ).to_wire(),
        "ordered_fulfilled_products": [item.to_wire() for item in products],
        "ordered_node_results": [item.to_wire() for item in node_results],
        "status": status,
        "terminal_failure": None if terminal is None else terminal.to_wire(),
    }


def _validate_graph_result_v2_context(*, plan_result: object, **values: object) -> None:
    plan = _preflight_exact(
        plan_result,
        WorkspaceSemanticMaterializationGraphPlanResult,
        "graph_result_v2.plan_result",
    )
    _graph_result_v2_payload(**values)
    if (
        values["graph_digest"] != plan.graph.graph_digest
        or values["execution_binding_digest"]
        != plan.graph_execution_binding.binding_digest
    ):
        raise ContractViolation("graph result V2 differs from plan")
    node_results = cast(
        tuple[WorkspaceSemanticMaterializationNodeResultEvidenceV3, ...],
        values["ordered_node_results"],
    )
    for item in node_results:
        item.validate_context(plan)
    order = tuple(
        item.node_digest for item in plan.graph_execution_binding.ordered_node_bindings
    )
    result_nodes = tuple(item.node_digest for item in node_results)
    status = cast(str, values["status"])
    terminal = cast(
        WorkspaceSemanticMaterializationTerminalFailureV3 | None,
        values["terminal_failure"],
    )
    if status == "succeeded":
        if result_nodes != order:
            raise ContractViolation("successful graph result lacks complete coverage")
    else:
        if terminal is None:
            raise ContractViolation("failed graph result lacks terminal evidence")
        terminal.validate_context(plan)
        if result_nodes != order[: len(result_nodes)]:
            raise ContractViolation("failed graph result node evidence is not prefix")
        if (
            len(result_nodes) >= len(order)
            or terminal.terminal_node_digest != order[len(result_nodes)]
        ):
            raise ContractViolation("failed graph result terminal node is not next")
    terminal_products = (
        () if terminal is None else terminal.ordered_completed_fulfilled_products
    )
    expected_products = (
        tuple(
            product
            for item in node_results
            for product in item.ordered_fulfilled_products
        )
        + terminal_products
    )
    products = cast(
        tuple[WorkspaceFulfilledDependencyProductV3, ...],
        values["ordered_fulfilled_products"],
    )
    if tuple(item.fulfillment_digest for item in products) != tuple(
        item.fulfillment_digest for item in expected_products
    ) or len({item.fulfillment_digest for item in products}) != len(products):
        raise ContractViolation("graph result V2 fulfillment closure differs")
    entries = () if terminal is None else terminal.ordered_evidence_entries
    entry_kinds = {item.evidence_kind for item in entries}
    counter_values = {
        item.counter: item.value
        for item in cast(
            tuple[WorkspaceSemanticMaterializationResultCounterEntryV2, ...],
            values["counter_entries"],
        )
    }
    expected_counters = {
        "dependency_body_observation_count": len(products)
        + int(bool(entry_kinds & {"body", "observed_body"})),
        "dependency_head_observation_count": (2 * len(products))
        + (
            len(entry_kinds & {"head_h1", "head_h2"})
            if terminal is not None
            and terminal.terminal_stage
            in {"dependency_head_reread", "dependency_body_read"}
            else 0
        ),
        "edge_count": len(plan.graph.edges),
        "executed_count": sum(item.outcome == "executed" for item in node_results),
        "fulfilled_product_count": len(products),
        "node_count": len(plan.graph.nodes),
        "package_head_observation_count": len(node_results)
        + int(bool(entry_kinds & {"package_result", "package_reuse"})),
        "publication_count": sum(item.outcome == "executed" for item in node_results)
        + int({"publication_receipt", "package_result"} <= entry_kinds),
        "reused_count": sum(item.outcome == "reused" for item in node_results),
        "session_event_count": len(node_results)
        + int("session_event_positive" in entry_kinds),
    }
    if counter_values != expected_counters:
        raise ContractViolation("graph result V2 counters differ from evidence")


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationGraphExecutionMetrics:
    binding_validation_ns: int
    dependency_head_reread_ns: int
    dependency_body_read_ns: int
    execution_input_closure_ns: int
    package_operation_ns: int
    session_fanout_ns: int
    total_ns: int
    physical_dependency_head_read_count: int
    physical_dependency_body_read_count: int
    physical_package_head_read_count: int
    physical_body_read_bytes: int
    physical_body_write_count: int
    physical_body_write_bytes: int
    physical_cas_attempt_count: int
    physical_retry_count: int
    physical_session_event_write_count: int
    physical_session_event_read_count: int

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            _nonnegative(getattr(self, name), f"execution_metrics.{name}")
        if any(
            getattr(self, name) > self.total_ns
            for name in (
                "binding_validation_ns",
                "dependency_head_reread_ns",
                "dependency_body_read_ns",
                "execution_input_closure_ns",
                "package_operation_ns",
                "session_fanout_ns",
            )
        ):
            raise ContractViolation("execution metric component exceeds total")


def _coordinator_digest_wire(value: ContentDigest) -> str:
    return value.value


def _coordinator_contract_wire(value: SemanticContractRef) -> dict[str, object]:
    return {
        "key": value.key,
        "schema_digest": _coordinator_digest_wire(value.schema_digest),
        "version": value.version,
    }


def _coordinator_package_wire(
    value: SemanticPackageCoordinate,
) -> dict[str, object]:
    return {
        "manifest_digest": _coordinator_digest_wire(value.manifest_digest),
        "package_kind": value.package_kind,
        "package_ref": value.package_ref,
    }


def _coordinator_coordinate_wire(
    value: SemanticValueCoordinate,
) -> dict[str, object]:
    return {
        "contract": _coordinator_contract_wire(value.contract),
        "digest": _coordinator_digest_wire(value.digest),
        "role": value.role,
        "size_bytes": value.size_bytes,
        "value_ref": value.value_ref,
    }


def _coordinator_publication_request_wire(
    value: WorkspaceSemanticMaterializationRequestV3,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_REQUEST_V3,
        "code_intent_digest": _coordinator_digest_wire(value.code_intent_digest),
        "code_match_digest": _coordinator_digest_wire(value.code_match_digest),
        "planning_input_digest": _coordinator_digest_wire(value.planning_input_digest),
        "execution_input_closure_digest": _coordinator_digest_wire(
            value.execution_input_closure_digest
        ),
        "expected_head_revision": value.expected_head_revision,
        "operation_result_digest": _coordinator_digest_wire(
            value.operation_result_digest
        ),
        "package": _coordinator_package_wire(value.package),
        "request_digest": _coordinator_digest_wire(value.request_digest),
        "result_coordinate": _coordinator_coordinate_wire(value.result_coordinate),
        "source_identity_digest": _coordinator_digest_wire(
            value.source_identity_digest
        ),
    }


def _coordinator_publication_head_wire(value: object) -> dict[str, object]:
    head = cast(WorkspaceSemanticMaterializationHeadV3, value)
    return {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V3,
        "code_intent_digest": _coordinator_digest_wire(head.code_intent_digest),
        "code_match_digest": _coordinator_digest_wire(head.code_match_digest),
        "planning_input_digest": _coordinator_digest_wire(head.planning_input_digest),
        "execution_input_closure_digest": _coordinator_digest_wire(
            head.execution_input_closure_digest
        ),
        "head_digest": _coordinator_digest_wire(head.head_digest),
        "operation_result_digest": _coordinator_digest_wire(
            head.operation_result_digest
        ),
        "package": _coordinator_package_wire(head.package),
        "request": _coordinator_publication_request_wire(head.request),
        "result_coordinate": _coordinator_coordinate_wire(head.result_coordinate),
        "source_identity_digest": _coordinator_digest_wire(head.source_identity_digest),
    }


def _coordinator_head_reread_wire(
    value: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_REREAD_EVIDENCE_V3,
        "canonical_head_wire_digest": _coordinator_digest_wire(
            value.canonical_head_wire_digest
        ),
        "code_intent_digest": _coordinator_digest_wire(value.code_intent_digest),
        "code_match_digest": _coordinator_digest_wire(value.code_match_digest),
        "planning_input_digest": _coordinator_digest_wire(value.planning_input_digest),
        "execution_input_closure_digest": _coordinator_digest_wire(
            value.execution_input_closure_digest
        ),
        "head": _coordinator_publication_head_wire(value.head),
        "materialization_head_digest": _coordinator_digest_wire(
            value.materialization_head_digest
        ),
        "materialization_head_revision": value.materialization_head_revision,
        "observation_role": value.observation_role,
        "package": _coordinator_package_wire(value.package),
        "reread_evidence_digest": _coordinator_digest_wire(
            value.reread_evidence_digest
        ),
        "result_coordinate": _coordinator_coordinate_wire(value.result_coordinate),
        "source_identity_digest": _coordinator_digest_wire(
            value.source_identity_digest
        ),
    }


def _coordinator_publication_receipt_wire(
    value: WorkspaceSemanticMaterializationPublicationReceiptV3,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_RECEIPT_V3,
        "canonical_head_wire_digest": _coordinator_digest_wire(
            value.canonical_head_wire_digest
        ),
        "head": _coordinator_publication_head_wire(value.head),
        "head_advanced": value.head_advanced,
        "head_revision": value.head_revision,
        "prior_head_revision": value.prior_head_revision,
        "receipt_digest": _coordinator_digest_wire(value.receipt_digest),
        "request": _coordinator_publication_request_wire(value.request),
    }


def _coordinator_session_source_wire(
    value: WorkspaceMaterializationSessionSourceEvidenceV3,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_MATERIALIZATION_SESSION_SOURCE_EVIDENCE_V3,
        "disposition": value.disposition,
        "head_reread_evidence_digest": _coordinator_digest_wire(
            value.head_reread_evidence.reread_evidence_digest
        ),
        "publication_receipt_digest": (
            None
            if value.publication_receipt_digest is None
            else _coordinator_digest_wire(value.publication_receipt_digest)
        ),
        "source_evidence_digest": _coordinator_digest_wire(
            value.source_evidence_digest
        ),
    }


def _coordinator_session_event_reread_wire(
    value: WorkspaceMaterializationSessionEventRereadEvidenceV3,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_MATERIALIZATION_SESSION_EVENT_REREAD_EVIDENCE_V3,
        "canonical_event_wire_digest": _coordinator_digest_wire(
            value.canonical_event_wire_digest
        ),
        "canonical_session_head_wire_digest": _coordinator_digest_wire(
            value.canonical_session_head_wire_digest
        ),
        "event_digest": _coordinator_digest_wire(value.event.event_digest),
        "reread_evidence_digest": _coordinator_digest_wire(
            value.reread_evidence_digest
        ),
        "session_head_digest": _coordinator_digest_wire(value.session_head.head_digest),
        "session_head_revision": value.session_head_revision,
        "workspace_session_ref": value.workspace_session_ref,
    }


def _coordinator_session_fanout_wire(
    value: WorkspaceMaterializationSessionFanoutReceiptV3,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_MATERIALIZATION_SESSION_FANOUT_RECEIPT_V3,
        "append_request_digest": _coordinator_digest_wire(
            value.append_request.request_digest
        ),
        "event_reread_evidence_digest": _coordinator_digest_wire(
            value.event_reread_evidence.reread_evidence_digest
        ),
        "head_advanced": value.head_advanced,
        "head_revision": value.head_revision,
        "prior_head_revision": value.prior_head_revision,
        "receipt_digest": _coordinator_digest_wire(value.receipt_digest),
    }


def _coordinator_fulfilled_product_wire(
    value: WorkspaceFulfilledDependencyProductV3,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_FULFILLED_DEPENDENCY_PRODUCT_V3,
        "consumed_body_coordinate": _coordinator_coordinate_wire(
            value.consumed_body_coordinate
        ),
        "consumer_node_digest": _coordinator_digest_wire(value.consumer_node_digest),
        "fulfillment_digest": _coordinator_digest_wire(value.fulfillment_digest),
        "graph_digest": _coordinator_digest_wire(value.graph_digest),
        "head_h1_reread_evidence_digest": _coordinator_digest_wire(
            value.head_h1_reread_evidence_digest
        ),
        "head_h2_reread_evidence_digest": _coordinator_digest_wire(
            value.head_h2_reread_evidence_digest
        ),
        "result_execution_input_closure_digest": _coordinator_digest_wire(
            value.result_execution_input_closure_digest
        ),
        "result_head_digest": _coordinator_digest_wire(value.result_head_digest),
        "result_head_revision": value.result_head_revision,
        "target_node_digest": _coordinator_digest_wire(value.target_node_digest),
        "target_resolution": _coordinator_target_resolution_wire(
            value.target_resolution
        ),
    }


def _coordinator_head_observation_wire(
    value: WorkspaceSemanticPackageHeadObservation,
) -> dict[str, object]:
    result: dict[str, object] = {
        "contract": _head_observation_contract(value.stored_head_contract),
        "expected_post_head_digest": (
            None
            if value.expected_post_head_digest is None
            else _coordinator_digest_wire(value.expected_post_head_digest)
        ),
        "expected_post_revision": value.expected_post_revision,
        "historical_execution_input_closure_digest": (
            None
            if value.historical_execution_input_closure_digest is None
            else _coordinator_digest_wire(
                value.historical_execution_input_closure_digest
            )
        ),
        "observation_digest": _coordinator_digest_wire(value.observation_digest),
        "package": _coordinator_package_wire(value.package),
        "predecessor_head_digest": (
            None
            if value.predecessor_head_digest is None
            else _coordinator_digest_wire(value.predecessor_head_digest)
        ),
        "predecessor_head_revision": value.predecessor_head_revision,
        "profile_binding_digest": _coordinator_digest_wire(
            value.profile_binding_digest
        ),
        "source_identity_digest": _coordinator_digest_wire(
            value.source_identity_digest
        ),
        "state": value.state,
    }
    if value.stored_head_contract is not None:
        occurrence = value.stored_package_occurrence
        if type(occurrence) is not WorkspaceMaterializationPackageOccurrenceV4:
            raise ContractViolation(
                "V4 graph head requires its exact package occurrence"
            )
        result["stored_head_contract"] = value.stored_head_contract
        result["stored_package_occurrence"] = occurrence.to_wire()
    return result


def _coordinator_target_resolution_wire(
    value: WorkspaceDependencyTargetResolution,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_DEPENDENCY_TARGET_RESOLUTION,
        "composed_target_intent_digest": _coordinator_digest_wire(
            value.composed_target_intent_digest
        ),
        "demand_digest": _coordinator_digest_wire(value.demand_digest),
        "head_observation": _coordinator_head_observation_wire(value.head_observation),
        "participation_policy_digest": _coordinator_digest_wire(
            value.participation_policy_digest
        ),
        "required_result_role": value.required_result_role,
        "resolution_digest": _coordinator_digest_wire(value.resolution_digest),
        "result_product_contract": _coordinator_contract_wire(
            value.result_product_contract
        ),
        "target_local_code_match_digest": _coordinator_digest_wire(
            value.target_local_code_match_digest
        ),
        "target_package_entry_digest": _coordinator_digest_wire(
            value.target_package_entry_digest
        ),
    }


def _coordinator_node_result_payload(values: dict[str, object]) -> dict[str, object]:
    products = cast(
        tuple[WorkspaceFulfilledDependencyProductV3, ...],
        values["ordered_fulfilled_products"],
    )
    head = cast(
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
        values["package_head_reread_evidence"],
    )
    publication = cast(
        WorkspaceSemanticMaterializationPublicationReceiptV3 | None,
        values["publication_receipt"],
    )
    source = cast(
        WorkspaceMaterializationSessionSourceEvidenceV3,
        values["session_source_evidence"],
    )
    event = cast(
        WorkspaceMaterializationSessionEventRereadEvidenceV3,
        values["session_event_reread_evidence"],
    )
    fanout = cast(
        WorkspaceMaterializationSessionFanoutReceiptV3,
        values["session_fanout_receipt"],
    )
    return {
        "execution_binding_digest": cast(
            ContentDigest, values["execution_binding_digest"]
        ).value,
        "execution_input_closure_digest": cast(
            ContentDigest, values["execution_input_closure_digest"]
        ).value,
        "graph_digest": cast(ContentDigest, values["graph_digest"]).value,
        "node_digest": cast(ContentDigest, values["node_digest"]).value,
        "operation_result_digest": (
            None
            if values["operation_result_digest"] is None
            else cast(ContentDigest, values["operation_result_digest"]).value
        ),
        "ordered_fulfilled_products": [
            _coordinator_fulfilled_product_wire(item) for item in products
        ],
        "outcome": values["outcome"],
        "package_head_reread_evidence": _coordinator_head_reread_wire(head),
        "publication_receipt": (
            None
            if publication is None
            else _coordinator_publication_receipt_wire(publication)
        ),
        "publication_receipt_digest": (
            None
            if values["publication_receipt_digest"] is None
            else cast(ContentDigest, values["publication_receipt_digest"]).value
        ),
        "publication_request_digest": (
            None
            if values["publication_request_digest"] is None
            else cast(ContentDigest, values["publication_request_digest"]).value
        ),
        "result_coordinate": _coordinator_coordinate_wire(
            cast(SemanticValueCoordinate, values["result_coordinate"])
        ),
        "result_head_digest": cast(ContentDigest, values["result_head_digest"]).value,
        "result_head_revision": values["result_head_revision"],
        "session_event_reread_evidence": _coordinator_session_event_reread_wire(event),
        "session_event_reread_evidence_digest": cast(
            ContentDigest, values["session_event_reread_evidence_digest"]
        ).value,
        "session_fanout_receipt": _coordinator_session_fanout_wire(fanout),
        "session_fanout_receipt_digest": cast(
            ContentDigest, values["session_fanout_receipt_digest"]
        ).value,
        "session_source_evidence": _coordinator_session_source_wire(source),
        "session_source_evidence_digest": cast(
            ContentDigest, values["session_source_evidence_digest"]
        ).value,
    }


def _create_coordinator_fulfilled_dependency_product_v2(
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    consumer_binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
    target_binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
    target_resolution: WorkspaceDependencyTargetResolution,
    head_h1: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    head_h2: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    consumed_body_coordinate: SemanticValueCoordinate,
) -> WorkspaceFulfilledDependencyProductV3:
    """Fast construction after the nominal coordinator validated one admitted plan.

    Public constructors/codecs retain full contextual revalidation. This helper
    only removes repeated full-plan traversal from the already admitted C3 loop.
    """

    values = {
        "graph_digest": plan_result.graph.graph_digest,
        "consumer_node_digest": consumer_binding.node_digest,
        "target_node_digest": target_binding.node_digest,
        "target_resolution": target_resolution,
        "head_h1_reread_evidence_digest": head_h1.reread_evidence_digest,
        "head_h2_reread_evidence_digest": head_h2.reread_evidence_digest,
        "result_head_revision": head_h1.materialization_head_revision,
        "result_head_digest": head_h1.materialization_head_digest,
        "result_execution_input_closure_digest": head_h1.execution_input_closure_digest,
        "consumed_body_coordinate": consumed_body_coordinate,
    }
    if (
        target_resolution not in consumer_binding.incoming_target_resolutions
        or head_h1.package != target_binding.package
        or head_h2.package != target_binding.package
        or head_h1.source_identity_digest
        != target_binding.package_entry.source_identity_digest
        or head_h2.source_identity_digest
        != target_binding.package_entry.source_identity_digest
        or head_h1.code_intent_digest != target_binding.code_intent.intent_digest
        or head_h2.code_intent_digest != target_binding.code_intent.intent_digest
        or head_h1.code_match_digest != target_binding.code_match.match_digest
        or head_h1.planning_input_digest != target_binding.planning_input_digest
        or head_h2.code_match_digest != target_binding.code_match.match_digest
        or head_h2.planning_input_digest != target_binding.planning_input_digest
        or head_h1.observation_role != "dependency_h1"
        or head_h2.observation_role != "dependency_h2"
        or head_h1.package != head_h2.package
        or head_h1.result_coordinate != consumed_body_coordinate
        or head_h1.result_coordinate != head_h2.result_coordinate
        or head_h1.materialization_head_revision
        != head_h2.materialization_head_revision
        or head_h1.materialization_head_digest != head_h2.materialization_head_digest
        or head_h1.canonical_head_wire_digest != head_h2.canonical_head_wire_digest
        or head_h1.execution_input_closure_digest
        != head_h2.execution_input_closure_digest
        or consumed_body_coordinate.role != target_resolution.required_result_role
        or consumed_body_coordinate.contract
        != target_resolution.result_product_contract
    ):
        raise ContractViolation("coordinator fulfilled product differs from bindings")
    payload = {
        "consumed_body_coordinate": _coordinator_coordinate_wire(
            consumed_body_coordinate
        ),
        "consumer_node_digest": consumer_binding.node_digest.value,
        "graph_digest": plan_result.graph.graph_digest.value,
        "head_h1_reread_evidence_digest": head_h1.reread_evidence_digest.value,
        "head_h2_reread_evidence_digest": head_h2.reread_evidence_digest.value,
        "result_execution_input_closure_digest": head_h1.execution_input_closure_digest.value,
        "result_head_digest": head_h1.materialization_head_digest.value,
        "result_head_revision": head_h1.materialization_head_revision,
        "target_node_digest": target_binding.node_digest.value,
        "target_resolution": _coordinator_target_resolution_wire(target_resolution),
    }
    return _frozen_value(
        WorkspaceFulfilledDependencyProductV3,
        head_h1_reread_evidence=head_h1,
        head_h2_reread_evidence=head_h2,
        **values,
        fulfillment_digest=_digest(WORKSPACE_FULFILLED_DEPENDENCY_PRODUCT_V3, payload),
    )


def _create_coordinator_node_result_evidence_v2(
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
    outcome: str,
    execution_input_closure_digest: ContentDigest,
    ordered_fulfilled_products: tuple[WorkspaceFulfilledDependencyProductV3, ...],
    package_head_reread_evidence: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    publication_receipt: WorkspaceSemanticMaterializationPublicationReceiptV3 | None,
    session_source_evidence: WorkspaceMaterializationSessionSourceEvidenceV3,
    session_event_reread_evidence: WorkspaceMaterializationSessionEventRereadEvidenceV3,
    session_fanout_receipt: WorkspaceMaterializationSessionFanoutReceiptV3,
) -> tuple[WorkspaceSemanticMaterializationNodeResultEvidenceV3, dict[str, object]]:
    """Construct one node result without recursively validating the whole plan."""

    head = package_head_reread_evidence
    values = {
        "graph_digest": plan_result.graph.graph_digest,
        "execution_binding_digest": plan_result.graph_execution_binding.binding_digest,
        "node_digest": binding.node_digest,
        "outcome": outcome,
        "execution_input_closure_digest": execution_input_closure_digest,
        "ordered_fulfilled_products": ordered_fulfilled_products,
        "result_head_revision": head.materialization_head_revision,
        "result_head_digest": head.materialization_head_digest,
        "result_coordinate": head.result_coordinate,
        "package_head_reread_evidence": head,
        "publication_receipt": publication_receipt,
        "session_source_evidence": session_source_evidence,
        "session_event_reread_evidence": session_event_reread_evidence,
        "session_fanout_receipt": session_fanout_receipt,
        "session_source_evidence_digest": session_source_evidence.source_evidence_digest,
        "session_event_reread_evidence_digest": session_event_reread_evidence.reread_evidence_digest,
        "operation_result_digest": (
            None
            if publication_receipt is None
            else publication_receipt.request.operation_result_digest
        ),
        "publication_request_digest": (
            None
            if publication_receipt is None
            else publication_receipt.request.request_digest
        ),
        "publication_receipt_digest": (
            None if publication_receipt is None else publication_receipt.receipt_digest
        ),
        "session_fanout_receipt_digest": session_fanout_receipt.receipt_digest,
    }
    if (
        tuple(item.target_resolution for item in ordered_fulfilled_products)
        != binding.incoming_target_resolutions
        or any(
            item.consumer_node_digest != binding.node_digest
            for item in ordered_fulfilled_products
        )
        or head.package != binding.package
        or head.source_identity_digest != binding.package_entry.source_identity_digest
        or head.code_intent_digest != binding.code_intent.intent_digest
        or head.code_match_digest != binding.code_match.match_digest
        or head.planning_input_digest != binding.planning_input_digest
        or (head.result_coordinate.role, head.result_coordinate.contract)
        not in {(item.role, item.contract) for item in binding.required_result_products}
    ):
        raise ContractViolation("coordinator node result differs from binding")
    payload = _coordinator_node_result_payload(values)
    result = _frozen_value(
        WorkspaceSemanticMaterializationNodeResultEvidenceV3,
        **values,
        node_result_digest=_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_RESULT_EVIDENCE_V3, payload
        ),
    )
    return (
        result,
        {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_RESULT_EVIDENCE_V3,
            **payload,
            "node_result_digest": result.node_result_digest.value,
        },
    )


def _create_coordinator_graph_result_v2(
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    ordered_node_results: tuple[
        WorkspaceSemanticMaterializationNodeResultEvidenceV3, ...
    ],
    ordered_node_wires: tuple[dict[str, object], ...],
    ordered_fulfilled_products: tuple[WorkspaceFulfilledDependencyProductV3, ...],
    counter_entries: tuple[WorkspaceSemanticMaterializationResultCounterEntryV2, ...],
) -> WorkspaceSemanticMaterializationGraphResultV3:
    """Close a successful exact traversal without N repeated plan validations."""

    if tuple(item.node_digest for item in ordered_node_results) != tuple(
        item.node_digest
        for item in plan_result.graph_execution_binding.ordered_node_bindings
    ):
        raise ContractViolation("coordinator result lacks complete execution order")
    if tuple(
        product.fulfillment_digest
        for item in ordered_node_results
        for product in item.ordered_fulfilled_products
    ) != tuple(item.fulfillment_digest for item in ordered_fulfilled_products):
        raise ContractViolation("coordinator result fulfillment closure differs")
    values = {
        "graph_digest": plan_result.graph.graph_digest,
        "execution_binding_digest": plan_result.graph_execution_binding.binding_digest,
        "status": "succeeded",
        "ordered_node_results": ordered_node_results,
        "terminal_failure": None,
        "ordered_fulfilled_products": ordered_fulfilled_products,
        "counter_entries": counter_entries,
    }
    if len(ordered_node_wires) != len(ordered_node_results) or any(
        wire.get("node_result_digest") != result.node_result_digest.value
        for result, wire in zip(ordered_node_results, ordered_node_wires, strict=True)
    ):
        raise ContractViolation("coordinator node result wires differ")
    payload = {
        "counter_entries": [
            {"counter": item.counter, "value": item.value} for item in counter_entries
        ],
        "execution_binding_digest": plan_result.graph_execution_binding.binding_digest.value,
        "graph_digest": plan_result.graph.graph_digest.value,
        "ordered_fulfilled_products": [
            _coordinator_fulfilled_product_wire(item)
            for item in ordered_fulfilled_products
        ],
        "ordered_node_results": list(ordered_node_wires),
        "status": "succeeded",
        "terminal_failure": None,
    }
    result = _frozen_value(
        WorkspaceSemanticMaterializationGraphResultV3,
        **values,
        result_digest=_digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3, payload
        ),
    )
    return result


__all__ = [
    "WORKSPACE_DEPENDENCY_TARGET_RESOLUTION",
    "WORKSPACE_FULFILLED_DEPENDENCY_PRODUCT_V3",
    "WORKSPACE_MATERIALIZATION_PLANNING_COUNTERS",
    "WORKSPACE_MATERIALIZATION_PLANNING_TIMING_STAGES",
    "WORKSPACE_OBSERVED_HEAD_CLASSIFICATIONS",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_FAILURE_EVIDENCE_ENTRY_V2",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EDGE",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_EXECUTION_BINDING",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_NODE",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_ADMISSION",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_PLAN_RESULT",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_OBSERVATION_ROLES_V2",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_LOCAL_ROOT_ASSOCIATION",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_EXECUTION_BINDING",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_NODE_RESULT_EVIDENCE_V3",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_FAILURE_V3",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_TERMINAL_MATRIX_V2",
    "WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION",
    "WORKSPACE_SEMANTIC_PLANNED_DEPENDENCY_INPUT",
    "WORKSPACE_SEMANTIC_PLANNING_DEMAND_CLOSURE",
    "WorkspaceDependencyTargetResolution",
    "WorkspaceFulfilledDependencyProductV3",
    "WorkspaceMaterializationPlanningCounterEntry",
    "WorkspaceMaterializationPlanningTimingEntry",
    "WorkspaceSemanticMaterializationFailureEvidenceEntryV2",
    "WorkspaceSemanticMaterializationGraph",
    "WorkspaceSemanticMaterializationGraphEdge",
    "WorkspaceSemanticMaterializationGraphExecutionBinding",
    "WorkspaceSemanticMaterializationGraphExecutionMetrics",
    "WorkspaceSemanticMaterializationGraphNode",
    "WorkspaceSemanticMaterializationGraphPlanAdmission",
    "WorkspaceSemanticMaterializationGraphPlanResult",
    "WorkspaceSemanticMaterializationGraphResultV3",
    "WorkspaceSemanticMaterializationLocalRootAssociation",
    "WorkspaceSemanticMaterializationNodeExecutionBinding",
    "WorkspaceSemanticMaterializationNodeResultEvidenceV3",
    "WorkspaceSemanticMaterializationResultCounterEntryV2",
    "WorkspaceSemanticMaterializationTerminalEvidenceContextV3",
    "WorkspaceSemanticMaterializationTerminalFailureV3",
    "WorkspaceSemanticPackageHeadObservation",
    "WorkspaceSemanticPlannedDependencyInput",
    "WorkspaceSemanticPlanningDemandClosure",
]
