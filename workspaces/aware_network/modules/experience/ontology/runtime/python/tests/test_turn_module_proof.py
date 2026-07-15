from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_history.stable_ids import stable_branch_id
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from ._experience_runtime_test_paths import REPO_ROOT


EXPERIENCE_TURN_CLASS_FQN = "aware_experience.turn.Turn"


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
    for python_root in _experience_meta_python_roots(repo_root):
        if python_root.exists():
            monkeypatch.syspath_prepend(str(python_root))


def _build_experience_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    from aware_experience.handlers._generated import (  # noqa: WPS433
        meta_handlers as experience_meta_handlers,
    )
    from aware_reactivity.handlers._generated import (  # noqa: WPS433
        meta_handlers as reactivity_meta_handlers,
    )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
        bootstrap_modules=(
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
    )
    assert runtime.context is not None
    return runtime


@pytest.mark.asyncio
async def test_turn_build_then_add_feedback_module_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_history_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.stable_ids import (
        stable_turn_feedback_id,
        stable_turn_id,
    )

    environment_id = uuid5(NAMESPACE_URL, "aware://tests/experience/turn/environment")
    target_actor_id = uuid5(NAMESPACE_URL, "aware://tests/experience/turn/actor")
    turn_key = "reactive-turn-0001"
    mailbox_key = f"{environment_id}:{target_actor_id}"

    turn_id = stable_turn_id(
        environment_id=environment_id,
        target_actor_id=target_actor_id,
        key=turn_key,
    )
    feedback0_id = stable_turn_feedback_id(turn_id=turn_id, sequence=0)
    feedback1_id = stable_turn_feedback_id(turn_id=turn_id, sequence=1)

    boot_thread_id = uuid5(NAMESPACE_URL, "aware://tests/experience/turn/thread")
    boot_branch_id = stable_branch_id(
        environment_id=environment_id, thread_id=boot_thread_id
    )

    lane = LaneIds(
        branch_id=boot_branch_id,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Turn",
            root_class_fqn=EXPERIENCE_TURN_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=EXPERIENCE_TURN_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "environment_id": environment_id,
                        "target_actor_id": target_actor_id,
                        "key": turn_key,
                        "mailbox_key": mailbox_key,
                        "max_attempts": 2,
                        "created_at_unix_ms": 1_000,
                        "accepted_at_unix_ms": 1_000,
                        "idempotency_key": "idempotency-1",
                        "payload": {
                            "program_ref": "conversation_default:HumanConversationMessage_v1"
                        },
                    },
                    expected_root_object_id=turn_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=EXPERIENCE_TURN_CLASS_FQN,
                    function_name="add_feedback",
                    object_id=ROOT_OBJECT_ID,
                    args=[
                        0,
                        "dispatch",
                        "requested",
                        1_001,
                        "requested",
                        {"sequence": 0},
                    ],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=EXPERIENCE_TURN_CLASS_FQN,
                    function_name="add_feedback",
                    object_id=ROOT_OBJECT_ID,
                    args=[
                        1,
                        "execute",
                        "running",
                        1_002,
                        "running",
                        {"sequence": 1},
                    ],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=EXPERIENCE_TURN_CLASS_FQN,
                    function_name="finish_terminal",
                    object_id=ROOT_OBJECT_ID,
                    args=[
                        "succeeded",
                        1_003,
                        "program turn applied",
                        None,
                        None,
                        [],
                    ],
                ),
            ],
        )

        assertions.expect_root(turn_id)
        assertions.expect_instance(turn_id)
        assertions.expect_instance(feedback0_id)
        assertions.expect_instance(feedback1_id)
        assertions.expect_edge(source_id=turn_id, target_id=feedback0_id)
        assertions.expect_edge(source_id=turn_id, target_id=feedback1_id)

        assertions.expect_primitive(
            instance_id=UUID(str(feedback0_id)),
            field_name="stage",
            expected="dispatch",
        )
        assertions.expect_primitive(
            instance_id=UUID(str(feedback0_id)),
            field_name="status",
            expected="requested",
        )
        assertions.expect_primitive(
            instance_id=UUID(str(feedback1_id)),
            field_name="stage",
            expected="execute",
        )
        assertions.expect_primitive(
            instance_id=UUID(str(feedback1_id)),
            field_name="status",
            expected="running",
        )
        assertions.expect_primitive(
            instance_id=UUID(str(turn_id)),
            field_name="state",
            expected="terminal",
        )
        assertions.expect_primitive(
            instance_id=UUID(str(turn_id)),
            field_name="terminal_status",
            expected="succeeded",
        )
        assertions.expect_primitive(
            instance_id=UUID(str(turn_id)),
            field_name="result_summary",
            expected="program turn applied",
        )
        assert result.root_object_id == turn_id
