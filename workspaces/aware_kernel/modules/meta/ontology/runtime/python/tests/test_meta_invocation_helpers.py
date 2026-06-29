from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import get_type_hints
from uuid import UUID, uuid4

from pydantic import BaseModel

from aware_meta.graph.instance.commit.fs_store import CommitActionDescriptor
from aware_meta.runtime.commit.required_reactions import (
    RuntimeCommitReactionContext,
    RuntimeCommitReactionReceipt,
)
from aware_meta.runtime.invocation_commits import append_invocation_domain_commit
from aware_meta.runtime.invocation_helpers import (
    build_invocation_operation_label_index,
    jsonify_invocation_payload,
    link_function_call_response_commit,
    resolve_invocation_operation_label,
)
from aware_meta.runtime.invocation_commit_actions import (
    OPG_CONSTRUCTOR_CALL_TARGET,
    build_constructor_commit_action,
    build_instance_commit_action,
)
from aware_meta.runtime.invocation_reactions import (
    run_invocation_required_commit_reactions,
)
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID, resolve_meta_author_id
from aware_meta.runtime.commit.identity_history import (
    _derive_oigi_post_oig_from_changes,
)
from aware_meta.runtime.function_call_builder import (
    build_meta_function_call,
    resolve_meta_function_config,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import (
    default_meta_class_instance_resolver,
    default_meta_enum_option_resolver,
    parse_meta_default_value,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import (
    stable_class_instance_identity_id,
    stable_function_call_id,
    stable_function_call_response_commit_id,
)


class _Mode(Enum):
    active = "active"


class _Payload(BaseModel):
    value_id: str
    mode: _Mode


@dataclass(frozen=True)
class _RecordedInvocationCommit:
    branch_id: UUID
    projection_hash: str
    object_instance_graph_identity_id: UUID
    object_instance_graph_id: UUID
    before_oig: ObjectInstanceGraph
    root_object_id: UUID | None
    changes: list[ObjectInstanceGraphChange]
    graph_hash_pre: str
    graph_hash_post: str
    author_id: UUID
    commit_action: CommitActionDescriptor | None


class _FakeLaneCommitter:
    def __init__(self, commit_result: ObjectInstanceGraphCommit | None) -> None:
        self._commit_result = commit_result
        self.recorded: _RecordedInvocationCommit | None = None

    async def commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        before_oig: ObjectInstanceGraph,
        root_object_id: UUID | None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_action: CommitActionDescriptor | None,
    ) -> ObjectInstanceGraphCommit | None:
        self.recorded = _RecordedInvocationCommit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            before_oig=before_oig,
            root_object_id=root_object_id,
            changes=changes,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            commit_action=commit_action,
        )
        return self._commit_result

    def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
        return {"append_ms": 4}


class _FakeRequiredReactionRunner:
    def __init__(self) -> None:
        self.contexts: list[RuntimeCommitReactionContext] = []

    async def __call__(
        self,
        context: RuntimeCommitReactionContext,
    ) -> tuple[RuntimeCommitReactionReceipt, ...]:
        self.contexts.append(context)
        return ()


def test_jsonify_invocation_payload_normalizes_runtime_values() -> None:
    value_id = uuid4()
    item_id = uuid4()

    payload = jsonify_invocation_payload(
        {
            "id": value_id,
            "model": _Payload(value_id=str(value_id), mode=_Mode.active),
            "items": (_Mode.active, item_id),
        }
    )

    assert payload == {
        "id": str(value_id),
        "model": {
            "value_id": str(value_id),
            "mode": "active",
        },
        "items": ["active", str(item_id)],
    }


def test_link_function_call_response_commit_appends_stable_edge_once() -> None:
    response_id = uuid4()
    oig_commit_id = uuid4()
    response = SimpleNamespace(
        id=response_id,
        function_call_response_commits=[],
    )
    oig_commit = ObjectInstanceGraphCommit.model_construct(id=oig_commit_id)

    link_function_call_response_commit(response=response, oig_commit=oig_commit)
    link_function_call_response_commit(response=response, oig_commit=oig_commit)

    assert len(response.function_call_response_commits) == 1
    edge = response.function_call_response_commits[0]
    assert edge.id == stable_function_call_response_commit_id(
        function_call_response_id=response_id,
        object_instance_graph_commit_id=oig_commit_id,
    )
    assert edge.object_instance_graph_commit is oig_commit
    assert edge.object_instance_graph_commit_id == oig_commit_id
    assert edge.function_call_response_id == response_id
    assert edge.position == 0


def test_resolve_invocation_operation_label_uses_class_function_label() -> None:
    function_id = uuid4()
    function_config = SimpleNamespace(id=function_id, name="attach_lane")
    class_config = SimpleNamespace(
        name="Thread",
        class_config_function_configs=[
            SimpleNamespace(
                function_config_id=function_id,
                function_config=function_config,
            )
        ],
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(object_config_graph_nodes=[]),
        class_configs_by_id={uuid4(): class_config},
    )

    label_index = build_invocation_operation_label_index(index)

    assert label_index == {function_id: "Thread.attach_lane"}
    assert (
        resolve_invocation_operation_label(
            index=index,
            function_id=function_id,
            label_index=label_index,
        )
        == "Thread.attach_lane"
    )


def test_resolve_invocation_operation_label_falls_back_to_function_name() -> None:
    function_id = uuid4()
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_config_graph_nodes=[
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=SimpleNamespace(id=function_id, name="read"),
                )
            ]
        ),
        class_configs_by_id={},
    )

    assert (
        resolve_invocation_operation_label(index=index, function_id=function_id)
        == "read"
    )


def test_resolve_invocation_operation_label_returns_none_for_unknown_function() -> None:
    index = SimpleNamespace(
        ocg=SimpleNamespace(object_config_graph_nodes=[]),
        class_configs_by_id={},
    )

    assert resolve_invocation_operation_label(index=index, function_id=uuid4()) is None


def test_build_constructor_commit_action_records_root_identity() -> None:
    function_id = uuid4()
    root_object_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    root_class_instance_id = uuid4()

    action = build_constructor_commit_action(
        operation_label=" Project.create ",
        function_id=function_id,
        root_object_id=root_object_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        root_class_instance_id=root_class_instance_id,
    )

    assert action.operation_label == "Project.create"
    assert action.call_target == OPG_CONSTRUCTOR_CALL_TARGET
    assert action.function_id == function_id
    assert action.object_id == root_object_id
    assert action.class_instance_identity_id == stable_class_instance_identity_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_id=root_class_instance_id,
    )


def test_build_instance_commit_action_records_target_identity() -> None:
    function_id = uuid4()
    object_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    target_class_instance_id = uuid4()

    action = build_instance_commit_action(
        operation_label="Thread.attach_lane",
        call_target="instance",
        function_id=function_id,
        object_id=object_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        source_class_instance_id=target_class_instance_id,
    )

    assert action.operation_label == "Thread.attach_lane"
    assert action.call_target == "instance"
    assert action.function_id == function_id
    assert action.object_id == object_id
    assert action.class_instance_identity_id == stable_class_instance_identity_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_id=target_class_instance_id,
    )


def test_build_instance_commit_action_falls_back_to_function_label() -> None:
    function_id = uuid4()

    action = build_instance_commit_action(
        operation_label=" ",
        call_target="instance",
        function_id=function_id,
        object_id=None,
        object_instance_graph_identity_id=uuid4(),
        source_class_instance_id=None,
    )

    assert action.operation_label == f"function:{function_id}"
    assert action.call_target == "instance"
    assert action.class_instance_identity_id is None


def test_append_invocation_domain_commit_delegates_typed_commit_action() -> None:
    branch_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    root_object_id = uuid4()
    author_id = uuid4()
    function_id = uuid4()
    object_id = uuid4()
    target_class_instance_id = uuid4()
    before_oig = ObjectInstanceGraph.model_construct(id=object_instance_graph_id)
    commit = ObjectInstanceGraphCommit.model_construct(id=uuid4())
    committer = _FakeLaneCommitter(commit)
    action = build_instance_commit_action(
        operation_label="Thread.attach_lane",
        call_target="instance",
        function_id=function_id,
        object_id=object_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        source_class_instance_id=target_class_instance_id,
    )

    result = asyncio.run(
        append_invocation_domain_commit(
            branch_id=branch_id,
            projection_hash="thread",
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            before_oig=before_oig,
            root_object_id=root_object_id,
            changes=[],
            graph_hash_pre="pre",
            graph_hash_post="post",
            author_id=author_id,
            action=action,
            committer=committer,
        )
    )

    assert result.commit is commit
    assert result.perf_profile == {"append_ms": 4}
    recorded = committer.recorded
    assert recorded is not None
    assert recorded == _RecordedInvocationCommit(
        branch_id=branch_id,
        projection_hash="thread",
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        before_oig=before_oig,
        root_object_id=root_object_id,
        changes=[],
        graph_hash_pre="pre",
        graph_hash_post="post",
        author_id=author_id,
        commit_action=recorded.commit_action,
    )
    commit_action = recorded.commit_action
    assert commit_action is not None
    assert commit_action.operation_label == "Thread.attach_lane"
    assert commit_action.call_target == "instance"
    assert commit_action.function_id == function_id
    assert commit_action.object_id == object_id
    assert commit_action.class_instance_identity_id == action.class_instance_identity_id


def test_run_invocation_required_commit_reactions_uses_action_source_identity() -> None:
    branch_id = uuid4()
    actor_id = uuid4()
    function_id = uuid4()
    object_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    target_class_instance_id = uuid4()
    commit = ObjectInstanceGraphCommit.model_construct(id=uuid4())
    perf_ms: dict[str, int] = {}
    index = SimpleNamespace()
    runner = _FakeRequiredReactionRunner()
    action = build_instance_commit_action(
        operation_label="Thread.attach_lane",
        call_target="instance",
        function_id=function_id,
        object_id=object_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        source_class_instance_id=target_class_instance_id,
    )

    receipts = asyncio.run(
        run_invocation_required_commit_reactions(
            index=index,
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash="thread",
            domain_commit=commit,
            action=action,
            perf_ms=perf_ms,
            runner=runner,
        )
    )

    assert receipts == ()
    assert len(runner.contexts) == 1
    context = runner.contexts[0]
    assert context.index is index
    assert context.actor_id == actor_id
    assert context.domain_branch_id == branch_id
    assert context.domain_projection_hash == "thread"
    assert context.domain_commit is commit
    assert (
        context.source_class_instance_identity_id == action.class_instance_identity_id
    )
    assert context.perf_ms is perf_ms


def test_meta_commit_reaction_index_contracts_use_meta_runtime_index() -> None:
    context_hints = get_type_hints(RuntimeCommitReactionContext)
    reaction_hints = get_type_hints(run_invocation_required_commit_reactions)

    assert context_hints["index"] is MetaGraphRuntimeIndex
    assert reaction_hints["index"] is MetaGraphRuntimeIndex


def test_meta_runtime_commit_reactions_do_not_import_legacy_runtime_index() -> None:
    for rel_path in (
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/required_reactions.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/invocation_reactions.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_lane.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_history.py",
    ):
        source = Path(rel_path).read_text(encoding="utf-8")

        assert "aware_runtime.index" not in source
        assert "AwareRuntimeIndex" not in source


def test_materialize_meta_oig_post_detaches_snapshot_lists() -> None:
    before_oig = ObjectInstanceGraph.model_construct(
        id=uuid4(),
        hash="sha256:test:pre",
        class_instances=[],
        class_instance_relationships=[],
    )

    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=(),
        attribute_configs_by_id={},
        class_configs_by_id={},
    )

    assert after_oig is not before_oig
    assert after_oig.class_instances is not before_oig.class_instances
    assert (
        after_oig.class_instance_relationships
        is not before_oig.class_instance_relationships
    )
    assert before_oig.hash == "sha256:test:pre"
    assert isinstance(after_oig.hash, str)
    assert after_oig.hash


def test_oigi_history_post_derivation_uses_selective_copy(monkeypatch) -> None:
    before_oig = ObjectInstanceGraph.model_construct(
        id=uuid4(),
        hash="sha256:test:pre",
        class_instances=[],
        class_instance_relationships=[],
    )
    original_model_copy = ObjectInstanceGraph.model_copy
    observed_deep_flags: list[bool] = []

    def guarded_model_copy(self, *, update=None, deep: bool = False):
        observed_deep_flags.append(deep)
        if deep:
            raise AssertionError("OIGI history post-state must not deep-copy OIG")
        return original_model_copy(self, update=update, deep=deep)

    monkeypatch.setattr(ObjectInstanceGraph, "model_copy", guarded_model_copy)
    index = SimpleNamespace(attribute_configs_by_id={}, class_configs_by_id={})

    after_oig = _derive_oigi_post_oig_from_changes(
        index=index,
        before_oig=before_oig,
        changes=[],
    )

    assert after_oig is not before_oig
    assert observed_deep_flags == [False]


def test_meta_oig_post_materialization_is_not_runtime_owned() -> None:
    for rel_path in (
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/oig_post.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_lane.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_history.py",
    ):
        source = Path(rel_path).read_text(encoding="utf-8")

        assert "aware_runtime.function_call.oig_post" not in source
        assert "aware_runtime.function_call.post_materialization" not in source


def test_meta_author_resolver_uses_system_actor_fallback() -> None:
    actor_id = uuid4()

    assert resolve_meta_author_id(actor_id) == actor_id
    assert resolve_meta_author_id(str(actor_id)) == actor_id
    assert resolve_meta_author_id(None) == META_SYSTEM_ACTOR_ID


def test_meta_value_resolvers_accept_json_friendly_values() -> None:
    enum_option_id = uuid4()
    class_instance_id = uuid4()
    type_descriptor = SimpleNamespace(
        enum_config=SimpleNamespace(
            enum_options=[
                SimpleNamespace(
                    id=enum_option_id,
                    value="active",
                    label="Active",
                    position=2,
                )
            ],
        ),
    )

    assert (
        default_meta_enum_option_resolver(type_descriptor, {"value": "Active"})
        == enum_option_id
    )
    assert default_meta_enum_option_resolver(type_descriptor, 2) == enum_option_id
    assert (
        default_meta_class_instance_resolver(
            SimpleNamespace(),
            {"value": {"id": str(class_instance_id)}},
        )
        == class_instance_id
    )
    assert parse_meta_default_value('{"enabled": true}') == {"enabled": True}


def test_meta_value_author_helpers_are_not_runtime_owned() -> None:
    for rel_path in (
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/author.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/value_resolvers.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_history.py",
    ):
        source = Path(rel_path).read_text(encoding="utf-8")

        assert "aware_runtime.function_call.author" not in source
        assert "aware_runtime.value_resolvers" not in source


def test_build_meta_function_call_uses_meta_index_contract() -> None:
    function_id = uuid4()
    lane_id = uuid4()
    call_key = uuid4()
    object_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    function_config = FunctionConfig.model_construct(
        id=function_id,
        name="create",
        function_config_attribute_configs=[],
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_config_graph_nodes=[
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=function_config,
                )
            ],
        ),
        class_configs_by_id={},
    )

    function_call = build_meta_function_call(
        index=index,
        object_id=object_id,
        function_id=function_id,
        args=[],
        kwargs={},
        domain_oig_lane=SimpleNamespace(id=lane_id),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        call_key=call_key,
        expected_graph_hash_pre="sha256:test:pre",
    )

    assert resolve_meta_function_config(index=index, function_id=function_id) is (
        function_config
    )
    assert function_call.id == stable_function_call_id(
        object_instance_graph_lane_id=lane_id,
        function_config_id=function_id,
        call_key=call_key,
    )
    assert function_call.graph_hash_pre == "sha256:test:pre"
    if "target_class_instance_identity_id" in FunctionCall.model_fields:
        assert function_call.target_class_instance_identity_id == (
            stable_class_instance_identity_id(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                class_instance_id=object_id,
            )
        )


def test_meta_function_call_builder_is_not_runtime_owned() -> None:
    for rel_path in (
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/function_call_builder.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_lane.py",
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_history.py",
    ):
        source = Path(rel_path).read_text(encoding="utf-8")

        assert "aware_runtime.function_call.call_builders" not in source


def test_meta_oigi_lane_bootstrap_uses_generated_handler_executor() -> None:
    source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_lane.py"
    ).read_text(encoding="utf-8")

    assert "build_meta_graph_generated_handler_executor" in source
    assert "oigi_generated_handlers" in source
    assert "aware_runtime.function_call.translator" not in source
    assert "execute_constructor" not in source
    assert "scoped_change_collection" not in source


def test_meta_oigi_history_projection_stays_off_runtime_execution_hydration() -> None:
    source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/commit/identity_history.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "execute_function" not in source
    assert "hydrate_orm_graph_from_oig" not in source
    assert "scoped_change_collection" not in source
    assert "build_object_instance_graph_changes_from_orm_change_set" not in source


def test_run_invocation_required_commit_reactions_prefers_explicit_source_identity() -> (
    None
):
    explicit_source_identity_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    index = SimpleNamespace()
    runner = _FakeRequiredReactionRunner()
    action = build_instance_commit_action(
        operation_label="Thread.attach_lane",
        call_target="instance",
        function_id=uuid4(),
        object_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        source_class_instance_id=uuid4(),
    )

    asyncio.run(
        run_invocation_required_commit_reactions(
            index=index,
            actor_id=uuid4(),
            domain_branch_id=uuid4(),
            domain_projection_hash="thread",
            domain_commit=ObjectInstanceGraphCommit.model_construct(id=uuid4()),
            action=action,
            source_class_instance_identity_id=explicit_source_identity_id,
            runner=runner,
        )
    )

    assert len(runner.contexts) == 1
    assert (
        runner.contexts[0].source_class_instance_identity_id
        == explicit_source_identity_id
    )
