from __future__ import annotations

import asyncio
import copy
import json
import pickle
import statistics
import time
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    SemanticBody,
    SemanticContractRef,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_local_service_runtime import InMemoryLocalOperationalStateStore
from aware_workspace_runtime.materialization_operation import (
    WorkspaceMaterializeExecutionInputCompositionAdmission,
    WorkspaceMaterializeExecutionPlan,
    WorkspaceMaterializeOperation,
    WorkspaceMaterializeOperationAdmission,
    WorkspaceMaterializeOperationError,
    WorkspaceMaterializeOperationRequest,
    WorkspaceMaterializeOperationStageError,
    _select_graph_result_coordinate,
    admit_workspace_materialize_execution_input_composition,
    admit_workspace_materialize_operation,
    derive_workspace_materialize_execution_input_closure_digest,
)
from aware_workspace_runtime.materialization_session import (
    WorkspaceMaterializationSessionAuthorityGrade,
    WorkspaceMaterializationSessionBaselineGrade,
    WorkspaceMaterializationSessionJournal,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    DirectoryWorkspaceSemanticMaterializationBodyStore,
    WorkspaceSemanticMaterializationPublisher,
)
from test_semantic_materialization_publication import (
    OUTPUT,
    RESULT,
    _BodyStore,
    _invocation,
    _Provider,
    _runtime,
)


def _digest(marker: str) -> str:
    return ContentDigest.of_bytes(marker.encode()).value


class _Resolver:
    implementation_ref = "test-plan-resolver"
    implementation_digest = _digest("resolver")

    def __init__(self, plan: WorkspaceMaterializeExecutionPlan) -> None:
        self.plan = plan
        self.profile_ref = plan.profile_ref
        self.profile_digest = plan.profile_digest
        self.calls = 0

    async def resolve(
        self, admission: WorkspaceMaterializeOperationAdmission
    ) -> WorkspaceMaterializeExecutionPlan:
        admission._assert_intact()
        self.calls += 1
        return self.plan


class _FailResolver(_Resolver):
    async def resolve(
        self, admission: WorkspaceMaterializeOperationAdmission
    ) -> WorkspaceMaterializeExecutionPlan:
        admission._assert_intact()
        raise RuntimeError("injected plan failure")


class _FailExecutionProvider(_Provider):
    async def derive(self, invocation):
        _ = invocation
        raise RuntimeError("injected execution failure")


class _CountingProvider(_Provider):
    def __init__(self) -> None:
        self.calls = 0

    async def derive(self, invocation):
        self.calls += 1
        return await super().derive(invocation)


class _Authority:
    operation_ref = "workspace-operation:materialize"
    operation_digest = _digest("operation")

    def __init__(
        self,
        request_digest: str,
        *,
        grade: WorkspaceMaterializationSessionAuthorityGrade = (
            WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL
        ),
    ) -> None:
        self._request_digest = request_digest
        self._grade = grade

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade:
        return self._grade

    def admits(self, request: WorkspaceMaterializeOperationRequest) -> bool:
        return request.request_digest == self._request_digest

    def permitted_package_refs_for(
        self, request: WorkspaceMaterializeOperationRequest
    ) -> tuple[str, ...]:
        assert request.request_digest == self._request_digest
        return (request.package_ref,)


class _ExecutionInputAuthority:
    def __init__(
        self,
        plan: WorkspaceMaterializeExecutionPlan,
        resolver: _Resolver,
        *,
        grade: WorkspaceMaterializationSessionAuthorityGrade,
    ) -> None:
        self._expected = {
            "package_ref": plan.package_ref,
            "package_kind": plan.package_kind,
            "manifest_digest": plan.manifest_digest,
            "source_authority_ref": plan.source_authority_ref,
            "source_authority_digest": plan.source_authority_digest,
            "operation_ref": plan.operation_ref,
            "operation_digest": plan.operation_digest,
            "profile_ref": plan.profile_ref,
            "profile_digest": plan.profile_digest,
            "plan_resolver_ref": resolver.implementation_ref,
            "plan_resolver_digest": resolver.implementation_digest,
            "execution_input_closure_digest": (
                derive_workspace_materialize_execution_input_closure_digest(
                    plan.input_bodies
                )
            ),
        }
        self._grade = grade

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade:
        return self._grade

    def admits_composition(self, **values: str) -> bool:
        return values == self._expected


class _ForeignGradeExecutionInputAuthority(_ExecutionInputAuthority):
    @property
    def authority_grade(self) -> str:  # type: ignore[override]
        return "local_operational"


def _values():
    runtime = _runtime()
    invocation, bodies = _invocation("one")
    plan = WorkspaceMaterializeExecutionPlan.create(
        source_authority_ref="workspace-source:test",
        source_authority_digest=_digest("source"),
        operation_ref=_Authority.operation_ref,
        operation_digest=_Authority.operation_digest,
        invocation=invocation,
        input_bodies=bodies,
    )
    return runtime, plan


def _request(
    plan: WorkspaceMaterializeExecutionPlan,
    resolver: _Resolver,
    *,
    execution_input_closure_digest: str | None = None,
    materialization_revision: int = 0,
    session_revision: int = 0,
    session_cursor: int = 0,
    predecessor_event_digest: str | None = None,
) -> WorkspaceMaterializeOperationRequest:
    return WorkspaceMaterializeOperationRequest.create(
        workspace_session_ref="workspace-session:test",
        epoch="session-epoch:test",
        participant_ref="participant:test",
        actor_ref="actor:test",
        workflow_session_ref="workflow-session:test",
        materialization_attempt_ref="attempt:test",
        branch_baseline_ref="workspace-source-head:test",
        branch_baseline_digest=_digest("baseline"),
        branch_baseline_grade=(
            WorkspaceMaterializationSessionBaselineGrade.SOURCE_HEAD_LOCAL_OPERATIONAL.value
        ),
        package_ref=plan.package_ref,
        package_kind=plan.package_kind,
        manifest_digest=plan.manifest_digest,
        source_authority_ref=plan.source_authority_ref,
        source_authority_digest=plan.source_authority_digest,
        operation_ref=plan.operation_ref,
        operation_digest=plan.operation_digest,
        profile_ref=plan.profile_ref,
        profile_digest=plan.profile_digest,
        plan_resolver_ref=resolver.implementation_ref,
        plan_resolver_digest=resolver.implementation_digest,
        execution_input_closure_digest=(
            derive_workspace_materialize_execution_input_closure_digest(
                plan.input_bodies
            )
            if execution_input_closure_digest is None
            else execution_input_closure_digest
        ),
        expected_materialization_head_revision=materialization_revision,
        expected_session_head_revision=session_revision,
        expected_session_cursor=session_cursor,
        expected_predecessor_event_digest=predecessor_event_digest,
    )


def _admission(
    request: WorkspaceMaterializeOperationRequest,
    plan: WorkspaceMaterializeExecutionPlan,
    resolver: _Resolver,
    *,
    grade: WorkspaceMaterializationSessionAuthorityGrade = (
        WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL
    ),
) -> WorkspaceMaterializeOperationAdmission:
    execution_input_admission = _execution_input_admission(
        plan,
        resolver,
        grade=grade,
    )
    return admit_workspace_materialize_operation(
        request=request,
        operation_authority=_Authority(request.request_digest, grade=grade),
        execution_input_admission=execution_input_admission,
    )


def _execution_input_admission(
    plan: WorkspaceMaterializeExecutionPlan,
    resolver: _Resolver,
    *,
    grade: WorkspaceMaterializationSessionAuthorityGrade = (
        WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL
    ),
) -> WorkspaceMaterializeExecutionInputCompositionAdmission:
    return admit_workspace_materialize_execution_input_composition(
        package_ref=plan.package_ref,
        package_kind=plan.package_kind,
        manifest_digest=plan.manifest_digest,
        source_authority_ref=plan.source_authority_ref,
        source_authority_digest=plan.source_authority_digest,
        operation_ref=plan.operation_ref,
        operation_digest=plan.operation_digest,
        profile_ref=plan.profile_ref,
        profile_digest=plan.profile_digest,
        plan_resolver_ref=resolver.implementation_ref,
        plan_resolver_digest=resolver.implementation_digest,
        input_bodies=plan.input_bodies,
        composition_authority=_ExecutionInputAuthority(
            plan,
            resolver,
            grade=grade,
        ),
    )


def _semantic_body(
    template: SemanticBody,
    *,
    canonical_body: bytes | None = None,
    role: str | None = None,
    contract: SemanticContractRef | None = None,
    value_ref: str | None = None,
) -> SemanticBody:
    body = template.canonical_body if canonical_body is None else canonical_body
    coordinate = SemanticValueCoordinate(
        role=template.coordinate.role if role is None else role,
        contract=template.coordinate.contract if contract is None else contract,
        value_ref=(template.coordinate.value_ref if value_ref is None else value_ref),
        digest=ContentDigest.of_bytes(body),
        size_bytes=len(body),
    )
    return SemanticBody(coordinate, body)


def _ordered(*bodies: SemanticBody) -> tuple[SemanticBody, ...]:
    return tuple(
        sorted(
            bodies,
            key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
        )
    )


def _p95(values: list[float]) -> float:
    return statistics.quantiles(values, n=20, method="inclusive")[18]


def _operation(runtime, resolver, state=None, body_store=None):
    state = state or InMemoryLocalOperationalStateStore()
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=state,
        body_store=body_store or _BodyStore(),
    )
    journal = WorkspaceMaterializationSessionJournal(
        state_store=state,
        package_head_resolver=publisher.read_head,
    )
    return (
        WorkspaceMaterializeOperation(
            runtime=runtime,
            plan_resolver=resolver,
            publisher=publisher,
            session_journal=journal,
        ),
        publisher,
        journal,
    )


def test_operation_executes_publishes_fanout_and_exactly_retries() -> None:
    runtime, plan = _values()
    resolver = _Resolver(plan)
    request = _request(plan, resolver)
    operation, publisher, journal = _operation(runtime, resolver)
    admission = _admission(request, plan, resolver)

    first = asyncio.run(operation.execute(admission))
    retry = asyncio.run(operation.execute(admission))

    assert first.publication.receipt == retry.publication.receipt
    assert first.fanout.event == retry.fanout.event
    assert first.fanout.head == retry.fanout.head
    assert first.fanout.receipt.head_advanced is True
    assert retry.fanout.receipt.head_advanced is False
    assert first.plan_digest == plan.plan_digest
    assert first.result_digest == first.publication.receipt.head.result_digest
    assert first.publication.metrics.head_cas_count == 1
    assert retry.publication.metrics.head_cas_count == 0
    assert first.fanout.metrics.head_state_cas_count == 1
    assert retry.fanout.metrics.head_state_cas_count == 0
    assert retry.fanout.metrics.event_state_reuse_count == 1
    assert resolver.calls == 2
    assert publisher.read_head(plan.package_ref) is not None
    assert journal.read_head(request.workspace_session_ref) is not None


def test_graph_result_selection_uses_exact_demanded_role_and_contract() -> None:
    runtime, _plan = _values()
    invocation, bodies = _invocation("one")
    completion = asyncio.run(runtime.execute(invocation, bodies))
    snapshot = runtime.snapshot_completion(completion)
    required_output = CodeSemanticRequiredResultProduct.create(
        role="output", contract=OUTPUT
    )
    selected = _select_graph_result_coordinate(
        required_products=(required_output,),
        snapshot=snapshot,
    )
    assert selected == snapshot.result.outputs[0].output
    assert selected != snapshot.result.transition.result

    required_state = CodeSemanticRequiredResultProduct.create(
        role="result", contract=RESULT
    )
    assert _select_graph_result_coordinate(
        required_products=(required_state,), snapshot=snapshot
    ) == snapshot.result.transition.result

    wrong_contract = CodeSemanticRequiredResultProduct.create(
        role="output",
        contract=SemanticContractRef(
            "test.output.foreign",
            "1",
            ContentDigest.of_bytes(b"test.output.foreign.v1"),
        ),
    )
    with pytest.raises(WorkspaceMaterializeOperationError, match="did not produce"):
        _select_graph_result_coordinate(
            required_products=(wrong_contract,), snapshot=snapshot
        )
    for closure in ((), (required_output, required_state)):
        with pytest.raises(WorkspaceMaterializeOperationError, match="requires one"):
            _select_graph_result_coordinate(
                required_products=closure, snapshot=snapshot
            )


def test_request_codec_admission_and_composition_poisons_fail_closed() -> None:
    runtime, plan = _values()
    resolver = _Resolver(plan)
    request = _request(plan, resolver)
    assert (
        WorkspaceMaterializeOperationRequest.from_json_bytes(request.to_json_bytes())
        == request
    )
    payload = json.loads(request.to_json_bytes())
    payload["expected_session_cursor"] = True
    with pytest.raises(WorkspaceMaterializeOperationError, match="integer type"):
        WorkspaceMaterializeOperationRequest.from_json_bytes(
            canonical_json_bytes(payload)
        )

    forged = object.__new__(WorkspaceMaterializeOperationAdmission)
    with pytest.raises(WorkspaceMaterializeOperationError, match="not registered"):
        forged._assert_intact()
    with pytest.raises(TypeError, match="not serializable"):
        copy.copy(_admission(request, plan, resolver))

    operation, _, _ = _operation(runtime, resolver)
    admission = _admission(request, plan, resolver)
    resolver.implementation_digest = _digest("substituted-resolver")
    with pytest.raises(WorkspaceMaterializeOperationStageError) as failure:
        asyncio.run(operation.execute(admission))
    assert failure.value.stage == "plan"
    assert "substituted" in str(failure.value.cause)


def test_execution_input_closure_is_strict_complete_and_context_free() -> None:
    _, plan = _values()
    source = plan.input_bodies[0]
    reconstructed = SemanticBody(source.coordinate, bytes(source.canonical_body))
    changed_body = _semantic_body(source, canonical_body=b'{"source":"two"}')
    changed_role = _semantic_body(source, role="source-alternate")
    changed_contract = _semantic_body(
        source,
        contract=replace(source.coordinate.contract, key="test.source.alternate"),
    )
    changed_ref = _semantic_body(source, value_ref="source-alternate")
    extra = _semantic_body(source, value_ref="source-extra")

    original_digest = derive_workspace_materialize_execution_input_closure_digest(
        (source,)
    )
    assert (
        derive_workspace_materialize_execution_input_closure_digest((reconstructed,))
        == original_digest
    )
    assert derive_workspace_materialize_execution_input_closure_digest(
        ()
    ) == derive_workspace_materialize_execution_input_closure_digest(())
    for closure in (
        (),
        (changed_body,),
        (changed_role,),
        (changed_contract,),
        (changed_ref,),
        _ordered(source, extra),
    ):
        assert (
            derive_workspace_materialize_execution_input_closure_digest(closure)
            != original_digest
        )

    with pytest.raises(TypeError, match="exact tuple"):
        derive_workspace_materialize_execution_input_closure_digest([source])  # type: ignore[arg-type]

    class _ForeignBody(SemanticBody):
        pass

    with pytest.raises(TypeError, match="exact SemanticBody"):
        derive_workspace_materialize_execution_input_closure_digest(
            (_ForeignBody(source.coordinate, source.canonical_body),)
        )

    incomplete = object.__new__(SemanticBody)
    with pytest.raises((AttributeError, TypeError)):
        derive_workspace_materialize_execution_input_closure_digest((incomplete,))

    with pytest.raises(WorkspaceMaterializeOperationError, match="unique"):
        derive_workspace_materialize_execution_input_closure_digest((source, source))

    ordered_pair = _ordered(source, extra)
    with pytest.raises(WorkspaceMaterializeOperationError, match="canonical"):
        derive_workspace_materialize_execution_input_closure_digest(
            tuple(reversed(ordered_pair))
        )

    digest_mismatch = object.__new__(SemanticBody)
    object.__setattr__(digest_mismatch, "coordinate", source.coordinate)
    object.__setattr__(digest_mismatch, "canonical_body", b"different")
    with pytest.raises(ValueError, match="digest differs"):
        derive_workspace_materialize_execution_input_closure_digest((digest_mismatch,))

    wrong_size_coordinate = replace(
        source.coordinate,
        size_bytes=source.coordinate.size_bytes + 1,
    )
    size_mismatch = object.__new__(SemanticBody)
    object.__setattr__(size_mismatch, "coordinate", wrong_size_coordinate)
    object.__setattr__(size_mismatch, "canonical_body", source.canonical_body)
    with pytest.raises(ValueError, match="size differs"):
        derive_workspace_materialize_execution_input_closure_digest((size_mismatch,))


def test_request_v1_and_canonical_scalar_substitutions_fail_strict_decoding() -> None:
    _, plan = _values()
    resolver = _Resolver(plan)
    request = _request(plan, resolver)

    old = json.loads(request.to_json_bytes())
    old["contract"] = "aware.workspace.semantic-materialize-operation-request.v1"
    old.pop("execution_input_closure_digest")
    with pytest.raises(WorkspaceMaterializeOperationError):
        WorkspaceMaterializeOperationRequest.from_json_bytes(canonical_json_bytes(old))

    for field, value in (
        ("expected_materialization_head_revision", False),
        ("expected_session_head_revision", True),
        ("expected_session_cursor", False),
    ):
        poison = json.loads(request.to_json_bytes())
        poison[field] = value
        with pytest.raises(WorkspaceMaterializeOperationError, match="integer type"):
            WorkspaceMaterializeOperationRequest.from_json_bytes(
                canonical_json_bytes(poison)
            )


def test_nominal_execution_input_admission_rejects_forgery_and_substitution() -> None:
    _, plan = _values()
    resolver = _Resolver(plan)
    admission = _execution_input_admission(plan, resolver)

    with pytest.raises(TypeError, match="not serializable"):
        copy.copy(admission)
    with pytest.raises(TypeError, match="not serializable"):
        copy.deepcopy(admission)
    with pytest.raises(TypeError, match="not serializable"):
        pickle.dumps(admission)
    forged = object.__new__(WorkspaceMaterializeExecutionInputCompositionAdmission)
    with pytest.raises(WorkspaceMaterializeOperationError, match="not registered"):
        forged._assert_intact()
    with pytest.raises(TypeError):

        class _ForeignAdmission(WorkspaceMaterializeExecutionInputCompositionAdmission):
            pass

    base = {
        "package_ref": plan.package_ref,
        "package_kind": plan.package_kind,
        "manifest_digest": plan.manifest_digest,
        "source_authority_ref": plan.source_authority_ref,
        "source_authority_digest": plan.source_authority_digest,
        "operation_ref": plan.operation_ref,
        "operation_digest": plan.operation_digest,
        "profile_ref": plan.profile_ref,
        "profile_digest": plan.profile_digest,
        "plan_resolver_ref": resolver.implementation_ref,
        "plan_resolver_digest": resolver.implementation_digest,
    }
    substitutions = {
        "package_ref": "aware.sdk.foreign",
        "package_kind": "service",
        "manifest_digest": _digest("foreign-manifest"),
        "source_authority_ref": "workspace-source:foreign",
        "source_authority_digest": _digest("foreign-source"),
        "operation_ref": "workspace-operation:foreign",
        "operation_digest": _digest("foreign-operation"),
        "profile_ref": "foreign-profile",
        "profile_digest": _digest("foreign-profile"),
        "plan_resolver_ref": "foreign-resolver",
        "plan_resolver_digest": _digest("foreign-resolver"),
    }
    authority = _ExecutionInputAuthority(
        plan,
        resolver,
        grade=WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL,
    )
    for field, substitution in substitutions.items():
        values = dict(base)
        values[field] = substitution
        with pytest.raises(
            WorkspaceMaterializeOperationError,
            match="composition was not admitted",
        ):
            admit_workspace_materialize_execution_input_composition(
                **values,
                input_bodies=plan.input_bodies,
                composition_authority=authority,
            )

    with pytest.raises(
        WorkspaceMaterializeOperationError, match="grade is not nominal"
    ):
        admit_workspace_materialize_execution_input_composition(
            **base,
            input_bodies=plan.input_bodies,
            composition_authority=_ForeignGradeExecutionInputAuthority(
                plan,
                resolver,
                grade=WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL,
            ),
        )

    request_with_foreign_closure = _request(
        plan,
        resolver,
        execution_input_closure_digest=_digest("foreign-closure"),
    )
    with pytest.raises(
        WorkspaceMaterializeOperationError,
        match="execution input admission differs from request",
    ):
        admit_workspace_materialize_operation(
            request=request_with_foreign_closure,
            operation_authority=_Authority(request_with_foreign_closure.request_digest),
            execution_input_admission=admission,
        )


def test_same_admission_rejects_different_coherent_closure_before_code() -> None:
    runtime, admitted_plan = _values()
    admitted_body = admitted_plan.input_bodies[0]
    changed_body = _semantic_body(
        admitted_body,
        canonical_body=b'{"source":"substituted"}',
        value_ref="source-substituted",
    )
    changed_invocation = replace(
        admitted_plan.invocation,
        invocation_ref="invocation-substituted",
        idempotency_key="invocation-substituted",
        inputs=(changed_body.coordinate,),
    )
    changed_plan = WorkspaceMaterializeExecutionPlan.create(
        source_authority_ref=admitted_plan.source_authority_ref,
        source_authority_digest=admitted_plan.source_authority_digest,
        operation_ref=admitted_plan.operation_ref,
        operation_digest=admitted_plan.operation_digest,
        invocation=changed_invocation,
        input_bodies=(changed_body,),
    )
    resolver = _Resolver(changed_plan)
    request = _request(admitted_plan, resolver)
    admission = _admission(request, admitted_plan, resolver)
    counting_provider = _CountingProvider()
    runtime._providers["test-provider"] = counting_provider  # pyright: ignore[reportPrivateUsage]
    operation, publisher, journal = _operation(runtime, resolver)

    with pytest.raises(WorkspaceMaterializeOperationStageError) as failure:
        asyncio.run(operation.execute(admission))

    assert failure.value.stage == "plan"
    assert "resolved execution input closure differs" in str(failure.value.cause)
    assert counting_provider.calls == 0
    assert publisher.read_head(admitted_plan.package_ref) is None
    assert journal.read_head(request.workspace_session_ref) is None


def test_execution_input_closure_derivation_performance_is_visible() -> None:
    _, plan = _values()
    source = plan.input_bodies[0]
    input_bodies = tuple(
        _semantic_body(source, value_ref=f"source-{index:04d}")
        for index in range(100)
    )

    for _ in range(2):
        derive_workspace_materialize_execution_input_closure_digest(input_bodies)
    samples_ms: list[float] = []
    for _ in range(10):
        started = time.perf_counter_ns()
        derive_workspace_materialize_execution_input_closure_digest(input_bodies)
        samples_ms.append((time.perf_counter_ns() - started) / 1_000_000)

    median_ms = statistics.median(samples_ms)
    p95_ms = _p95(samples_ms)
    assert median_ms < 5.0
    assert p95_ms < 10.0
    print(
        "workspace-execution-input-closure-benchmark",
        {
            "body_count": len(input_bodies),
            "body_bytes": sum(len(item.canonical_body) for item in input_bodies),
            "median_ms": round(median_ms, 6),
            "p95_ms": round(p95_ms, 6),
        },
    )


def test_plan_source_substitution_and_named_stage_failures_are_visible() -> None:
    runtime, plan = _values()
    substituted = WorkspaceMaterializeExecutionPlan.create(
        source_authority_ref="workspace-source:foreign",
        source_authority_digest=plan.source_authority_digest,
        operation_ref=plan.operation_ref,
        operation_digest=plan.operation_digest,
        invocation=plan.invocation,
        input_bodies=plan.input_bodies,
    )
    resolver = _Resolver(substituted)
    request = _request(plan, resolver)
    operation, _, _ = _operation(runtime, resolver)
    with pytest.raises(WorkspaceMaterializeOperationStageError) as failure:
        asyncio.run(operation.execute(_admission(request, plan, resolver)))
    assert failure.value.stage == "plan"
    assert failure.value.failure_code == "plan_failed"
    assert tuple(name for name, _ in failure.value.stage_timings_ns) == ("plan",)
    assert failure.value.total_ns >= sum(
        value for _, value in failure.value.stage_timings_ns
    )

    failing = _FailResolver(plan)
    failed_request = _request(plan, failing)
    failed_operation, _, _ = _operation(runtime, failing)
    with pytest.raises(WorkspaceMaterializeOperationStageError) as failure:
        asyncio.run(failed_operation.execute(_admission(failed_request, plan, failing)))
    assert failure.value.stage == "plan"
    assert "injected plan failure" in str(failure.value.cause)

    with pytest.raises(WorkspaceMaterializeOperationError, match="not an exact prefix"):
        WorkspaceMaterializeOperationStageError(
            "execution",
            RuntimeError("forged"),
            stage_timings_ns=(("execution", 1),),
            total_ns=1,
        )


def test_publication_and_fanout_interruptions_report_exact_stage() -> None:
    runtime, plan = _values()
    resolver = _Resolver(plan)
    runtime._providers["test-provider"] = _FailExecutionProvider()  # pyright: ignore[reportPrivateUsage]
    request = _request(plan, resolver)
    operation, _, _ = _operation(runtime, resolver)
    with pytest.raises(WorkspaceMaterializeOperationStageError) as failure:
        asyncio.run(operation.execute(_admission(request, plan, resolver)))
    assert failure.value.stage == "execution"
    assert tuple(name for name, _ in failure.value.stage_timings_ns) == (
        "plan",
        "execution",
    )

    runtime, plan = _values()
    resolver = _Resolver(plan)
    stale_publication = _request(plan, resolver, materialization_revision=3)
    operation, publisher, _ = _operation(runtime, resolver)
    with pytest.raises(WorkspaceMaterializeOperationStageError) as failure:
        asyncio.run(operation.execute(_admission(stale_publication, plan, resolver)))
    assert failure.value.stage == "publication"
    assert tuple(name for name, _ in failure.value.stage_timings_ns) == (
        "plan",
        "execution",
        "publication",
    )
    assert publisher.read_head(plan.package_ref) is None

    runtime, plan = _values()
    resolver = _Resolver(plan)
    stale_session = _request(
        plan,
        resolver,
        session_revision=1,
        session_cursor=1,
        predecessor_event_digest=_digest("foreign-event"),
    )
    operation, publisher, journal = _operation(runtime, resolver)
    with pytest.raises(WorkspaceMaterializeOperationStageError) as failure:
        asyncio.run(operation.execute(_admission(stale_session, plan, resolver)))
    assert failure.value.stage == "fanout"
    assert tuple(name for name, _ in failure.value.stage_timings_ns) == (
        "plan",
        "execution",
        "publication",
        "fanout",
    )
    assert publisher.read_head(plan.package_ref) is not None
    assert journal.read_head(stale_session.workspace_session_ref) is None


def test_shared_grade_and_sqlite_restart_preserve_exact_operation_state(
    tmp_path: Path,
) -> None:
    sqlite = pytest.importorskip("aware_local_service_state_sqlite")
    runtime, plan = _values()
    resolver = _Resolver(plan)
    request = _request(plan, resolver)
    database = tmp_path / "operation.sqlite3"
    state = sqlite.SqliteLocalOperationalStateStore(database)
    operation, publisher, journal = _operation(
        runtime,
        resolver,
        state=state,
        body_store=DirectoryWorkspaceSemanticMaterializationBodyStore(
            tmp_path / "bodies", repository_binding_ref="repository:test"
        ),
    )
    result = asyncio.run(
        operation.execute(
            _admission(
                request,
                plan,
                resolver,
                grade=(
                    WorkspaceMaterializationSessionAuthorityGrade.WORKSPACE_AUTHORIZED_SHARED
                ),
            )
        )
    )
    assert result.fanout.event.authority_grade == "workspace_authorized_shared"

    reconstructed_state = sqlite.SqliteLocalOperationalStateStore(database)
    reconstructed_publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=reconstructed_state,
        body_store=DirectoryWorkspaceSemanticMaterializationBodyStore(
            tmp_path / "bodies", repository_binding_ref="repository:test"
        ),
    )
    reconstructed_journal = WorkspaceMaterializationSessionJournal(
        state_store=reconstructed_state,
        package_head_resolver=reconstructed_publisher.read_head,
    )
    assert reconstructed_publisher.read_head(plan.package_ref) == publisher.read_head(
        plan.package_ref
    )
    assert reconstructed_journal.read_head(request.workspace_session_ref) == (
        journal.read_head(request.workspace_session_ref)
    )
