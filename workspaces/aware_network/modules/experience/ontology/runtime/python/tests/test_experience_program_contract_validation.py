from __future__ import annotations

from types import SimpleNamespace
from typing import Iterable, Mapping
from uuid import UUID, uuid4

import pytest

from aware_experience.program.language import (
    InvocationPlan,
    PlanCall,
    PlanCallArg,
    PlanExpectEventConfig,
    PlanInput,
    PlanInvoke,
    PlanIntentActionConfig,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanPortProjectionNodeContract,
    PlanPortProjectionNodeKey,
    PlanSymbolRef,
)
from aware_experience.program.service import _ReactivityProgramContractValidator
from aware_experience.program.runtime_invocation import (
    ProgramIntentRecord,
    ProgramApplyError,
    RuntimeInvocationPlanExecutor,
)


class _InvokerStub:
    async def invoke_function(self, _request):  # noqa: ANN001
        raise AssertionError("invoke_function should not be called in this test")


def _invoker_stub() -> object:
    return _InvokerStub()


def _index_stub() -> object:
    return SimpleNamespace()


class _ContractValidatorStub:
    def __init__(self) -> None:
        self.event_expectations: dict[UUID, bool] | None = None
        self.action_intents: list[tuple[UUID, UUID]] | None = None

    async def validate_event_action_contracts(
        self,
        *,
        event_expectations: Mapping[UUID, bool],
        action_intents: Iterable[tuple[UUID, UUID]],
    ) -> None:
        self.event_expectations = dict(event_expectations)
        self.action_intents = list(action_intents)


class _IntentRecorderStub:
    def __init__(self) -> None:
        self.records: list[ProgramIntentRecord] = []

    async def record_program_intent(self, record: ProgramIntentRecord) -> None:
        self.records.append(record)


class _CommitStoreStub:
    async def head(
        self, *, branch_id: UUID, projection_hash: str
    ) -> Mapping[str, object] | None:
        _ = branch_id, projection_hash
        return None


class _AssertingHeadStore:
    def __init__(
        self,
        *,
        expected_branch_id: UUID | None = None,
        expected_projection_hash: str,
    ) -> None:
        self._expected_branch_id = expected_branch_id
        self._expected_projection_hash = expected_projection_hash

    async def head(
        self, *, branch_id: UUID, projection_hash: str
    ) -> Mapping[str, object] | None:
        if self._expected_branch_id is not None:
            assert branch_id == self._expected_branch_id
        assert projection_hash == self._expected_projection_hash
        return None


@pytest.mark.asyncio
async def test_runtime_executor_fails_closed_on_required_unresolved_input() -> None:
    plan = InvocationPlan(
        name="InputContractRequired",
        steps=(
            PlanInput(
                name="message_text",
                source=PlanSymbolRef(name="plan.message_text"),
                default=None,
                required=True,
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        store=_CommitStoreStub(),
    )

    with pytest.raises(ProgramApplyError, match="Required input unresolved"):
        await executor.execute(plan)


@pytest.mark.asyncio
async def test_runtime_executor_fails_closed_when_contract_validator_is_missing() -> (
    None
):
    event_config_id = uuid4()
    action_config_id = uuid4()
    plan = InvocationPlan(
        name="MissingValidator",
        steps=(
            PlanExpectEventConfig(ref=str(event_config_id), required=True),
            PlanIntentActionConfig(
                action_ref=str(action_config_id),
                event_ref=str(event_config_id),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        store=_CommitStoreStub(),
    )

    with pytest.raises(
        ProgramApplyError, match="Program contract validation unavailable"
    ):
        await executor.execute(plan)


@pytest.mark.asyncio
async def test_runtime_executor_bind_uses_local_projection_branch_id_for_folded_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_identity_branch_id = uuid4()
    actor_role_id = uuid4()
    plan = InvocationPlan(
        name="FoldedActorRoleBind",
        ports=(
            PlanPortContract(
                key="actor_role_actor_role_id",
                projection="actor_role",
                projection_nodes=(
                    PlanPortProjectionNodeContract(
                        key="actor_role",
                        node="actor.Actor::actor_roles",
                        keys=(
                            PlanPortProjectionNodeKey(
                                name="actor_role",
                                value_expr=PlanLocalRef(name="actor_role_id"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        steps=(
            PlanInput(
                name="actor_role_id",
                source=PlanSymbolRef(name="actor_role_id"),
                default=PlanSymbolRef(name="plan.actor_role_id"),
                required=False,
            ),
            PlanInput(
                name="actor_role_branch_id",
                source=PlanSymbolRef(name="actor_role_branch_id"),
                default=PlanSymbolRef(name="plan.actor_identity_branch_id"),
                required=False,
            ),
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="bind",
                    args=(
                        PlanCallArg(
                            name="port",
                            value=PlanSymbolRef(
                                name="program.port.actor_role_actor_role_id",
                            ),
                        ),
                        PlanCallArg(name="view_key", value="actor_role.main"),
                    ),
                ),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        store=_CommitStoreStub(),
    )
    monkeypatch.setattr(
        "aware_experience.program.runtime_discovery.build_program_describe_environment_opgs",
        lambda *, index: [  # noqa: ARG005
            SimpleNamespace(
                id=uuid4(),
                name="actor_role",
                projection_hash="sha256:test:actor-role",
            ),
        ],
    )

    await executor.execute(
        plan,
        symbols={
            "plan.actor_identity_branch_id": str(actor_identity_branch_id),
            "plan.actor_role_id": str(actor_role_id),
        },
    )

    assert executor.resolved_lane() == (
        actor_identity_branch_id,
        "sha256:test:actor-role",
    )


@pytest.mark.asyncio
async def test_runtime_executor_uses_contract_validator_for_expect_and_intent() -> None:
    event_config_id = uuid4()
    action_config_id = uuid4()
    validator = _ContractValidatorStub()
    plan = InvocationPlan(
        name="RuntimeContractValidation",
        steps=(
            PlanInput(
                name="actor_ref",
                source=PlanSymbolRef(name="plan.actor_id"),
                default=None,
                required=True,
            ),
            PlanLet(name="actor_ref_copy", value=PlanLocalRef(name="actor_ref")),
            PlanExpectEventConfig(ref=str(event_config_id), required=True),
            PlanIntentActionConfig(
                action_ref=str(action_config_id),
                event_ref=str(event_config_id),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        contract_validator=validator,
    )

    results = await executor.execute(plan)
    assert results == []
    assert validator.event_expectations == {event_config_id: True}
    assert validator.action_intents == [(action_config_id, event_config_id)]


@pytest.mark.asyncio
async def test_runtime_executor_records_program_intent_only_on_real_run() -> None:
    event_config_id = uuid4()
    action_config_id = uuid4()
    turn_instruction_id = uuid4()
    instruction_intent_id = uuid4()
    event_id = uuid4()
    intent_key = "program-turn:test-intent"
    validator = _ContractValidatorStub()
    recorder = _IntentRecorderStub()
    plan = InvocationPlan(
        name="RuntimeIntentReceipt",
        steps=(
            PlanIntentActionConfig(
                action_ref=str(action_config_id),
                event_ref=str(event_config_id),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        contract_validator=validator,
        intent_recorder=recorder,
    )
    symbols: dict[str, object] = {
        "plan.intent.0.program_turn_instruction_id": str(turn_instruction_id),
        "plan.intent.0.program_impl_instruction_intent_id": str(instruction_intent_id),
        "plan.intent.0.event_id": str(event_id),
        "plan.intent.0.intent_key": intent_key,
    }

    assert await executor.execute(plan, symbols=symbols, validate_only=True) == []
    assert recorder.records == []

    assert await executor.execute(plan, symbols=symbols) == []

    assert validator.action_intents == [(action_config_id, event_config_id)]
    assert recorder.records == [
        ProgramIntentRecord(
            event_id=event_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            intent_key=intent_key,
            step_index=0,
            program_turn_instruction_id=turn_instruction_id,
            program_impl_instruction_intent_id=instruction_intent_id,
        )
    ]


@pytest.mark.asyncio
async def test_runtime_executor_accepts_bind_when_inactive() -> None:
    plan = InvocationPlan(
        name="BindInactive",
        steps=(
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="bind",
                    args=(
                        PlanCallArg(
                            name="port",
                            value=PlanSymbolRef(name="program.port.main"),
                        ),
                        PlanCallArg(name="view_key", value="conversation.chat"),
                        PlanCallArg(name="is_active", value=False),
                    ),
                ),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
    )

    results = await executor.execute(plan)
    assert results == []


@pytest.mark.asyncio
async def test_runtime_executor_bind_rejects_missing_port_resolver_contract() -> None:
    plan = InvocationPlan(
        name="BindMissingContract",
        steps=(
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="bind",
                    args=(
                        PlanCallArg(
                            name="port",
                            value=PlanSymbolRef(name="program.port.main"),
                        ),
                        PlanCallArg(name="view_key", value="conversation.chat"),
                    ),
                ),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
    )

    with pytest.raises(
        ProgramApplyError,
        match=r"bind unresolved port contract; expected projection on declared port",
    ):
        await executor.execute(plan)


@pytest.mark.asyncio
async def test_runtime_executor_bind_reads_compiled_port_contract_metadata() -> None:
    plan = InvocationPlan(
        name="BindCompiledPortContract",
        ports=(
            PlanPortContract(
                key="main",
                projection="thread",
                projection_nodes=(
                    PlanPortProjectionNodeContract(
                        key="thread",
                        node="thread.main",
                        keys=(
                            PlanPortProjectionNodeKey(
                                name="class_instance_identity_id",
                                value_expr=PlanSymbolRef(name="plan.thread_id"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        steps=(
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="bind",
                    args=(
                        PlanCallArg(
                            name="port",
                            value=PlanSymbolRef(name="program.port.main"),
                        ),
                        PlanCallArg(name="view_key", value="thread.main"),
                    ),
                ),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
    )

    with pytest.raises(
        ProgramApplyError,
        match=r"bind branch id for projection thread must resolve to UUID",
    ):
        await executor.execute(plan, symbols={"plan.thread_branch_id": "not-a-uuid"})


@pytest.mark.asyncio
async def test_runtime_executor_bind_resolves_projection_alias_from_port_nodes_when_unique(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thread_id = uuid4()
    projection_hash = "sha256:test:home"
    opg_id = uuid4()
    plan = InvocationPlan(
        name="BindProjectionAliasUnique",
        ports=(
            PlanPortContract(
                key="main",
                projection="home_story",
                projection_nodes=(
                    PlanPortProjectionNodeContract(
                        key="home",
                        node="home.home",
                        keys=(
                            PlanPortProjectionNodeKey(
                                name="class_instance_identity_id",
                                value_expr=PlanSymbolRef(name="plan.thread_id"),
                            ),
                        ),
                    ),
                    PlanPortProjectionNodeContract(
                        key="door",
                        node="doors.front_door",
                        keys=(),
                    ),
                ),
            ),
        ),
        steps=(
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="bind",
                    args=(
                        PlanCallArg(
                            name="port",
                            value=PlanSymbolRef(name="program.port.main"),
                        ),
                        PlanCallArg(name="view_key", value="home_story.security.door"),
                    ),
                ),
            ),
        ),
    )

    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=thread_id,
        commit=True,
        publish=False,
        store=_AssertingHeadStore(expected_projection_hash="sha256:test:home"),
    )
    monkeypatch.setattr(
        "aware_experience.program.runtime_discovery.build_program_describe_environment_opgs",
        lambda *, index: [  # noqa: ARG005
            SimpleNamespace(id=opg_id, name="home", projection_hash=projection_hash),
        ],
    )

    await executor.execute(plan)

    assert executor._resolved_lane_branch_id == thread_id
    assert executor._resolved_lane_projection_hash == projection_hash


@pytest.mark.asyncio
async def test_runtime_executor_bind_infers_branch_from_keyed_root_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home_id = uuid4()
    projection_hash = "sha256:test:home"
    opg_id = uuid4()
    plan = InvocationPlan(
        name="BindKeyedRootNode",
        ports=(
            PlanPortContract(
                key="main",
                projection="home_story",
                projection_nodes=(
                    PlanPortProjectionNodeContract(
                        key="home",
                        node="home",
                        keys=(
                            PlanPortProjectionNodeKey(
                                name="class_instance_identity_id",
                                value_expr=PlanSymbolRef(name="plan.home_id"),
                            ),
                        ),
                    ),
                    PlanPortProjectionNodeContract(
                        key="door",
                        node="doors",
                        keys=(
                            PlanPortProjectionNodeKey(
                                name="class_instance_identity_id",
                                value_expr=PlanSymbolRef(name="plan.door_id"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        steps=(
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="bind",
                    args=(
                        PlanCallArg(
                            name="port",
                            value=PlanSymbolRef(name="program.port.main"),
                        ),
                        PlanCallArg(name="view_key", value="home_story.security.door"),
                    ),
                ),
            ),
        ),
    )

    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        store=_AssertingHeadStore(
            expected_branch_id=home_id,
            expected_projection_hash="sha256:test:home",
        ),
    )
    monkeypatch.setattr(
        "aware_experience.program.runtime_discovery.build_program_describe_environment_opgs",
        lambda *, index: [  # noqa: ARG005
            SimpleNamespace(id=opg_id, name="home", projection_hash=projection_hash),
        ],
    )

    await executor.execute(
        plan,
        symbols={
            "plan.home_id": str(home_id),
            "plan.door_id": str(uuid4()),
        },
    )

    assert executor._resolved_lane_branch_id == home_id
    assert executor._resolved_lane_projection_hash == projection_hash


@pytest.mark.asyncio
async def test_runtime_executor_bind_rejects_ambiguous_projection_alias_from_port_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    plan = InvocationPlan(
        name="BindProjectionAliasAmbiguous",
        ports=(
            PlanPortContract(
                key="main",
                projection="home_story",
                projection_nodes=(
                    PlanPortProjectionNodeContract(
                        key="home",
                        node="home.home",
                        keys=(),
                    ),
                    PlanPortProjectionNodeContract(
                        key="tv",
                        node="tvs.living_room_tv",
                        keys=(),
                    ),
                ),
            ),
        ),
        steps=(
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="bind",
                    args=(
                        PlanCallArg(
                            name="port",
                            value=PlanSymbolRef(name="program.port.main"),
                        ),
                        PlanCallArg(
                            name="view_key", value="home_story.entertainment.tv"
                        ),
                    ),
                ),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
    )
    monkeypatch.setattr(
        "aware_experience.program.runtime_discovery.build_program_describe_environment_opgs",
        lambda *, index: [  # noqa: ARG005
            SimpleNamespace(
                id=uuid4(), name="home", projection_hash="sha256:test:home"
            ),
            SimpleNamespace(id=uuid4(), name="tvs", projection_hash="sha256:test:tvs"),
        ],
    )

    with pytest.raises(
        ProgramApplyError, match="Ambiguous projection alias in bind contract"
    ):
        await executor.execute(
            plan, symbols={"plan.home_story_branch_id": str(branch_id)}
        )


@pytest.mark.asyncio
async def test_runtime_executor_legacy_plan_port_target_is_not_directive() -> None:
    plan = InvocationPlan(
        name="LegacyPlanPortTarget",
        steps=(
            PlanInvoke(
                kind="effect",
                call=PlanCall(
                    target="plan.port",
                    args=(),
                ),
            ),
        ),
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=_invoker_stub(),
        index=_index_stub(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
    )

    with pytest.raises(ProgramApplyError, match="Invocation requires an active lane"):
        await executor.execute(plan)


class _EvaluatorStub:
    def __init__(self, *, bindings_by_event: dict[UUID, object]) -> None:
        self._bindings_by_event = bindings_by_event

    async def resolve_bindings_for_event_config_ids(
        self,
        *,
        event_config_ids: set[UUID],
        include_disabled: bool,
        force_refresh: bool,
    ) -> Mapping[UUID, object]:
        _ = event_config_ids, include_disabled, force_refresh
        return dict(self._bindings_by_event)


@pytest.mark.asyncio
async def test_reactivity_validator_allows_optional_event_without_binding() -> None:
    event_config_id = uuid4()
    action_config_id = uuid4()
    validator = _ReactivityProgramContractValidator(
        condition_evaluator=_EvaluatorStub(bindings_by_event={}),
    )

    await validator.validate_event_action_contracts(
        event_expectations={event_config_id: False},
        action_intents=[(action_config_id, event_config_id)],
    )


@pytest.mark.asyncio
async def test_reactivity_validator_requires_intended_action_binding() -> None:
    event_config_id = uuid4()
    action_config_id = uuid4()
    other_action_config_id = uuid4()
    binding = SimpleNamespace(
        action_bindings=[
            SimpleNamespace(
                is_enabled=True,
                action_config_id=other_action_config_id,
            )
        ]
    )
    validator = _ReactivityProgramContractValidator(
        condition_evaluator=_EvaluatorStub(
            bindings_by_event={event_config_id: [binding]},
        ),
    )

    with pytest.raises(ProgramApplyError, match="intent action_config is not bound"):
        await validator.validate_event_action_contracts(
            event_expectations={event_config_id: True},
            action_intents=[(action_config_id, event_config_id)],
        )
