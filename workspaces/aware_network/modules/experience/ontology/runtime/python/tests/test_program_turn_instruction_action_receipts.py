from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import IsolatedMetaAwareRoot, MetaOIGAssertions
from aware_meta.runtime.testing.proof import (
    LaneIds,
    ProofCall,
    run_meta_runtime_proof,
)
from ._experience_runtime_test_paths import REPO_ROOT

from aware_experience.handlers.impl.program import (
    program_turn_instruction as turn_instruction_impl,
)
from aware_experience.handlers.impl.program import (
    program_turn_instruction_action as action_receipt_impl,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_experience_ontology.program.program_turn_instruction import (
    ProgramTurnInstruction,
)
from aware_experience_ontology.program.program_turn_instruction_action import (
    ProgramTurnInstructionAction,
)
from aware_experience_ontology.stable_ids import (
    stable_program_turn_instruction_action_id,
)
from aware_reactivity_ontology.action.action_config import ActionConfig
from aware_reactivity_ontology.event.event_config import EventConfig


class _Session:
    def __init__(self) -> None:
        self._instances: dict[tuple[type, UUID], object] = {}

    def imap_get(self, cls, object_id):
        return self._instances.get((cls, object_id))

    def put(self, obj: object) -> None:
        object_id = getattr(obj, "id")
        self._instances[(obj.__class__, object_id)] = obj


def _u(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware://tests/experience/program-action/{name}")


def _experience_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
    )


def _experience_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/runtime/python",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/runtime/python",
    )


def _prepend_experience_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _experience_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_experience_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    from aware_experience.handlers._generated import (
        meta_handlers as experience_meta_handlers,
    )
    from aware_reactivity.handlers._generated import (
        meta_handlers as reactivity_meta_handlers,
    )

    handler_modules = (
        cast(
            MetaGraphGeneratedLanguageHandlerModule, cast(Any, reactivity_meta_handlers)
        ),
        cast(
            MetaGraphGeneratedLanguageHandlerModule, cast(Any, experience_meta_handlers)
        ),
    )
    bootstrap_modules = (
        cast(
            MetaGraphGeneratedConstructorBootstrapModule,
            cast(Any, reactivity_meta_handlers),
        ),
        cast(
            MetaGraphGeneratedConstructorBootstrapModule,
            cast(Any, experience_meta_handlers),
        ),
    )
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=handler_modules,
        bootstrap_modules=bootstrap_modules,
    )
    assert runtime.context is not None
    return runtime


def _intent_instruction(
    *,
    instruction_intent_id: UUID,
    action_config_id: UUID,
    event_config_id: UUID,
) -> ProgramImplInstructionIntent:
    return ProgramImplInstructionIntent.model_construct(
        id=instruction_intent_id,
        program_impl_instruction_id=_u(f"program-instruction:{instruction_intent_id}"),
        action_config_id=action_config_id,
        event_config_id=event_config_id,
    )


@pytest.mark.asyncio
async def test_build_action_receipt_validates_intent_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        action_receipt_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )
    turn_instruction_id = _u("turn-instruction")
    instruction_intent_id = _u("instruction-intent")
    action_config_id = _u("action-config")
    event_config_id = _u("event-config")
    action_intent_id = _u("action-intent")
    intent_key = "program-turn:door-lock"
    intent_instruction = _intent_instruction(
        instruction_intent_id=instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
    )
    action_config = ActionConfig.model_construct(id=action_config_id, name="door.lock")
    event_config = EventConfig.model_construct(
        id=event_config_id, name="door.requested"
    )
    session.put(intent_instruction)
    session.put(action_config)
    session.put(event_config)

    receipt = await action_receipt_impl.build_via_program_turn_instruction(
        program_turn_instruction_id=turn_instruction_id,
        program_impl_instruction_intent_id=instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        action_intent_id=action_intent_id,
        intent_key=intent_key,
    )

    assert receipt.id == stable_program_turn_instruction_action_id(
        program_turn_instruction_id=turn_instruction_id,
        program_impl_instruction_intent_id=instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        intent_key=intent_key,
    )
    assert receipt.program_impl_instruction_intent is intent_instruction
    assert receipt.action_config is action_config
    assert receipt.event_config is event_config
    assert receipt.action_intent_id == action_intent_id
    assert receipt.intent_key == intent_key

    session.put(receipt)
    assert (
        await action_receipt_impl.build_via_program_turn_instruction(
            program_turn_instruction_id=turn_instruction_id,
            program_impl_instruction_intent_id=instruction_intent_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            action_intent_id=action_intent_id,
            intent_key=intent_key,
        )
        is receipt
    )

    with pytest.raises(RuntimeError, match="action_config mismatch"):
        await action_receipt_impl.build_via_program_turn_instruction(
            program_turn_instruction_id=turn_instruction_id,
            program_impl_instruction_intent_id=instruction_intent_id,
            action_config_id=_u("other-action-config"),
            event_config_id=event_config_id,
            action_intent_id=action_intent_id,
            intent_key=intent_key,
        )


@pytest.mark.asyncio
async def test_record_action_attaches_unique_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        turn_instruction_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )
    monkeypatch.setattr(
        action_receipt_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )
    monkeypatch.setattr(
        ProgramTurnInstructionAction,
        "build_via_program_turn_instruction",
        staticmethod(action_receipt_impl.build_via_program_turn_instruction),
    )
    turn_instruction_id = _u("record-turn-instruction")
    instruction_intent_id = _u("record-instruction-intent")
    action_config_id = _u("record-action-config")
    event_config_id = _u("record-event-config")
    action_intent_id = _u("record-action-intent")
    intent_key = "program-turn:record-action"
    turn_instruction = ProgramTurnInstruction.model_construct(
        id=turn_instruction_id,
        program_turn_id=_u("turn"),
        program_instruction_id=_u("instruction"),
        sequence=0,
        bind_receipt=None,
        invoke_receipt=None,
        action_receipt=None,
        decisions=[],
    )
    session.put(
        _intent_instruction(
            instruction_intent_id=instruction_intent_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
        )
    )

    receipt = await turn_instruction_impl.record_action(
        program_turn_instruction=turn_instruction,
        program_impl_instruction_intent_id=instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        action_intent_id=action_intent_id,
        intent_key=intent_key,
    )

    assert turn_instruction.action_receipt is receipt
    assert receipt.action_intent_id == action_intent_id
    assert receipt.intent_key == intent_key
    assert (
        await turn_instruction_impl.record_action(
            program_turn_instruction=turn_instruction,
            program_impl_instruction_intent_id=instruction_intent_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            action_intent_id=action_intent_id,
            intent_key=intent_key,
        )
        is receipt
    )

    with pytest.raises(RuntimeError, match="payload mismatch"):
        await turn_instruction_impl.record_action(
            program_turn_instruction=turn_instruction,
            program_impl_instruction_intent_id=instruction_intent_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            action_intent_id=_u("other-action-intent"),
            intent_key=intent_key,
        )


@pytest.mark.asyncio
async def test_program_action_receipt_committed_graph_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(
        repo_root=repo_root,
        monkeypatch=monkeypatch,
    )

    import aware_experience_ontology  # noqa: F401
    import aware_reactivity_ontology  # noqa: F401
    from aware_meta.enum.instance.option_resolver import build_enum_option_resolver
    from aware_meta.graph.instance.builder import (
        build_object_instance_graph,
        build_rooted_object_instance_graph_base,
    )
    from aware_meta.graph.instance.commit.builder import (
        build_object_instance_graph_commit,
    )
    from aware_meta.graph.instance.commit.committer import FSLaneCommitter
    from aware_meta.graph.instance.commit.materializer import OIGMaterializer
    from aware_meta.runtime.graph_commit_invocation_backend import (
        resolve_meta_graph_object_projection_graph_identity_id,
    )
    from aware_meta_ontology.stable_ids import (
        stable_object_instance_graph_id,
        stable_object_instance_graph_identity_id,
    )
    from aware_reactivity.stable_ids import stable_action_intent_id
    from aware_experience_ontology.program.impl.program_impl import ProgramImpl
    from aware_experience_ontology.program.impl.program_impl_instruction import (
        ProgramImplInstruction,
    )
    from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
        ProgramImplInstructionType,
    )
    from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
        ProgramImplInstructionIntent,
    )
    from aware_experience_ontology.program.program import Program
    from aware_experience_ontology.program.program_enums import ProgramRunStatus
    from aware_experience_ontology.program.program_turn import ProgramTurn
    from aware_experience_ontology.program.program_turn_instruction import (
        ProgramTurnInstruction,
    )
    from aware_experience_ontology.program.program_turn_instruction_action import (
        ProgramTurnInstructionAction,
    )
    from aware_experience_ontology.stable_ids import (
        stable_program_id,
        stable_program_impl_id,
        stable_program_impl_instruction_id,
        stable_program_impl_instruction_intent_id,
        stable_program_turn_id,
        stable_program_turn_instruction_action_id,
        stable_program_turn_instruction_id,
    )

    action_config_id = _u("committed-action-config")
    event_config_id = _u("committed-event-config")
    event_id = _u("committed-event")
    intent_key = "program-turn:committed-action"
    action_intent_id = stable_action_intent_id(
        event_id=event_id,
        config_id=action_config_id,
        intent_key=intent_key,
    )
    subscription_intent_key = "subscription:committed-action"
    subscription_intent_id = stable_action_intent_id(
        event_id=event_id,
        config_id=action_config_id,
        intent_key=subscription_intent_key,
    )

    program_config_id = _u("committed-program-config")
    program_impl_id = stable_program_impl_id(
        program_config_id=program_config_id,
        key="impl",
    )
    program_instruction_id = stable_program_impl_instruction_id(
        program_impl_id=program_impl_id,
        sequence=0,
    )
    instruction_intent_id = stable_program_impl_instruction_intent_id(
        program_impl_instruction_id=program_instruction_id,
    )
    program_id = stable_program_id(program_impl_id=program_impl_id, key="runtime")
    turn_id = _u("committed-turn")
    program_turn_id = stable_program_turn_id(program_id=program_id, turn_id=turn_id)
    turn_instruction_id = stable_program_turn_instruction_id(
        program_turn_id=program_turn_id,
        program_instruction_id=program_instruction_id,
        sequence=0,
    )
    receipt_id = stable_program_turn_instruction_action_id(
        program_turn_instruction_id=turn_instruction_id,
        program_impl_instruction_intent_id=instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        intent_key=intent_key,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index
        lane = LaneIds()

        action_result, action_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ActionIntent",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.action.ActionIntent",
                    function_name="create_via_event",
                    args=[event_id, action_config_id, intent_key],
                    expected_root_object_id=action_intent_id,
                )
            ],
        )
        action_assertions.expect_root(action_intent_id)
        action_assertions.expect_primitive(
            instance_id=action_intent_id,
            field_name="intent_key",
            expected=intent_key,
        )

        subscription_result, subscription_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(),
            opg_name="ActionIntent",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.action.ActionIntent",
                    function_name="create_via_event",
                    args=[event_id, action_config_id, subscription_intent_key],
                    kwargs={"actor_subscription_id": _u("subscription")},
                    expected_root_object_id=subscription_intent_id,
                )
            ],
        )
        subscription_assertions.expect_root(subscription_intent_id)
        subscription_assertions.expect_primitive(
            instance_id=subscription_intent_id,
            field_name="intent_key",
            expected=subscription_intent_key,
        )
        assert action_result.branch_id != subscription_result.branch_id

        program_opg = next(
            opg
            for opg in index.ocg.object_projection_graphs
            if opg.name == "ProgramRuntime"
        )
        branch_id = _u("committed-program-runtime-branch")
        oig_id = stable_object_instance_graph_id(
            object_projection_graph_id=program_opg.id,
            key=f"program-runtime:{branch_id}",
        )
        opgi_id = resolve_meta_graph_object_projection_graph_identity_id(
            index=index,
            opg=program_opg,
        )
        oigi_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=opgi_id,
            object_instance_graph_id=oig_id,
        )

        instruction_intent = ProgramImplInstructionIntent(
            id=instruction_intent_id,
            program_impl_instruction_id=program_instruction_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
        )
        program_instruction = ProgramImplInstruction(
            id=program_instruction_id,
            program_impl_id=program_impl_id,
            type=ProgramImplInstructionType.intent,
            sequence=0,
            instruction_intent=instruction_intent,
        )
        program_impl = ProgramImpl(
            id=program_impl_id,
            program_config_id=program_config_id,
            key="impl",
            instructions=[program_instruction],
        )
        action_receipt = ProgramTurnInstructionAction(
            id=receipt_id,
            program_turn_instruction_id=turn_instruction_id,
            program_impl_instruction_intent_id=instruction_intent_id,
            program_impl_instruction_intent=instruction_intent,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            action_intent_id=action_intent_id,
            intent_key=intent_key,
        )
        turn_instruction = ProgramTurnInstruction(
            id=turn_instruction_id,
            program_turn_id=program_turn_id,
            program_instruction_id=program_instruction_id,
            program_instruction=program_instruction,
            sequence=0,
            action_receipt=action_receipt,
        )
        program_turn = ProgramTurn(
            id=program_turn_id,
            program_id=program_id,
            turn_id=turn_id,
            order=0,
            instructions=[turn_instruction],
        )
        program = Program(
            id=program_id,
            program_impl_id=program_impl_id,
            program_impl=program_impl,
            key="runtime",
            status=ProgramRunStatus.running,
            turns=[program_turn],
        )

        before_oig = build_rooted_object_instance_graph_base(
            key="program_runtime",
            name="program_runtime",
            description="ProgramRuntime B1 committed proof base",
            object_config_graph=index.ocg,
            object_projection_graph=program_opg,
            root_source_object_id=program_id,
            oig_id=oig_id,
        )
        after_oig = build_object_instance_graph(
            root_instance=program,
            object_config_graph=index.ocg,
            object_projection_graph=program_opg,
            name="program_runtime",
            description="ProgramRuntime B1 committed proof",
            oig_id=oig_id,
            instance_registry=[
                action_receipt,
                instruction_intent,
                program,
                program_impl,
                program_instruction,
                program_turn,
                turn_instruction,
            ],
            enum_option_resolver=build_enum_option_resolver(
                object_config_graph=index.ocg,
            ),
        )
        domain_commit = build_object_instance_graph_commit(
            old=before_oig,
            new=after_oig,
            branch_id=branch_id,
            object_instance_graph_identity_id=oigi_id,
            object_projection_graph=program_opg,
            author_id=lane.actor_id or _u("committed-author"),
        )
        assert domain_commit is not None
        committed = await FSLaneCommitter().commit(
            branch_id=branch_id,
            projection_hash=program_opg.projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=oig_id,
            before_oig=before_oig,
            root_object_id=program_id,
            changes=domain_commit.object_instance_graph_changes,
            graph_hash_pre=domain_commit.graph_hash_pre,
            graph_hash_post=domain_commit.graph_hash_post,
            author_id=lane.actor_id or _u("committed-author"),
        )
        assert committed is not None
        rehydrated_oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=program_opg,
            commit_id=committed.commit.id,
            oig_id=oig_id,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        assertions = MetaOIGAssertions(
            oig=rehydrated_oig,
            index=index,
        )
        assertions.expect_root(program_id)
        assertions.expect_instance(turn_instruction_id)
        assertions.expect_instance(receipt_id)
        assertions.expect_edge(
            source_id=turn_instruction_id,
            target_id=receipt_id,
            relationship_name="action_receipt",
        )
        assertions.expect_primitive(
            instance_id=receipt_id,
            field_name="program_impl_instruction_intent_id",
            expected=instruction_intent_id,
        )
        assertions.expect_primitive(
            instance_id=receipt_id,
            field_name="action_intent_id",
            expected=action_intent_id,
        )
        assertions.expect_primitive(
            instance_id=receipt_id,
            field_name="intent_key",
            expected=intent_key,
        )
