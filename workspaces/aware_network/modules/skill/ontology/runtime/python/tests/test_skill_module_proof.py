from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from _skill_runtime_test_paths import REPO_ROOT, install_skill_dependency_paths

install_skill_dependency_paths()

from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    SourceObjectId,
    run_meta_runtime_proof,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_skill.handlers._generated import (
    meta_handlers as skill_meta_handlers,
)

_API_PACKAGE_CLASS_FQN = "aware_api.api.ApiPackage"
_SKILL_CONFIG_CLASS_FQN = "aware_skill.skill.SkillConfig"
_SKILL_CONFIG_API_CLASS_FQN = "aware_skill.skill.SkillConfigApi"
_SKILL_CONFIG_API_ENDPOINT_CLASS_FQN = "aware_skill.skill.SkillConfigApiEndpoint"
_SKILL_CONFIG_EXPERIENCE_CLASS_FQN = "aware_skill.skill.SkillConfigExperience"
_SKILL_CONFIG_STEP_CLASS_FQN = "aware_skill.skill.SkillConfigStep"
_SKILL_RUN_CLASS_FQN = "aware_skill.skill.SkillRun"
_SKILL_PACKAGE_CLASS_FQN = "aware_skill.skill.SkillPackage"

_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)
_SKILL_META_HANDLERS_ANY: Any = skill_meta_handlers
_SKILL_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SKILL_META_HANDLERS_ANY,
)
_SKILL_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SKILL_META_HANDLERS_ANY,
)


def _skill_module_proof_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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
        repo_root
        / "workspaces/aware_network/modules/skill/ontology/structure/aware.toml",
    )


def _build_skill_module_proof_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_skill_module_proof_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            _API_META_HANDLER_MODULE,
            _SKILL_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _API_META_BOOTSTRAP_MODULE,
            _SKILL_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _runtime_index(runtime: MetaGraphRuntime) -> MetaGraphRuntimeIndex:
    assert runtime.context is not None
    return runtime.context.index


def _class_configs_by_name(assertions: Any) -> dict[str, ClassConfig]:
    return {
        class_config.name: class_config
        for class_config in assertions._class_configs_by_id.values()  # noqa: SLF001
        if class_config.name is not None
    }


def _payload_value(payload: object) -> object:
    if isinstance(payload, dict) and "value" in payload:
        return payload["value"]
    return payload


def _select_runtime_inline_request_class_config(runtime_index) -> ClassConfig:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        if class_config.value_mode == ClassValueMode.inline_value:
            return class_config
    raise AssertionError(
        "Expected one compiled inline_value ClassConfig for the Skill module proof"
    )


async def _object_instance_graph_commit_id_for_head(
    *,
    branch_id: UUID,
    projection_hash: str,
) -> UUID:
    from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
    from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id

    head_commit = await FSCommitStore().head_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head_commit is not None
    return stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=head_commit.object_instance_graph_identity_id,
        commit_id=head_commit.commit.id,
    )


@pytest.mark.asyncio
async def test_skill_config_and_package_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_api_ontology  # noqa: F401
    import aware_code_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_skill_ontology  # noqa: F401
    from aware_api_ontology.stable_ids import (
        stable_api_call_id,
        stable_api_id,
        stable_api_package_id,
    )
    from aware_code.stable_ids import stable_code_package_id
    from aware_skill_ontology.skill.skill_run import SkillRun
    from aware_skill_ontology.skill.skill_run_enums import SkillRunStatus
    from aware_skill_ontology.stable_ids import (
        stable_skill_config_api_endpoint_id,
        stable_skill_config_api_id,
        stable_skill_config_experience_id,
        stable_skill_config_id,
        stable_skill_config_step_id,
        stable_skill_config_step_target_id,
        stable_skill_config_target_id,
        stable_skill_package_api_package_id,
        stable_skill_package_id,
        stable_skill_run_id,
        stable_skill_run_step_id,
    )
    from aware_api_runtime.package_ref_resolution import ApiRuntimePackageRef
    from aware_skill.execution import (
        SkillRunHarnessRequest,
        SkillStepApiCallInput,
        materialize_skill_run,
        materialize_skill_run_from_package_refs,
        resolve_committed_skill_execution_plan,
    )
    from aware_skill.package_ref_resolution import SkillRuntimePackageRef

    skill_name = "door-control"
    api_name = "home-devices"
    capability_name = "door"
    endpoint_name = "open"
    run_key = "door-control/run/001"
    target_name = "front-door"
    source_package_name = "aware_skill_test_source_package"
    expected_projection_experience_id = uuid4()
    expected_projection_experience_graph_identity_id = uuid4()

    expected_api_id = stable_api_id(name=api_name)
    expected_api_package_id = stable_api_package_id(name="home-devices-api")
    expected_skill_config_id = stable_skill_config_id(name=skill_name)
    expected_skill_config_step_id = stable_skill_config_step_id(
        skill_config_id=expected_skill_config_id,
        position=1,
    )
    expected_skill_config_api_id = stable_skill_config_api_id(
        skill_config_id=expected_skill_config_id,
        api_id=expected_api_id,
    )
    expected_skill_run_id = stable_skill_run_id(
        skill_config_id=expected_skill_config_id,
        run_key=run_key,
    )
    expected_skill_run_step_id = stable_skill_run_step_id(
        skill_run_id=expected_skill_run_id,
        skill_config_step_id=expected_skill_config_step_id,
    )
    expected_skill_package_id = stable_skill_package_id(name=skill_name)
    expected_skill_package_api_package_id = stable_skill_package_api_package_id(
        skill_package_id=expected_skill_package_id,
        api_package_id=expected_api_package_id,
    )
    expected_source_code_package_id = stable_code_package_id(
        package_name=source_package_name,
        language="aware",
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_skill_module_proof_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        idx = _runtime_index(runtime)
        request_class_config = _select_runtime_inline_request_class_config(idx)
        opg_names = {(opg.name or "").strip() for opg in idx.opg_by_hash.values()}
        assert {
            "Api",
            "ApiCall",
            "ApiPackage",
            "CodePackage",
            "SkillConfig",
            "SkillPackage",
            "SkillRun",
        } <= opg_names
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="Api",
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="ApiCall",
        )
        api_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="ApiPackage",
        )
        skill_config_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="SkillConfig",
        )
        skill_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="SkillPackage",
        )
        skill_run_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="SkillRun",
        )
        api_package_opg = idx.opg_by_hash[api_package_projection_hash]
        skill_config_opg = idx.opg_by_hash[skill_config_projection_hash]
        skill_package_opg = idx.opg_by_hash[skill_package_projection_hash]
        skill_run_opg = idx.opg_by_hash[skill_run_projection_hash]

        lane = LaneIds(
            actor_id=uuid4(),
        )
        api_branch_id = uuid4()
        endpoint_ref = f"{api_name}.{capability_name}.{endpoint_name}"
        api_snapshot = await commit_api_reference_snapshot(
            index=idx,
            actor_id=lane.actor_id,
            branch_id=api_branch_id,
            projection_hash=api_projection_hash,
            api_name=api_name,
            endpoint_refs=(endpoint_ref,),
            endpoint_request_class_config_ids={
                endpoint_ref: request_class_config.id,
            },
        )
        assert api_snapshot.api.id == expected_api_id
        expected_api_endpoint_id = api_snapshot.endpoint_ids_by_ref[endpoint_ref]
        api_call_key = uuid4()
        expected_api_call_id = stable_api_call_id(
            api_capability_endpoint_id=expected_api_endpoint_id,
            call_key=api_call_key,
        )
        api_object_instance_graph_commit_id = (
            api_snapshot.object_instance_graph_commit_id
        )

        api_package_result, api_package_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                actor_id=lane.actor_id,
                branch_id=api_branch_id,
            ),
            opg_name="ApiPackage",
            projection_hash=api_package_projection_hash,
            root_class_fqn=_API_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_API_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": "home-devices-api",
                        "api_id": expected_api_id,
                        "api_object_instance_graph_commit_id": api_object_instance_graph_commit_id,
                        "fqn_prefix": "aware_home_devices.api",
                        "manifest_relative_path": "aware.api.toml",
                    },
                    expected_root_object_id=expected_api_package_id,
                ),
            ],
        )
        assert api_package_result.root_object_id == expected_api_package_id
        api_package_assertions.expect_root(expected_api_package_id)
        api_package_assertions.expect_instance(expected_api_package_id)
        api_package_assertions.expect_primitive(
            instance_id=expected_api_package_id,
            field_name="name",
            expected="home-devices-api",
        )
        api_package_api_fk_value = api_package_assertions.primitive(
            instance_id=expected_api_package_id,
            field_name="api_id",
        )
        assert api_package_api_fk_value in {expected_api_id, str(expected_api_id)}
        api_package_api_commit_fk_value = api_package_assertions.primitive(
            instance_id=expected_api_package_id,
            field_name="api_object_instance_graph_commit_id",
        )
        assert api_package_api_commit_fk_value in {
            api_object_instance_graph_commit_id,
            str(api_object_instance_graph_commit_id),
        }
        api_package_oig_commit_id = await _object_instance_graph_commit_id_for_head(
            branch_id=api_package_result.branch_id,
            projection_hash=api_package_opg.projection_hash,
        )

        expected_skill_config_api_endpoint_id = stable_skill_config_api_endpoint_id(
            skill_config_api_id=expected_skill_config_api_id,
            api_endpoint_id=expected_api_endpoint_id,
            capability_name=capability_name,
            name=endpoint_name,
        )
        expected_skill_config_experience_id = stable_skill_config_experience_id(
            skill_config_id=expected_skill_config_id,
            projection_experience_id=expected_projection_experience_id,
        )
        expected_skill_config_target_id = stable_skill_config_target_id(
            skill_config_experience_id=expected_skill_config_experience_id,
            projection_experience_graph_identity_id=expected_projection_experience_graph_identity_id,
            name=target_name,
        )
        expected_skill_config_step_target_id = stable_skill_config_step_target_id(
            skill_config_step_id=expected_skill_config_step_id,
            skill_config_target_id=expected_skill_config_target_id,
        )

        config_result, config_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                actor_id=lane.actor_id,
                branch_id=uuid4(),
            ),
            opg_name="SkillConfig",
            projection_hash=skill_config_projection_hash,
            root_class_fqn=_SKILL_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SKILL_CONFIG_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": skill_name,
                        "description": "Reusable skill for controlled door actions",
                    },
                    expected_root_object_id=expected_skill_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_CONFIG_CLASS_FQN,
                    function_name="add_api",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "api_id": expected_api_id,
                        "description": "Home Devices API grouping.",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_CONFIG_API_CLASS_FQN,
                    function_name="add_api_endpoint",
                    object_id=SourceObjectId(expected_skill_config_api_id),
                    kwargs={
                        "api_endpoint_id": expected_api_endpoint_id,
                        "capability_name": capability_name,
                        "name": endpoint_name,
                        "description": "Skill-owned endpoint requirement.",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_CONFIG_CLASS_FQN,
                    function_name="add_step",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "position": 1,
                        "skill_config_api_endpoint_id": expected_skill_config_api_endpoint_id,
                        "instruction": "Read the requested door state before acting.",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_CONFIG_CLASS_FQN,
                    function_name="add_experience",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "projection_experience_id": expected_projection_experience_id,
                        "description": "Home projection experience namespace.",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_CONFIG_EXPERIENCE_CLASS_FQN,
                    function_name="add_target",
                    object_id=SourceObjectId(expected_skill_config_experience_id),
                    kwargs={
                        "projection_experience_graph_identity_id": expected_projection_experience_graph_identity_id,
                        "name": target_name,
                        "description": "Experience identity for the front door.",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_CONFIG_STEP_CLASS_FQN,
                    function_name="add_target",
                    object_id=SourceObjectId(expected_skill_config_step_id),
                    kwargs={
                        "skill_config_target_id": expected_skill_config_target_id,
                        "description": "This step applies to the front door target.",
                    },
                ),
            ],
        )
        assert config_result.root_object_id == expected_skill_config_id
        config_assertions.expect_root(expected_skill_config_id)
        config_assertions.expect_instance(expected_skill_config_id)
        config_assertions.expect_instance(expected_skill_config_step_id)
        config_assertions.expect_instance(expected_skill_config_experience_id)
        config_assertions.expect_instance(expected_skill_config_target_id)
        config_assertions.expect_instance(expected_skill_config_step_target_id)
        config_assertions.expect_instance(expected_skill_config_api_id)
        config_assertions.expect_instance(expected_skill_config_api_endpoint_id)
        skill_config_object_instance_graph_commit_id = (
            await _object_instance_graph_commit_id_for_head(
                branch_id=config_result.branch_id,
                projection_hash=skill_config_opg.projection_hash,
            )
        )
        config_assertions.expect_primitive(
            instance_id=expected_skill_config_id,
            field_name="name",
            expected=skill_name,
        )
        config_assertions.expect_primitive(
            instance_id=expected_skill_config_step_id,
            field_name="instruction",
            expected="Read the requested door state before acting.",
        )
        step_endpoint_fk_value = config_assertions.primitive(
            instance_id=expected_skill_config_step_id,
            field_name="skill_config_api_endpoint_id",
        )
        assert step_endpoint_fk_value in {
            expected_skill_config_api_endpoint_id,
            str(expected_skill_config_api_endpoint_id),
        }
        api_fk_value = config_assertions.primitive(
            instance_id=expected_skill_config_api_id,
            field_name="api_id",
        )
        assert api_fk_value in {expected_api_id, str(expected_api_id)}
        endpoint_fk_value = config_assertions.primitive(
            instance_id=expected_skill_config_api_endpoint_id,
            field_name="api_endpoint_id",
        )
        assert endpoint_fk_value in {
            expected_api_endpoint_id,
            str(expected_api_endpoint_id),
        }
        experience_fk_value = config_assertions.primitive(
            instance_id=expected_skill_config_experience_id,
            field_name="projection_experience_id",
        )
        assert experience_fk_value in {
            expected_projection_experience_id,
            str(expected_projection_experience_id),
        }
        target_graph_identity_fk_value = config_assertions.primitive(
            instance_id=expected_skill_config_target_id,
            field_name="projection_experience_graph_identity_id",
        )
        assert target_graph_identity_fk_value in {
            expected_projection_experience_graph_identity_id,
            str(expected_projection_experience_graph_identity_id),
        }
        config_assertions.expect_primitive(
            instance_id=expected_skill_config_target_id,
            field_name="name",
            expected=target_name,
        )
        step_target_fk_value = config_assertions.primitive(
            instance_id=expected_skill_config_step_target_id,
            field_name="skill_config_target_id",
        )
        assert step_target_fk_value in {
            expected_skill_config_target_id,
            str(expected_skill_config_target_id),
        }
        config_assertions.expect_primitive(
            instance_id=expected_skill_config_api_endpoint_id,
            field_name="capability_name",
            expected=capability_name,
        )
        config_assertions.expect_primitive(
            instance_id=expected_skill_config_api_endpoint_id,
            field_name="name",
            expected=endpoint_name,
        )
        resolved_plan = await resolve_committed_skill_execution_plan(
            index=idx,
            lane=MaterializationLaneContext(
                branch_id=config_result.branch_id,
                projection_hash=skill_config_opg.projection_hash,
            ),
            skill_config_id=expected_skill_config_id,
        )
        assert resolved_plan.skill_config_id == expected_skill_config_id
        assert resolved_plan.skill_name == skill_name
        assert [step.position for step in resolved_plan.steps] == [1]
        resolved_step = resolved_plan.steps[0]
        assert resolved_step.skill_config_step_id == expected_skill_config_step_id
        assert (
            resolved_step.skill_config_api_endpoint_id
            == expected_skill_config_api_endpoint_id
        )
        assert resolved_step.api_capability_endpoint_id == expected_api_endpoint_id
        assert resolved_step.endpoint_requirement_name == endpoint_name
        assert resolved_step.capability_name == capability_name
        assert len(resolved_step.targets) == 1
        resolved_target = resolved_step.targets[0]
        assert (
            resolved_target.skill_config_step_target_id
            == expected_skill_config_step_target_id
        )
        assert resolved_target.skill_config_target_id == expected_skill_config_target_id
        assert (
            resolved_target.projection_experience_graph_identity_id
            == expected_projection_experience_graph_identity_id
        )
        assert resolved_target.name == target_name
        harness_run_key = "door-control/run/harness-001"
        harness_api_call_key = uuid4()
        expected_harness_skill_run_id = stable_skill_run_id(
            skill_config_id=expected_skill_config_id,
            run_key=harness_run_key,
        )
        expected_harness_skill_run_step_id = stable_skill_run_step_id(
            skill_run_id=expected_harness_skill_run_id,
            skill_config_step_id=expected_skill_config_step_id,
        )
        harness_result = await materialize_skill_run(
            runtime=runtime,
            index=idx,
            actor_id=lane.actor_id,
            skill_config_lane=MaterializationLaneContext(
                branch_id=config_result.branch_id,
                projection_hash=skill_config_opg.projection_hash,
            ),
            api_source_lane=MaterializationLaneContext(
                branch_id=api_branch_id,
                projection_hash=api_projection_hash,
            ),
            api_call_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash=api_call_projection_hash,
            ),
            skill_run_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash=skill_run_opg.projection_hash,
            ),
            request=SkillRunHarnessRequest(
                skill_config_id=expected_skill_config_id,
                run_key=harness_run_key,
                step_inputs=(
                    SkillStepApiCallInput(
                        skill_config_step_id=expected_skill_config_step_id,
                        request_payload={},
                        call_key=harness_api_call_key,
                        description="Skill harness API call materialization proof.",
                    ),
                ),
            ),
        )
        assert harness_result.skill_run_id == expected_harness_skill_run_id
        assert harness_result.status == SkillRunStatus.succeeded.value
        assert harness_result.commit_id is not None
        assert harness_result.head_commit_id is not None
        assert len(harness_result.steps) == 1
        harness_step = harness_result.steps[0]
        assert harness_step.skill_run_step_id == expected_harness_skill_run_step_id
        assert harness_step.skill_config_step_id == expected_skill_config_step_id
        assert harness_step.status == SkillRunStatus.succeeded.value
        assert harness_step.api_call.call_key == harness_api_call_key
        assert (
            harness_step.api_call.api_capability_endpoint_id == expected_api_endpoint_id
        )
        assert harness_step.api_call.request_class_config_id == request_class_config.id
        assert harness_step.api_call.request_model_id.int != 0
        assert harness_step.api_call.request_hash

        class_configs_by_name = _class_configs_by_name(config_assertions)
        skill_config_api_class_config = class_configs_by_name["SkillConfigApi"]
        skill_config_api_endpoint_class_config = class_configs_by_name[
            "SkillConfigApiEndpoint"
        ]
        skill_config_experience_class_config = class_configs_by_name[
            "SkillConfigExperience"
        ]
        skill_config_target_class_config = class_configs_by_name["SkillConfigTarget"]
        skill_config_step_class_config = class_configs_by_name["SkillConfigStep"]
        skill_config_step_target_class_config = class_configs_by_name[
            "SkillConfigStepTarget"
        ]
        api_class_config = class_configs_by_name["Api"]
        api_capability_endpoint_class_config = class_configs_by_name[
            "ApiCapabilityEndpoint"
        ]
        projection_experience_class_config = class_configs_by_name[
            "ProjectionExperience"
        ]
        projection_experience_graph_identity_class_config = class_configs_by_name[
            "ProjectionExperienceGraphIdentity"
        ]
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_api_class_config.id,
            target_class_config_id=api_class_config.id,
            relationship_name="api",
        )
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_api_endpoint_class_config.id,
            target_class_config_id=api_capability_endpoint_class_config.id,
            relationship_name="api_endpoint",
        )
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_step_class_config.id,
            target_class_config_id=skill_config_api_endpoint_class_config.id,
            relationship_name="skill_config_api_endpoint",
        )
        skill_config_class_config = class_configs_by_name["SkillConfig"]
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_class_config.id,
            target_class_config_id=skill_config_experience_class_config.id,
            relationship_name="experiences",
        )
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_experience_class_config.id,
            target_class_config_id=projection_experience_class_config.id,
            relationship_name="projection_experience",
        )
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_experience_class_config.id,
            target_class_config_id=skill_config_target_class_config.id,
            relationship_name="targets",
        )
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_target_class_config.id,
            target_class_config_id=projection_experience_graph_identity_class_config.id,
            relationship_name="projection_experience_graph_identity",
        )
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_step_class_config.id,
            target_class_config_id=skill_config_step_target_class_config.id,
            relationship_name="targets",
        )
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_step_target_class_config.id,
            target_class_config_id=skill_config_target_class_config.id,
            relationship_name="skill_config_target",
        )
        skill_run_class_config = class_configs_by_name["SkillRun"]
        config_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_config_class_config.id,
            target_class_config_id=skill_run_class_config.id,
            relationship_name="runs",
        )

        run_result, run_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                actor_id=lane.actor_id,
                branch_id=config_result.branch_id,
            ),
            opg_name="SkillRun",
            projection_hash=skill_run_projection_hash,
            root_class_fqn=_SKILL_RUN_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SKILL_RUN_CLASS_FQN,
                    function_name="build_via_skill_config",
                    kwargs={
                        "skill_config_id": expected_skill_config_id,
                        "run_key": run_key,
                        "status": SkillRunStatus.running.value,
                    },
                    expected_root_object_id=expected_skill_run_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_RUN_CLASS_FQN,
                    function_name="create_step",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "skill_config_step_id": expected_skill_config_step_id,
                        "api_call_id": expected_api_call_id,
                        "status": SkillRunStatus.succeeded.value,
                    },
                ),
            ],
        )
        assert run_result.root_object_id == expected_skill_run_id
        run_assertions.expect_root(expected_skill_run_id)
        run_assertions.expect_instance(expected_skill_run_id)
        run_assertions.expect_instance(expected_skill_run_step_id)
        run_assertions.expect_edge(
            source_id=expected_skill_run_id,
            target_id=expected_skill_run_step_id,
            relationship_name="steps",
        )
        run_assertions.expect_primitive(
            instance_id=expected_skill_run_id,
            field_name="run_key",
            expected=run_key,
        )
        run_assertions.expect_primitive(
            instance_id=expected_skill_run_id,
            field_name="status",
            expected=SkillRunStatus.running.value,
        )
        run_step_config_step_fk_value = run_assertions.primitive(
            instance_id=expected_skill_run_step_id,
            field_name="skill_config_step_id",
        )
        assert run_step_config_step_fk_value in {
            expected_skill_config_step_id,
            str(expected_skill_config_step_id),
        }
        run_step_api_call_fk_value = run_assertions.primitive(
            instance_id=expected_skill_run_step_id,
            field_name="api_call_id",
        )
        assert run_step_api_call_fk_value in {
            expected_api_call_id,
            str(expected_api_call_id),
        }
        run_assertions.expect_primitive(
            instance_id=expected_skill_run_step_id,
            field_name="status",
            expected=SkillRunStatus.succeeded.value,
        )

        run_class_configs_by_name = _class_configs_by_name(run_assertions)
        skill_run_step_class_config = run_class_configs_by_name["SkillRunStep"]
        api_call_class_config = run_class_configs_by_name["ApiCall"]
        run_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_run_class_config.id,
            target_class_config_id=skill_run_step_class_config.id,
            relationship_name="steps",
        )
        run_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_run_step_class_config.id,
            target_class_config_id=skill_config_step_class_config.id,
            relationship_name="skill_config_step",
        )
        run_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_run_step_class_config.id,
            target_class_config_id=api_call_class_config.id,
            relationship_name="api_call",
        )

        run_payload = _payload_value(run_result.responses[-2].payload)
        assert isinstance(run_payload, dict)
        created_run = SkillRun.model_validate(run_payload)
        assert created_run.id == expected_skill_run_id
        assert created_run.skill_config_id == expected_skill_config_id

        package_result, package_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                actor_id=lane.actor_id,
                branch_id=config_result.branch_id,
            ),
            opg_name="SkillPackage",
            projection_hash=skill_package_projection_hash,
            root_class_fqn=_SKILL_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=_SKILL_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": skill_name,
                        "skill_config_id": expected_skill_config_id,
                        "skill_config_object_instance_graph_commit_id": (
                            skill_config_object_instance_graph_commit_id
                        ),
                        "source_code_package_id": expected_source_code_package_id,
                    },
                    expected_root_object_id=expected_skill_package_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=_SKILL_PACKAGE_CLASS_FQN,
                    function_name="attach_api_package",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={"api_package_id": expected_api_package_id},
                ),
            ],
        )
        assert package_result.root_object_id == expected_skill_package_id
        package_assertions.expect_root(expected_skill_package_id)
        package_assertions.expect_instance(expected_skill_package_id)
        package_assertions.expect_instance(expected_skill_package_api_package_id)
        package_assertions.expect_primitive(
            instance_id=expected_skill_package_id,
            field_name="name",
            expected=skill_name,
        )
        skill_config_fk_value = package_assertions.primitive(
            instance_id=expected_skill_package_id,
            field_name="skill_config_id",
        )
        assert skill_config_fk_value in {
            expected_skill_config_id,
            str(expected_skill_config_id),
        }
        skill_config_commit_fk_value = package_assertions.primitive(
            instance_id=expected_skill_package_id,
            field_name="skill_config_object_instance_graph_commit_id",
        )
        assert skill_config_commit_fk_value in {
            skill_config_object_instance_graph_commit_id,
            str(skill_config_object_instance_graph_commit_id),
        }
        source_code_package_fk_value = package_assertions.primitive(
            instance_id=expected_skill_package_id,
            field_name="source_code_package_id",
        )
        assert source_code_package_fk_value in {
            expected_source_code_package_id,
            str(expected_source_code_package_id),
        }
        api_package_fk_value = package_assertions.primitive(
            instance_id=expected_skill_package_api_package_id,
            field_name="api_package_id",
        )
        assert api_package_fk_value in {
            expected_api_package_id,
            str(expected_api_package_id),
        }

        package_class_configs_by_name = _class_configs_by_name(package_assertions)
        skill_package_class_config = package_class_configs_by_name["SkillPackage"]
        skill_package_api_package_class_config = package_class_configs_by_name[
            "SkillPackageApiPackage"
        ]
        package_assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=skill_package_class_config.id,
            target_class_config_id=skill_package_api_package_class_config.id,
            relationship_name="api_packages",
        )

        payload = _payload_value(package_result.responses[-1].payload)
        assert isinstance(payload, dict)
        assert UUID(str(payload["api_package_id"])) == expected_api_package_id

        skill_package_oig_commit_id = await _object_instance_graph_commit_id_for_head(
            branch_id=package_result.branch_id,
            projection_hash=skill_package_opg.projection_hash,
        )
        package_ref_run_key = "door-control/run/package-ref-e2e-001"
        package_ref_api_call_key = uuid4()
        expected_package_ref_skill_run_id = stable_skill_run_id(
            skill_config_id=expected_skill_config_id,
            run_key=package_ref_run_key,
        )
        expected_package_ref_skill_run_step_id = stable_skill_run_step_id(
            skill_run_id=expected_package_ref_skill_run_id,
            skill_config_step_id=expected_skill_config_step_id,
        )
        package_ref_result = await materialize_skill_run_from_package_refs(
            runtime=runtime,
            index=idx,
            actor_id=lane.actor_id,
            skill_package_ref=SkillRuntimePackageRef(
                family_key="skill",
                package_kind="skill",
                package_name=skill_name,
                semantic_package_id=str(expected_skill_package_id),
                semantic_object_instance_graph_commit_id=str(
                    skill_package_oig_commit_id
                ),
                semantic_root_kind="skill_config",
                semantic_root_id=str(expected_skill_config_id),
                semantic_root_object_instance_graph_commit_id=str(
                    skill_config_object_instance_graph_commit_id
                ),
            ),
            api_package_refs=(
                ApiRuntimePackageRef(
                    family_key="api",
                    package_kind="api",
                    package_name="home-devices-api",
                    semantic_package_id=str(expected_api_package_id),
                    semantic_object_instance_graph_commit_id=str(
                        api_package_oig_commit_id
                    ),
                    semantic_projection_name="ApiPackage",
                    semantic_root_kind="api",
                    semantic_root_id=str(expected_api_id),
                ),
            ),
            api_call_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash=api_call_projection_hash,
            ),
            skill_run_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash=skill_run_opg.projection_hash,
            ),
            request=SkillRunHarnessRequest(
                skill_config_id=expected_skill_config_id,
                run_key=package_ref_run_key,
                step_inputs=(
                    SkillStepApiCallInput(
                        skill_config_step_id=expected_skill_config_step_id,
                        request_payload={},
                        call_key=package_ref_api_call_key,
                        description="Clean package-ref Skill API call proof.",
                    ),
                ),
            ),
        )
        assert package_ref_result.skill_run_id == expected_package_ref_skill_run_id
        assert package_ref_result.status == SkillRunStatus.succeeded.value
        assert package_ref_result.commit_id is not None
        assert package_ref_result.head_commit_id is not None
        assert len(package_ref_result.steps) == 1
        package_ref_step = package_ref_result.steps[0]
        assert (
            package_ref_step.skill_run_step_id == expected_package_ref_skill_run_step_id
        )
        assert package_ref_step.skill_config_step_id == expected_skill_config_step_id
        assert package_ref_step.status == SkillRunStatus.succeeded.value
        assert package_ref_step.api_call.call_key == package_ref_api_call_key
        assert (
            package_ref_step.api_call.api_capability_endpoint_id
            == expected_api_endpoint_id
        )
        assert (
            package_ref_step.api_call.request_class_config_id == request_class_config.id
        )
        assert package_ref_step.api_call.request_model_id.int != 0
        assert package_ref_step.api_call.request_hash
