from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest

from aware_history.stable_ids import stable_branch_id
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.package_index import MetaRuntimePackageIndexEntry
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from aware_environment.handlers._generated import (
    meta_handlers as environment_meta_handlers,
)

from ._environment_runtime_test_paths import (
    REPO_ROOT,
    environment_package_manifest_paths,
)

_ENVIRONMENT_CLASS_FQN = "aware_environment.environment.Environment"
_ENVIRONMENT_PROFILE_CLASS_FQN = "aware_environment.environment.EnvironmentProfile"
_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN = (
    "aware_environment.environment.EnvironmentProfileConfig"
)
_PROCESS_CLASS_FQN = "aware_environment.process.Process"
_PROCESS_CONFIG_CLASS_FQN = "aware_environment.process.ProcessConfig"
_THREAD_CLASS_FQN = "aware_environment.thread.Thread"
_THREAD_CONFIG_CLASS_FQN = "aware_environment.thread.ThreadConfig"

_ENVIRONMENT_META_HANDLERS_ANY: Any = environment_meta_handlers
_ENVIRONMENT_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ENVIRONMENT_META_HANDLERS_ANY,
)
_ENVIRONMENT_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ENVIRONMENT_META_HANDLERS_ANY,
)


def _environment_module_proof_package_manifest_paths(
    repo_root: Path,
) -> tuple[Path, ...]:
    return environment_package_manifest_paths(repo_root)


def _package_entries_by_manifest_path(
    *,
    repo_root: Path,
    manifest_paths: tuple[Path, ...],
) -> dict[Path, MetaRuntimePackageIndexEntry]:
    from aware_meta.manifest.loader import load_aware_toml_spec

    entries: dict[Path, MetaRuntimePackageIndexEntry] = {}
    modules_root = repo_root / "modules"
    for manifest_path in manifest_paths:
        resolved_manifest_path = manifest_path.resolve()
        spec = load_aware_toml_spec(toml_path=resolved_manifest_path)
        try:
            module_id = resolved_manifest_path.relative_to(modules_root).parts[0]
        except ValueError:
            module_id = str(spec.package.package_name).strip()
        entries[resolved_manifest_path] = MetaRuntimePackageIndexEntry(
            module_id=module_id,
            package_name=str(spec.package.package_name).strip(),
            fqn_prefix=str(spec.package.fqn_prefix).strip(),
            manifest_path=resolved_manifest_path,
            dependency_package_names=tuple(
                str(dependency.package_name).strip()
                for dependency in spec.dependencies
                if str(dependency.package_name).strip()
            ),
        )
    return entries


def _build_environment_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    package_manifest_paths = _environment_module_proof_package_manifest_paths(
        repo_root,
    )
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ENVIRONMENT_META_HANDLER_MODULE,),
        bootstrap_modules=(_ENVIRONMENT_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=_package_entries_by_manifest_path(
            repo_root=repo_root,
            manifest_paths=package_manifest_paths,
        ),
        package_graph_cache_request_signature=(
            "pytest:environment-module-proof-meta-harness"
        ),
        source_analysis_allowed_manifest_paths=package_manifest_paths,
    )
    assert runtime.context is not None
    return runtime


def _payload_value(payload: object) -> object:
    if isinstance(payload, dict) and "value" in payload:
        return payload["value"]
    return payload


@pytest.mark.asyncio
async def test_environment_build_clean_territory_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_meta_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_environment_ontology  # noqa: F401
    from aware_environment_ontology.stable_ids import (
        stable_environment_config_id,
        stable_environment_id,
        stable_environment_ontology_id,
        stable_environment_profile_id,
        stable_environment_profile_config_id,
        stable_process_id,
        stable_process_config_id,
        stable_thread_id,
        stable_thread_config_id,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_environment_meta_runtime(
            repo_root,
            aware_root=aware_root,
        )
        env_id = stable_environment_id(key="test.environment")
        env_config_id = stable_environment_config_id(handle="test.environment")
        lane_profile_config_id = stable_environment_profile_config_id(
            environment_config_id=env_config_id,
            key="os.default",
        )
        lane_profile_id = stable_environment_profile_id(
            environment_id=env_id,
            profile_config_id=lane_profile_config_id,
        )
        lane_process_config_id = stable_process_config_id(
            environment_profile_config_id=lane_profile_config_id,
            key="environment",
        )
        lane_process_id = stable_process_id(
            environment_profile_id=lane_profile_id,
            process_config_id=lane_process_config_id,
            key="environment",
        )
        lane_thread_config_id = stable_thread_config_id(
            process_config_id=lane_process_config_id,
            key="bootstrap",
        )
        lane_thread_id = stable_thread_id(
            thread_config_id=lane_thread_config_id,
            process_id=lane_process_id,
            key="bootstrap",
        )
        lane_branch_id = stable_branch_id(
            environment_id=env_id, thread_id=lane_thread_id
        )

        lane = LaneIds(
            branch_id=lane_branch_id,
        )
        ontology_id = UUID("11111111-1111-4111-8111-111111111111")
        environment_ontology_id = stable_environment_ontology_id(
            environment_id=env_id,
            ontology_id=ontology_id,
        )

        environment_result, environment_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Environment",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ENVIRONMENT_CLASS_FQN,
                    function_name="build",
                    args=["test.environment", "Test Environment", None],
                    expected_root_object_id=env_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_ENVIRONMENT_CLASS_FQN,
                    function_name="attach_ontology",
                    object_id=ROOT_OBJECT_ID,
                    args=[ontology_id, "runtime", "active", "Kernel", None],
                ),
            ],
        )

        environment_assertions.expect_root(env_id)
        environment_assertions.expect_instance(env_id)
        environment_assertions.expect_instance(environment_ontology_id)
        environment_assertions.expect_edge(
            source_id=env_id,
            target_id=environment_ontology_id,
        )
        source_ids = {
            ci.source_object_id for ci in environment_assertions.oig.class_instances
        }
        assert lane_process_id not in source_ids
        assert lane_thread_id not in source_ids
        constructor_payload = _payload_value(environment_result.responses[0].payload)
        assert isinstance(constructor_payload, dict)
        assert constructor_payload["config_id"] == str(env_config_id)
        assert "environment_experience_profile_id" not in constructor_payload
        assert environment_result.root_object_id == env_id


@pytest.mark.asyncio
async def test_environment_create_process_then_create_thread(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_meta_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_environment_ontology  # noqa: F401
    from aware_environment_ontology.stable_ids import (
        stable_environment_config_id,
        stable_environment_id,
        stable_environment_profile_id,
        stable_environment_profile_config_id,
        stable_process_id,
        stable_process_config_id,
        stable_thread_id,
        stable_thread_config_id,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_environment_meta_runtime(
            repo_root,
            aware_root=aware_root,
        )
        env_id = stable_environment_id(key="test.environment.2")
        environment_config_id = stable_environment_config_id(
            handle="test.environment.2",
        )
        environment_profile_config_id = stable_environment_profile_config_id(
            environment_config_id=environment_config_id,
            key="os.default",
        )
        environment_profile_id = stable_environment_profile_id(
            environment_id=env_id,
            profile_config_id=environment_profile_config_id,
        )
        lane_process_config_id = stable_process_config_id(
            environment_profile_config_id=environment_profile_config_id,
            key="environment",
        )
        lane_process_id = stable_process_id(
            environment_profile_id=environment_profile_id,
            process_config_id=lane_process_config_id,
            key="environment",
        )
        lane_thread_config_id = stable_thread_config_id(
            process_config_id=lane_process_config_id,
            key="bootstrap",
        )
        lane_thread_id = stable_thread_id(
            thread_config_id=lane_thread_config_id,
            process_id=lane_process_id,
            key="bootstrap",
        )
        lane_branch_id = stable_branch_id(
            environment_id=env_id, thread_id=lane_thread_id
        )

        lane = LaneIds(
            branch_id=lane_branch_id,
        )

        worker_process_config_id = stable_process_config_id(
            environment_profile_config_id=environment_profile_config_id,
            key="worker",
        )
        worker_process_id = stable_process_id(
            environment_profile_id=environment_profile_id,
            process_config_id=worker_process_config_id,
            key="worker",
        )
        worker_thread_config_id = stable_thread_config_id(
            process_config_id=worker_process_config_id,
            key="worker-main",
        )
        worker_thread_id = stable_thread_id(
            thread_config_id=worker_thread_config_id,
            process_id=worker_process_id,
            key="worker-main",
        )

        environment_result, environment_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Environment",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ENVIRONMENT_CLASS_FQN,
                    function_name="build",
                    args=["test.environment.2", "Test Environment", None],
                    expected_root_object_id=env_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_ENVIRONMENT_CLASS_FQN,
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
            ],
        )

        profile_config_result, profile_config_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                branch_id=environment_profile_config_id,
            ),
            opg_name="EnvironmentProfileConfig",
            root_class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    function_name="build_via_environment_config",
                    args=[
                        environment_config_id,
                        "os.default",
                        "Default OS",
                        None,
                        None,
                    ],
                    expected_root_object_id=environment_profile_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    function_name="create_process_config",
                    object_id=ROOT_OBJECT_ID,
                    args=[
                        "workspace",
                        "worker",
                        "Worker",
                        None,
                        None,
                        None,
                        False,
                        None,
                    ],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_PROCESS_CONFIG_CLASS_FQN,
                    function_name="create_thread_config",
                    object_id=worker_process_config_id,
                    args=["worker-main", "Main", None, None, None, False, None, None],
                ),
            ],
        )

        profile_result, profile_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                branch_id=environment_profile_id,
            ),
            opg_name="EnvironmentProfile",
            root_class_fqn=_ENVIRONMENT_PROFILE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_ENVIRONMENT_PROFILE_CLASS_FQN,
                    function_name="build_via_environment",
                    args=[
                        env_id,
                        environment_profile_config_id,
                        "Default OS",
                        None,
                        "active",
                        {},
                    ],
                    expected_root_object_id=environment_profile_id,
                    allow_noop_commit=True,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_ENVIRONMENT_PROFILE_CLASS_FQN,
                    function_name="create_process",
                    object_id=ROOT_OBJECT_ID,
                    args=[worker_process_config_id, "worker", "Worker", None],
                    allow_noop_commit=True,
                ),
            ],
        )

        process_result, process_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                branch_id=worker_process_id,
            ),
            opg_name="Process",
            root_class_fqn=_PROCESS_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_PROCESS_CLASS_FQN,
                    function_name="build_via_environment_profile",
                    args=[
                        environment_profile_id,
                        worker_process_config_id,
                        "worker",
                        "Worker",
                        None,
                    ],
                    expected_root_object_id=worker_process_id,
                    allow_noop_commit=True,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_PROCESS_CLASS_FQN,
                    function_name="create_thread",
                    object_id=ROOT_OBJECT_ID,
                    args=[worker_thread_config_id, "worker-main", "Main", None, True],
                    allow_noop_commit=True,
                ),
            ],
        )

        thread_result, thread_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                branch_id=worker_thread_id,
            ),
            opg_name="Thread",
            root_class_fqn=_THREAD_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_THREAD_CLASS_FQN,
                    function_name="build_via_process",
                    args=[
                        worker_process_id,
                        worker_thread_config_id,
                        "worker-main",
                        "Main",
                        None,
                        True,
                    ],
                    expected_root_object_id=worker_thread_id,
                    allow_noop_commit=True,
                ),
            ],
        )

        environment_assertions.expect_root(env_id)
        assert environment_result.root_object_id == env_id

        profile_config_assertions.expect_root(environment_profile_config_id)
        profile_config_assertions.expect_instance(environment_profile_config_id)
        profile_config_assertions.expect_instance(worker_process_config_id)
        profile_config_assertions.expect_instance(worker_thread_config_id)
        profile_config_assertions.expect_edge(
            source_id=environment_profile_config_id,
            target_id=worker_process_config_id,
        )
        profile_config_assertions.expect_edge(
            source_id=worker_process_config_id, target_id=worker_thread_config_id
        )
        assert profile_config_result.root_object_id == environment_profile_config_id

        profile_assertions.expect_root(environment_profile_id)
        profile_assertions.expect_instance(environment_profile_id)
        assert profile_result.root_object_id == environment_profile_id

        process_assertions.expect_root(worker_process_id)
        process_assertions.expect_instance(worker_process_id)
        assert process_result.root_object_id == worker_process_id

        thread_assertions.expect_root(worker_thread_id)
        thread_assertions.expect_instance(worker_thread_id)
        assert thread_result.root_object_id == worker_thread_id
