"""Original planning completion bodies; no product admission or transfer authority."""

from copy import deepcopy

from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    SemanticValueCoordinate,
    TerminalStatus,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
)
from aware_code_semantic_contract_runtime.runtime import (
    ExecutionCompletion,
    SemanticBody,
)

from . import direct_epoch_tracking as hooks
from . import planning_execution as execution


def _prepare_completion(stage, completion):
    runtime = stage.record.expected.runtime
    if type(completion) is not ExecutionCompletion or not runtime.owns_completion(
        completion
    ):
        raise ContractViolation("original planning runtime completion required")
    snapshot = runtime.snapshot_completion(completion)
    if (
        snapshot.invocation_digest != stage.invocation_digest
        or snapshot.profile_digest != stage.record.expected.profile.digest
        or snapshot.result.status is not TerminalStatus.DELTA
        or snapshot.result.transition is None
    ):
        raise ContractViolation("planning completion invocation/profile/status differs")
    coordinate = snapshot.result.transition.result
    if coordinate.contract != DependencyPlanningInputCodec.contract:
        raise ContractViolation("planning completion result contract differs")
    expected_roles = set(stage.record.expected.profile.terminal_output_roles)
    if {o.output.role for o in snapshot.result.outputs} != expected_roles:
        raise ContractViolation("planning completion output set differs")
    value = DependencyPlanningInputCodec().decode(
        snapshot.body_for(coordinate).canonical_body
    )
    execution._planning_body(stage.record, value)
    return snapshot, value


def _original_retention(stage):
    lifecycle = selected._registration_state(
        stage.record.registration
    ).execution_lifecycle
    execution._origin(lifecycle.origin)
    retained = execution._ORIGINS[lifecycle.origin][4].get(stage.context)
    if lifecycle.terminal_mode == "runtime_completion":
        if (
            retained is None
            or retained[0] is not stage
            or retained[1] is not stage.completion
            or retained[2] is not stage.completion_snapshot
        ):
            raise ContractViolation("original planning completion association differs")
    elif (
        retained is not None
        or stage.completion is not None
        or stage.completion_snapshot is not None
    ):
        raise ContractViolation("owner-value stage cannot acquire completion evidence")
    return retained


def _validate_retained_completion(stage):
    if _original_retention(stage) is None:
        return None
    snapshot, value = _prepare_completion(stage, stage.completion)
    if snapshot != stage.completion_snapshot or value != stage.result:
        raise ContractViolation("retained planning completion changed")
    return snapshot


def retained_planning_output_body(origin, context, coordinate):
    """Read one declared output from original stage lineage; bytes grant no authority."""
    if type(coordinate) is not SemanticValueCoordinate:
        raise TypeError("exact planning output coordinate required")
    coordinate.__post_init__()
    host, registration, stages = execution._origin(origin)
    stage = stages.get(context)
    if stage is None:
        raise ContractViolation("original planning stage unavailable")
    execution._check_stage(host, registration, stages, stage, status="returned")
    snapshot = _validate_retained_completion(stage)
    if snapshot is None or coordinate not in tuple(
        o.output for o in snapshot.result.outputs
    ):
        raise ContractViolation(
            "coordinate is not an original declared planning output"
        )
    body = snapshot.body_for(coordinate)
    completion = stage.completion
    binding = stage.record.reservation.binding
    with hooks._guard(binding) as guard:
        hooks._original(binding, host, guard)
        _original_retention(stage)
        if (
            stages.get(context) is not stage
            or stage.status != "returned"
            or stage.completion is not completion
            or stage.completion_snapshot != snapshot
            or not stage.record.expected.runtime.owns_completion(completion)
        ):
            raise ContractViolation("planning output changed during read")
    return SemanticBody(deepcopy(body.coordinate), body.canonical_body)
