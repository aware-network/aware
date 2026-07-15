from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from _skill_runtime_test_paths import REPO_ROOT, prepend_skill_dependency_paths


def _prepend_skill_runtime_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    prepend_skill_dependency_paths(monkeypatch)


def test_skill_execution_dispatcher_has_no_direct_deprecated_runtime_imports() -> None:
    source = (
        REPO_ROOT
        / "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/execution/dispatcher.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "ocg_support" not in source
    assert "FunctionCallInvoker" not in source


def test_skill_execution_api_call_sources_have_no_direct_deprecated_runtime_imports() -> (
    None
):
    for relative_path in (
        "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/execution/_meta_hydration.py",
        "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/execution/api_calls.py",
        "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/execution/resolution.py",
    ):
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")

        assert "aware_runtime" not in source
        assert "hydrate_orm_graph_from_oig" not in source
        assert "ontology.materialization._lane_hydration" not in source


def test_skill_execution_harness_has_no_direct_deprecated_runtime_imports() -> None:
    source = (
        REPO_ROOT
        / "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/execution/harness.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "bind_runtime_lane" not in source
    assert "FunctionCallInvoker" not in source


def test_skill_run_harness_rejects_unknown_step_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    execution_module = import_module("aware_skill.execution")
    harness_module = import_module("aware_skill.execution.harness")
    request_class = cast(Any, getattr(execution_module, "SkillRunHarnessRequest"))
    step_input_class = cast(Any, getattr(execution_module, "SkillStepApiCallInput"))
    step_inputs_by_id = cast(
        Callable[..., object], getattr(harness_module, "_step_inputs_by_id")
    )

    planned_step_id = uuid4()
    unknown_step_id = uuid4()
    request = request_class(
        skill_config_id=uuid4(),
        run_key="unit/run/unknown-step",
        step_inputs=(step_input_class(skill_config_step_id=unknown_step_id),),
    )

    with pytest.raises(RuntimeError, match="unknown SkillConfigStep"):
        step_inputs_by_id(
            planned_step_ids=(planned_step_id,),
            request=request,
        )


def test_skill_run_harness_rejects_duplicate_step_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    execution_module = import_module("aware_skill.execution")
    harness_module = import_module("aware_skill.execution.harness")
    request_class = cast(Any, getattr(execution_module, "SkillRunHarnessRequest"))
    step_input_class = cast(Any, getattr(execution_module, "SkillStepApiCallInput"))
    step_inputs_by_id = cast(
        Callable[..., object], getattr(harness_module, "_step_inputs_by_id")
    )

    planned_step_id = uuid4()
    request = request_class(
        skill_config_id=uuid4(),
        run_key="unit/run/duplicate-step",
        step_inputs=(
            step_input_class(skill_config_step_id=planned_step_id),
            step_input_class(skill_config_step_id=planned_step_id),
        ),
    )

    with pytest.raises(RuntimeError, match="duplicate input"):
        step_inputs_by_id(
            planned_step_ids=(planned_step_id,),
            request=request,
        )


@pytest.mark.asyncio
async def test_skill_step_api_call_uses_api_dispatcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    execution_module = import_module("aware_skill.execution")
    api_calls_module = import_module("aware_skill.execution.api_calls")

    step_id = uuid4()
    endpoint_id = uuid4()
    request_class_config_id = uuid4()
    call_key = uuid4()
    envelope = SimpleNamespace(
        api_call_id=uuid4(),
        api_capability_endpoint_id=endpoint_id,
        call_key=call_key,
        request_hash="sha256:skill-dispatcher-proof",
        request_model_id=uuid4(),
        request_class_config_id=request_class_config_id,
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
        commit_id=uuid4(),
        head_commit_id=uuid4(),
    )
    captured: dict[str, object] = {}

    async def _fake_resolve_endpoint_invocation_contract(**_: object) -> object:
        contract_class = cast(
            Any, getattr(api_calls_module, "_ResolvedEndpointInvocationContract")
        )
        return contract_class(
            api_name="home_devices",
            request_class_config_id=request_class_config_id,
            request_class_ref="aware_home_api.door.OpenDoor",
            request_source_path="api_endpoint:request",
        )

    async def _fake_dispatch_api_invocation(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(envelope=envelope)

    monkeypatch.setattr(
        api_calls_module,
        "_resolve_endpoint_invocation_contract",
        _fake_resolve_endpoint_invocation_contract,
    )
    monkeypatch.setattr(
        api_calls_module,
        "dispatch_api_invocation",
        _fake_dispatch_api_invocation,
    )

    step_class = cast(Any, getattr(execution_module, "ResolvedSkillExecutionStep"))
    step_input_class = cast(Any, getattr(execution_module, "SkillStepApiCallInput"))
    materialize_skill_step_api_call = cast(
        Any,
        getattr(api_calls_module, "materialize_skill_step_api_call"),
    )
    result = await materialize_skill_step_api_call(
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        api_source_lane=cast(Any, object()),
        api_call_lane=cast(Any, object()),
        step=step_class(
            skill_config_step_id=step_id,
            position=1,
            instruction="Open the door.",
            skill_config_api_endpoint_id=uuid4(),
            api_capability_endpoint_id=endpoint_id,
            endpoint_requirement_name="open_door",
            capability_name="open_door",
            targets=(),
        ),
        step_input=step_input_class(
            skill_config_step_id=step_id,
            request_payload={"label": "Front Door"},
            call_key=call_key,
            description="Skill call",
        ),
        commit=False,
        publish=True,
    )

    ir = cast(Any, captured["ir"])
    assert ir.endpoint_ref == "home_devices.open_door.open_door"
    assert ir.api_capability_endpoint_id == endpoint_id
    assert dict(ir.request_payload) == {"label": "Front Door"}
    assert captured["call_key"] == call_key
    assert captured["commit"] is False
    assert captured["publish"] is True
    assert cast(Any, result).api_call_id == envelope.api_call_id
    assert cast(Any, result).api_capability_endpoint_id == endpoint_id
    assert cast(Any, result).request_class_config_id == request_class_config_id


@pytest.mark.asyncio
async def test_skill_run_from_package_refs_uses_attached_api_package_source_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    execution_module = import_module("aware_skill.execution")
    harness_module = import_module("aware_skill.execution.harness")
    api_invocation_module = import_module("aware_api_runtime.invocation")
    api_package_ref_module = import_module("aware_api_runtime.package_ref_resolution")
    skill_package_ref_module = import_module("aware_skill.package_ref_resolution")
    source_commit_class = cast(
        Any, getattr(api_invocation_module, "ApiInvocationSourceCommit")
    )
    api_package_ref_class = cast(
        Any, getattr(api_package_ref_module, "ApiRuntimePackageRef")
    )
    skill_package_ref_class = cast(
        Any, getattr(skill_package_ref_module, "SkillRuntimePackageRef")
    )

    skill_config_id = uuid4()
    skill_package_id = uuid4()
    api_package_id = uuid4()
    api_id = uuid4()
    step_id = uuid4()
    call_key = uuid4()
    skill_config_domain_commit_id = uuid4()
    skill_branch_id = uuid4()
    source_commit = source_commit_class(
        branch_id=uuid4(),
        projection_hash="sha256:pinned-api",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    api_call_lane = SimpleNamespace(
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )
    skill_run_lane = SimpleNamespace(
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:skill-run",
    )
    skill_package_ref = skill_package_ref_class(
        family_key="skill",
        package_kind="skill",
        package_name="door_control",
        semantic_package_id=str(skill_package_id),
        semantic_object_instance_graph_commit_id=str(uuid4()),
    )
    api_package_ref = api_package_ref_class(
        family_key="api",
        package_kind="api",
        package_name="home-devices-api",
        semantic_package_id=str(api_package_id),
        semantic_object_instance_graph_commit_id=str(uuid4()),
    )
    request_class = cast(Any, getattr(execution_module, "SkillRunHarnessRequest"))
    step_input_class = cast(Any, getattr(execution_module, "SkillStepApiCallInput"))
    step_class = cast(Any, getattr(execution_module, "ResolvedSkillExecutionStep"))
    call_materialization_class = cast(
        Any, getattr(execution_module, "SkillStepApiCallMaterialization")
    )
    request = request_class(
        skill_config_id=skill_config_id,
        run_key="door-control/run/package-ref",
        step_inputs=(
            step_input_class(
                skill_config_step_id=step_id,
                request_payload={"door": "front"},
                call_key=call_key,
            ),
        ),
    )
    plan = SimpleNamespace(
        skill_config_id=skill_config_id,
        steps=(
            step_class(
                skill_config_step_id=step_id,
                position=1,
                instruction="Open the door.",
                skill_config_api_endpoint_id=uuid4(),
                api_capability_endpoint_id=uuid4(),
                endpoint_requirement_name="open",
                capability_name="door",
                targets=(),
                api_id=api_id,
            ),
        ),
    )
    captured: dict[str, object] = {}

    async def _fake_resolve_skill_package_ref(**kwargs: object) -> object:
        captured["skill_package_ref"] = kwargs["package_ref"]
        return SimpleNamespace(
            skill_config_id=skill_config_id,
            api_package_ids=(api_package_id,),
            semantic_branch_id=str(skill_branch_id),
            skill_config_projection_hash="sha256:skill-config",
            skill_config_domain_commit_id=skill_config_domain_commit_id,
        )

    async def _fake_resolve_api_package_ref(**kwargs: object) -> object:
        captured["api_package_ref"] = kwargs["package_ref"]
        return SimpleNamespace(api_package_id=api_package_id, api_id=api_id)

    def _fake_source_commit_from_package_ref(binding: object) -> object:
        captured["api_binding"] = binding
        return source_commit

    async def _fake_resolve_plan_from_commit(**kwargs: object) -> object:
        captured["plan_kwargs"] = kwargs
        return plan

    async def _fake_materialize_skill_step_api_call(**kwargs: object) -> object:
        captured["api_call_kwargs"] = kwargs
        return call_materialization_class(
            skill_config_step_id=step_id,
            api_call_id=uuid4(),
            api_capability_endpoint_id=plan.steps[0].api_capability_endpoint_id,
            call_key=call_key,
            request_hash="sha256:skill-package-ref",
            request_model_id=uuid4(),
            request_class_config_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="sha256:api-call",
            commit_id=uuid4(),
            head_commit_id=uuid4(),
        )

    async def _fake_materialize_skill_run_receipt(**kwargs: object) -> object:
        captured["receipt_kwargs"] = kwargs
        return SimpleNamespace(status="succeeded")

    monkeypatch.setattr(
        harness_module,
        "resolve_committed_skill_runtime_package_ref",
        _fake_resolve_skill_package_ref,
    )
    monkeypatch.setattr(
        harness_module,
        "resolve_api_runtime_package_ref",
        _fake_resolve_api_package_ref,
    )
    monkeypatch.setattr(
        harness_module,
        "build_api_invocation_source_commit_from_package_ref",
        _fake_source_commit_from_package_ref,
    )
    monkeypatch.setattr(
        harness_module,
        "resolve_skill_execution_plan_from_commit",
        _fake_resolve_plan_from_commit,
    )
    monkeypatch.setattr(
        harness_module,
        "materialize_skill_step_api_call",
        _fake_materialize_skill_step_api_call,
    )
    monkeypatch.setattr(
        harness_module,
        "_materialize_skill_run_receipt",
        _fake_materialize_skill_run_receipt,
    )

    result = await cast(
        Any, getattr(harness_module, "materialize_skill_run_from_package_refs")
    )(
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        skill_package_ref=skill_package_ref,
        api_package_refs=(api_package_ref,),
        api_call_lane=cast(Any, api_call_lane),
        skill_run_lane=cast(Any, skill_run_lane),
        request=request,
        commit=False,
        publish=True,
    )

    assert result.status == "succeeded"
    assert captured["skill_package_ref"] is skill_package_ref
    assert captured["api_package_ref"] is api_package_ref
    plan_kwargs = cast(dict[str, object], captured["plan_kwargs"])
    assert plan_kwargs["branch_id"] == skill_branch_id
    assert plan_kwargs["projection_hash"] == "sha256:skill-config"
    assert plan_kwargs["commit_id"] == skill_config_domain_commit_id
    api_call_kwargs = cast(dict[str, object], captured["api_call_kwargs"])
    assert api_call_kwargs["api_source_commit"] == source_commit
    api_source_lane = cast(Any, api_call_kwargs["api_source_lane"])
    assert api_source_lane.branch_id == source_commit.branch_id
    assert api_source_lane.projection_hash == source_commit.projection_hash
    assert api_call_kwargs["api_call_lane"] is api_call_lane
    assert api_call_kwargs["commit"] is False
    assert api_call_kwargs["publish"] is True
    receipt_kwargs = cast(dict[str, object], captured["receipt_kwargs"])
    assert receipt_kwargs["skill_run_lane"] is skill_run_lane


@pytest.mark.asyncio
async def test_skill_run_from_package_refs_rejects_legacy_skill_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    harness_module = import_module("aware_skill.execution.harness")
    execution_module = import_module("aware_skill.execution")
    skill_package_ref_module = import_module("aware_skill.package_ref_resolution")
    skill_package_ref_class = cast(
        Any, getattr(skill_package_ref_module, "SkillRuntimePackageRef")
    )
    request_class = cast(Any, getattr(execution_module, "SkillRunHarnessRequest"))

    with pytest.raises(RuntimeError, match="semantic_object_instance_graph_commit_id"):
        await cast(
            Any, getattr(harness_module, "materialize_skill_run_from_package_refs")
        )(
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            actor_id=None,
            skill_package_ref=skill_package_ref_class(
                family_key="skill",
                package_kind="skill",
                package_name="door_control",
                semantic_head_commit_id=str(uuid4()),
                semantic_branch_id=str(uuid4()),
            ),
            api_package_refs=(),
            api_call_lane=cast(Any, object()),
            skill_run_lane=cast(Any, object()),
            request=request_class(
                skill_config_id=uuid4(),
                run_key="door-control/run/legacy-ref",
            ),
        )


@pytest.mark.asyncio
async def test_invoke_skill_package_derives_lanes_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    execution_module = import_module("aware_skill.execution")
    dispatcher_module = import_module("aware_skill.execution.dispatcher")
    api_package_ref_module = import_module("aware_api_runtime.package_ref_resolution")
    skill_package_ref_module = import_module("aware_skill.package_ref_resolution")
    invoke_skill_package = cast(Any, getattr(execution_module, "invoke_skill_package"))
    context_class = cast(Any, getattr(execution_module, "SkillInvocationContext"))
    request_class = cast(Any, getattr(execution_module, "SkillRunHarnessRequest"))
    step_input_class = cast(Any, getattr(execution_module, "SkillStepApiCallInput"))
    api_package_ref_class = cast(
        Any, getattr(api_package_ref_module, "ApiRuntimePackageRef")
    )
    skill_package_ref_class = cast(
        Any, getattr(skill_package_ref_module, "SkillRuntimePackageRef")
    )

    actor_id = uuid4()
    api_call_branch_id = uuid4()
    skill_run_branch_id = uuid4()
    skill_config_id = uuid4()
    skill_step_id = uuid4()
    api_ref = api_package_ref_class(
        family_key="api",
        package_kind="api",
        package_name="home-devices-api",
        semantic_package_id=str(uuid4()),
        semantic_object_instance_graph_commit_id=str(uuid4()),
    )
    skill_ref = skill_package_ref_class(
        family_key="skill",
        package_kind="skill",
        package_name="door_control",
        semantic_package_id=str(uuid4()),
        semantic_object_instance_graph_commit_id=str(uuid4()),
        semantic_root_kind="skill_config",
        semantic_root_id=str(skill_config_id),
    )
    request = request_class(
        skill_config_id=skill_config_id,
        run_key="door-control/run/facade",
        step_inputs=(
            step_input_class(
                skill_config_step_id=skill_step_id,
                request_payload={"door": "front"},
            ),
        ),
    )
    expected_result = SimpleNamespace(status="succeeded")
    captured: dict[str, object] = {}
    projection_names: list[str] = []

    def _fake_projection_hash(*, index: object, projection_name: str) -> str:
        del index
        projection_names.append(projection_name)
        return f"sha256:{projection_name}"

    async def _fake_materialize_skill_run_from_package_refs(**kwargs: object) -> object:
        captured.update(kwargs)
        return expected_result

    monkeypatch.setattr(
        dispatcher_module,
        "find_meta_graph_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        dispatcher_module,
        "materialize_skill_run_from_package_refs",
        _fake_materialize_skill_run_from_package_refs,
    )

    result = await invoke_skill_package(
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        context=context_class(
            actor_id=actor_id,
            api_call_branch_id=api_call_branch_id,
            skill_run_branch_id=skill_run_branch_id,
        ),
        skill_package_ref=skill_ref,
        api_package_refs=(api_ref,),
        request=request,
        commit=False,
        publish=True,
    )

    assert result is expected_result
    assert captured["actor_id"] == actor_id
    assert captured["skill_package_ref"] is skill_ref
    assert captured["api_package_refs"] == (api_ref,)
    assert captured["request"] is request
    assert captured["commit"] is False
    assert captured["publish"] is True
    api_call_lane = cast(Any, captured["api_call_lane"])
    assert api_call_lane.branch_id == api_call_branch_id
    assert api_call_lane.projection_hash == "sha256:ApiCall"
    skill_run_lane = cast(Any, captured["skill_run_lane"])
    assert skill_run_lane.branch_id == skill_run_branch_id
    assert skill_run_lane.projection_hash == "sha256:SkillRun"
    assert projection_names == ["ApiCall", "SkillRun"]
    assert "api_source_lane" not in captured
    assert "skill_config_lane" not in captured


@pytest.mark.asyncio
async def test_invoke_skill_package_rejects_manifest_and_legacy_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    execution_module = import_module("aware_skill.execution")
    api_package_ref_module = import_module("aware_api_runtime.package_ref_resolution")
    skill_package_ref_module = import_module("aware_skill.package_ref_resolution")
    invoke_skill_package = cast(Any, getattr(execution_module, "invoke_skill_package"))
    context_class = cast(Any, getattr(execution_module, "SkillInvocationContext"))
    request_class = cast(Any, getattr(execution_module, "SkillRunHarnessRequest"))
    api_package_ref_class = cast(
        Any, getattr(api_package_ref_module, "ApiRuntimePackageRef")
    )
    skill_package_ref_class = cast(
        Any, getattr(skill_package_ref_module, "SkillRuntimePackageRef")
    )

    context = context_class(
        actor_id=uuid4(),
    )
    request = request_class(
        skill_config_id=uuid4(),
        run_key="door-control/run/reject-legacy",
    )
    clean_skill_ref = skill_package_ref_class(
        family_key="skill",
        package_kind="skill",
        package_name="door_control",
        semantic_object_instance_graph_commit_id=str(uuid4()),
    )
    clean_api_ref = api_package_ref_class(
        family_key="api",
        package_kind="api",
        package_name="home-devices-api",
        semantic_object_instance_graph_commit_id=str(uuid4()),
    )

    with pytest.raises(RuntimeError, match="manifest_path"):
        await invoke_skill_package(
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            context=context,
            skill_package_ref=skill_package_ref_class(
                family_key="skill",
                package_kind="skill",
                package_name="door_control",
                manifest_path="skills/door_control/aware.skill.toml",
                semantic_object_instance_graph_commit_id=str(uuid4()),
            ),
            api_package_refs=(clean_api_ref,),
            request=request,
        )

    with pytest.raises(RuntimeError, match="semantic_head_commit_id"):
        await invoke_skill_package(
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            context=context,
            skill_package_ref=skill_package_ref_class(
                family_key="skill",
                package_kind="skill",
                package_name="door_control",
                semantic_object_instance_graph_commit_id=str(uuid4()),
                semantic_head_commit_id=str(uuid4()),
            ),
            api_package_refs=(clean_api_ref,),
            request=request,
        )

    with pytest.raises(RuntimeError, match="manifest_toml_path"):
        await invoke_skill_package(
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            context=context,
            skill_package_ref=clean_skill_ref,
            api_package_refs=(
                api_package_ref_class(
                    family_key="api",
                    package_kind="api",
                    package_name="home-devices-api",
                    manifest_toml_path="apis/home/aware.api.toml",
                    semantic_object_instance_graph_commit_id=str(uuid4()),
                ),
            ),
            request=request,
        )

    with pytest.raises(RuntimeError, match="semantic_head_commit_id"):
        await invoke_skill_package(
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            context=context,
            skill_package_ref=clean_skill_ref,
            api_package_refs=(
                api_package_ref_class(
                    family_key="api",
                    package_kind="api",
                    package_name="home-devices-api",
                    semantic_object_instance_graph_commit_id=str(uuid4()),
                    semantic_head_commit_id=str(uuid4()),
                ),
            ),
            request=request,
        )
