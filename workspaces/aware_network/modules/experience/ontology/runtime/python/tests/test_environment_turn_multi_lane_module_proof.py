from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

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
    MultiLaneProofCall,
    ProofCall,
    ROOT_OBJECT_ID,
    run_multi_lane_meta_runtime_proof,
)
from ._experience_runtime_test_paths import REPO_ROOT


ENVIRONMENT_ENVIRONMENT_CLASS_FQN = "aware_environment.environment.Environment"
ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN = (
    "aware_environment.environment.EnvironmentProfileConfig"
)
ENVIRONMENT_PROCESS_CONFIG_CLASS_FQN = "aware_environment.process.ProcessConfig"
ENVIRONMENT_THREAD_CONFIG_CLASS_FQN = "aware_environment.thread.ThreadConfig"
EXPERIENCE_TURN_CLASS_FQN = "aware_experience.turn.Turn"


def _experience_environment_meta_package_manifest_paths(
    repo_root: Path,
) -> tuple[Path, ...]:
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


def _experience_environment_meta_python_roots(
    repo_root: Path,
) -> tuple[Path, ...]:
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
        / "workspaces/aware_network/modules/environment/ontology/runtime/python",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/runtime/python",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/runtime/python",
    )


def _prepend_experience_environment_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for python_root in _experience_environment_meta_python_roots(repo_root):
        if python_root.exists():
            monkeypatch.syspath_prepend(str(python_root))


def _build_experience_environment_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    from aware_experience.handlers._generated import (  # noqa: WPS433
        meta_handlers as experience_meta_handlers,
    )
    from aware_environment.handlers._generated import (  # noqa: WPS433
        meta_handlers as environment_meta_handlers,
    )
    from aware_reactivity.handlers._generated import (  # noqa: WPS433
        meta_handlers as reactivity_meta_handlers,
    )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_environment_meta_package_manifest_paths(
            repo_root
        ),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, environment_meta_handlers),
            ),
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
                cast(Any, environment_meta_handlers),
            ),
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
async def test_meta_runtime_multi_lane_proof_executes_ordered_cross_opg_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_environment_meta_python_roots(
        repo_root=repo_root,
        monkeypatch=monkeypatch,
    )

    import aware_history_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_environment_ontology  # noqa: F401
    from aware_environment_ontology.stable_ids import (
        stable_environment_id,
        stable_environment_profile_config_id,
        stable_process_id,
        stable_process_config_id,
        stable_thread_id,
        stable_thread_config_id,
    )
    from aware_experience_ontology.stable_ids import (
        stable_turn_feedback_id,
        stable_turn_id,
    )

    environment_key = "multi-lane-proof-env"
    environment_id = stable_environment_id(key=environment_key)
    environment_profile_config_id = stable_environment_profile_config_id(
        environment_config_id=environment_id,
        key="os.default",
    )
    boot_process_config_id = stable_process_config_id(
        environment_profile_config_id=environment_profile_config_id,
        key="environment",
    )
    boot_process_id = stable_process_id(
        process_config_id=boot_process_config_id,
        key="environment",
    )
    boot_thread_config_id = stable_thread_config_id(
        process_config_id=boot_process_config_id,
        key="bootstrap",
    )
    boot_thread_id = stable_thread_id(
        thread_config_id=boot_thread_config_id,
        process_id=boot_process_id,
        key="bootstrap",
    )
    boot_branch_id = stable_branch_id(
        environment_id=environment_id, thread_id=boot_thread_id
    )
    lane = LaneIds(
        branch_id=boot_branch_id,
    )

    process_config_id = stable_process_config_id(
        environment_profile_config_id=environment_profile_config_id,
        key="worker",
    )
    process_id = stable_process_id(
        process_config_id=process_config_id,
        key="worker",
    )
    thread_config_id = stable_thread_config_id(
        process_config_id=process_config_id,
        key="worker-main",
    )
    thread_id = stable_thread_id(
        thread_config_id=thread_config_id,
        process_id=process_id,
        key="worker-main",
    )
    target_actor_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/runtime/multi-lane-proof/target-actor",
    )
    turn_key = "multi-lane-proof-turn-0001"
    turn_id = stable_turn_id(
        environment_id=environment_id,
        target_actor_id=target_actor_id,
        key=turn_key,
    )
    feedback_id = stable_turn_feedback_id(turn_id=turn_id, sequence=0)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_environment_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        results, assertions_by_opg = await run_multi_lane_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            calls=[
                MultiLaneProofCall(
                    opg_name="Environment",
                    root_class_fqn=ENVIRONMENT_ENVIRONMENT_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=ENVIRONMENT_ENVIRONMENT_CLASS_FQN,
                        function_name="build",
                        args=[
                            environment_key,
                            "Multi Lane Proof Environment",
                            None,
                        ],
                        expected_root_object_id=environment_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Environment",
                    root_class_fqn=ENVIRONMENT_ENVIRONMENT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ENVIRONMENT_ENVIRONMENT_CLASS_FQN,
                        function_name="apply_profile",
                        object_id=ROOT_OBJECT_ID,
                        args=[
                            environment_profile_config_id,
                            "Default OS",
                            None,
                            "active",
                            {},
                        ],
                        allow_noop_commit=True,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="EnvironmentProfileConfig",
                    root_class_fqn=ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "environment_config_id": environment_id,
                            "key": "os.default",
                            "title": "Default OS",
                            "description": None,
                            "narrative": None,
                        },
                        expected_root_object_id=environment_profile_config_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="EnvironmentProfileConfig",
                    root_class_fqn=ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                        function_name="create_process_config",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "type": "workspace",
                            "key": "worker",
                            "title": "Worker",
                            "description": None,
                            "shape": None,
                            "position": None,
                            "is_default": False,
                            "narrative": None,
                            "intent": None,
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="EnvironmentProfileConfig",
                    root_class_fqn=ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ENVIRONMENT_PROCESS_CONFIG_CLASS_FQN,
                        function_name="create_process",
                        object_id=process_config_id,
                        args=["worker", "Worker", None],
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="EnvironmentProfileConfig",
                    root_class_fqn=ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ENVIRONMENT_PROCESS_CONFIG_CLASS_FQN,
                        function_name="create_thread_config",
                        object_id=process_config_id,
                        kwargs={
                            "key": "worker-main",
                            "title": "Worker Main",
                            "description": None,
                            "workspace_view_key": None,
                            "position": None,
                            "is_default": False,
                            "narrative": None,
                            "intent": None,
                            "state_prompt_template": None,
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="EnvironmentProfileConfig",
                    root_class_fqn=ENVIRONMENT_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ENVIRONMENT_THREAD_CONFIG_CLASS_FQN,
                        function_name="create_thread",
                        object_id=thread_config_id,
                        args=[process_id, "worker-main", "Worker Main", None, True],
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Turn",
                    root_class_fqn=EXPERIENCE_TURN_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=EXPERIENCE_TURN_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "environment_id": environment_id,
                            "target_actor_id": target_actor_id,
                            "key": turn_key,
                            "mailbox_key": f"{environment_id}:{target_actor_id}",
                            "max_attempts": 1,
                            "created_at_unix_ms": 1_000,
                            "accepted_at_unix_ms": 1_000,
                            "idempotency_key": "multi-lane-proof-idem",
                            "payload": {"proof": "multi-lane"},
                        },
                        expected_root_object_id=turn_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Turn",
                    root_class_fqn=EXPERIENCE_TURN_CLASS_FQN,
                    call=ProofCall(
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
                ),
            ],
        )

        assert set(results.keys()) == {
            "Environment",
            "EnvironmentProfileConfig",
            "Turn",
        }
        environment_assertions = assertions_by_opg["Environment"]
        environment_profile_assertions = assertions_by_opg["EnvironmentProfileConfig"]
        turn_assertions = assertions_by_opg["Turn"]

        environment_assertions.expect_root(environment_id)
        environment_profile_assertions.expect_root(environment_profile_config_id)
        environment_profile_assertions.expect_instance(thread_id)

        turn_assertions.expect_root(turn_id)
        turn_assertions.expect_instance(feedback_id)
        turn_assertions.expect_edge(source_id=turn_id, target_id=feedback_id)
        turn_assertions.expect_primitive(
            instance_id=feedback_id,
            field_name="stage",
            expected="dispatch",
        )

        assert (
            results["Environment"].branch_id
            == results["EnvironmentProfileConfig"].branch_id
            == results["Turn"].branch_id
        )
