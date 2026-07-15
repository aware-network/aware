from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest

from _skill_runtime_test_paths import (
    REPO_ROOT,
    install_skill_dependency_paths,
    prepend_skill_dependency_paths,
)

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
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_skill.handlers._generated import meta_handlers as skill_meta_handlers

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


def _skill_manifest_compile_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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


def _build_skill_manifest_compile_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_skill_manifest_compile_package_manifest_paths(
            repo_root
        ),
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


def _select_runtime_inline_request_class_config(
    index: MetaGraphRuntimeIndex,
) -> ClassConfig:
    for class_config in sorted(
        index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    ):
        if class_config.value_mode == ClassValueMode.inline_value:
            return class_config
    raise AssertionError("Expected one inline_value ClassConfig for API proof seeding")


def _write_skill_package(root: Path) -> Path:
    package_root = root / "skills" / "door_control"
    sources_root = package_root / "skills"
    sources_root.mkdir(parents=True, exist_ok=True)
    _ = (package_root / "aware.skill.toml").write_text(
        """
aware_skill = 1

[skill]
package_name = "door-control-skill"
fqn_prefix = "door_control_skill"

[build]
sources_dir = "skills"
compilation_mode = "skill_ontology"

[[dependencies]]
package_name = "home-devices-api"
kind = "api_package"
""",
        encoding="utf-8",
    )
    _ = (sources_root / "door_control.aware").write_text(
        '''\
skill door_control {
    "Reusable door control skill."

    api home_devices;

    endpoint open_door home_devices.door.open {
        "Open one door."
    }

    step 1 open_door {
        """
        Read the requested door state before acting.
        """
    }
}
''',
        encoding="utf-8",
    )
    return package_root / "aware.skill.toml"


def _prepend_skill_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    prepend_skill_dependency_paths(monkeypatch)


def test_skill_materialization_sources_have_no_direct_deprecated_runtime_imports() -> (
    None
):
    for relative_path in (
        "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/ontology/materialization/skill_config.py",
        "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/ontology/materialization/_lane_hydration.py",
        "workspaces/aware_network/modules/skill/ontology/runtime/python/aware_skill/materialization/service.py",
    ):
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")

        assert "aware_runtime" not in source
        assert "bind_runtime_lane" not in source
        assert "AwareRuntimeIndex" not in source
        assert "BoundRuntimeLane" not in source
        assert "FunctionCallInvoker" not in source
        assert "hydrate_orm_graph_from_oig" not in source
        assert "RuntimeHarness" not in source
        assert "ocg_support" not in source


def test_skill_config_ontology_materialization_binds_api_runtime_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime(monkeypatch)
    materialization_module = import_module(
        "aware_skill.ontology.materialization.skill_config"
    )
    bind_skill_config_lane = cast(
        Callable[..., object],
        getattr(materialization_module, "_bind_skill_config_lane"),
    )
    bound_lane = object()
    captured: dict[str, object] = {}

    class _Runtime:
        def bind(self, **kwargs: object) -> object:
            captured.update(kwargs)
            return bound_lane

    actor_id = uuid4()
    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="skill_config_projection_hash",
    )

    assert (
        bind_skill_config_lane(
            runtime=_Runtime(),
            actor_id=actor_id,
            target_lane=lane,
        )
        is bound_lane
    )
    assert captured == {
        "projection": lane.projection_hash,
        "branch_id": lane.branch_id,
        "actor_id": actor_id,
    }


def test_skill_manifest_compiles_to_skill_compile_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime(monkeypatch)
    from aware_skill.compile import compile_skill_workspace

    skill_toml_path = _write_skill_package(tmp_path)

    result = compile_skill_workspace(
        toml_path=skill_toml_path,
        repo_root=tmp_path,
        emit_compile_plan=True,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "door-control-skill"
    assert result.compile_plan.source_files == ("skills/door_control.aware",)
    assert result.compile_plan_artifact is not None
    assert (
        result.compile_plan_artifact.relpath
        == ".aware/skill/runtime/door-control-skill/skill.compile_plan.json"
    )

    skill_config = result.compile_plan.skill_configs[0]
    assert skill_config.name == "door_control"
    assert skill_config.apis[0].api_ref == "home_devices"
    assert skill_config.api_endpoints[0].name == "open_door"
    assert skill_config.api_endpoints[0].endpoint_ref == "home_devices.door.open"
    assert skill_config.api_endpoints[0].capability_name == "door"
    assert skill_config.steps[0].endpoint_name == "open_door"
    assert (
        skill_config.steps[0].instruction
        == "Read the requested door state before acting."
    )


def test_skill_materialization_spec_round_trips_compile_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime(monkeypatch)
    from aware_skill.builder import encode_skill_compile_plan
    from aware_skill.compile import compile_skill_workspace
    from aware_skill.materialization.service import (
        build_skill_definition_materialization_plan,
        decode_skill_definition_materialization_step_payload,
        resolve_skill_definition_materialization_specs,
    )

    skill_toml_path = _write_skill_package(tmp_path)
    result = compile_skill_workspace(toml_path=skill_toml_path, repo_root=tmp_path)
    assert result.compile_plan is not None

    payload = encode_skill_compile_plan(plan=result.compile_plan)
    specs = resolve_skill_definition_materialization_specs(
        compile_plan_payloads=(payload,)
    )
    assert len(specs) == 1

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="skill_config_projection_hash",
    )
    plan = build_skill_definition_materialization_plan(lane=lane, specs=specs)
    assert plan.module_id == "skill"
    assert plan.pipeline_id == "skill.compile_plan.ontology"
    decoded = decode_skill_definition_materialization_step_payload(
        plan.steps[0].payload
    )
    assert decoded == specs[0]


@pytest.mark.asyncio
async def test_skill_compile_plan_materializes_skill_config_ontology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime(monkeypatch)
    repo_root = REPO_ROOT

    from aware_api_ontology.stable_ids import stable_api_id, stable_api_package_id
    from aware_code.stable_ids import stable_code_package_id
    from aware_skill.builder import encode_skill_compile_plan
    from aware_skill.compile import compile_skill_workspace
    from aware_skill.materialization.service import (
        materialize_skill_definition_ontology,
        materialize_skill_package_from_manifest,
    )
    from aware_skill_ontology.stable_ids import (
        stable_skill_config_id,
        stable_skill_package_id,
    )

    skill_toml_path = _write_skill_package(tmp_path)
    compile_result = compile_skill_workspace(
        toml_path=skill_toml_path, repo_root=tmp_path
    )
    assert compile_result.compile_plan is not None
    compile_plan_payload = encode_skill_compile_plan(plan=compile_result.compile_plan)

    api_name = "home_devices"
    expected_api_id = stable_api_id(name=api_name)
    expected_api_package_id = stable_api_package_id(name="home-devices-api")
    expected_skill_config_id = stable_skill_config_id(name="door_control")
    expected_skill_package_id = stable_skill_package_id(name="door_control")
    expected_source_code_package_id = stable_code_package_id(
        package_name="door-control-skill",
        language="aware",
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_skill_manifest_compile_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        idx = _runtime_index(runtime)
        opg_names = {(opg.name or "").strip() for opg in idx.opg_by_hash.values()}
        assert {"Api", "SkillConfig"} <= opg_names
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="Api",
        )
        skill_config_projection_hash = find_meta_graph_projection_hash_by_name(
            index=idx,
            projection_name="SkillConfig",
        )
        request_class_config = _select_runtime_inline_request_class_config(idx)
        request_class_config_id = request_class_config.id
        assert request_class_config_id is not None

        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()
        lane = LaneIds(actor_id=uuid4())
        api_branch_id = uuid4()
        endpoint_ref = f"{api_name}.door.open"
        api_snapshot = await commit_api_reference_snapshot(
            index=idx,
            actor_id=lane.actor_id,
            branch_id=api_branch_id,
            projection_hash=api_projection_hash,
            api_name=api_name,
            endpoint_refs=(endpoint_ref,),
            endpoint_request_class_config_ids={
                endpoint_ref: request_class_config_id,
            },
        )
        assert api_snapshot.api.id == expected_api_id

        receipt = await materialize_skill_definition_ontology(
            runtime=runtime,
            index=idx,
            actor_id=lane.actor_id,
            lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash=skill_config_projection_hash,
            ),
            compile_plan_payloads=(compile_plan_payload,),
            api_reference_branch_ids_by_api_name={api_name: api_branch_id},
        )

        assert receipt is not None
        assert receipt.status == "succeeded"
        assert len(receipt.steps) == 1
        assert receipt.steps[0].commit_id is not None
        assert receipt.steps[0].details["skill_config_id"] == str(
            expected_skill_config_id
        )
        assert receipt.steps[0].details["skill_config_api_count"] == 1
        assert receipt.steps[0].details["skill_config_api_endpoint_count"] == 1
        assert receipt.steps[0].details["skill_config_step_count"] == 1

        package_result = await materialize_skill_package_from_manifest(
            runtime=runtime,
            index=idx,
            actor_id=lane.actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            skill_toml_path=skill_toml_path,
            api_reference_branch_ids_by_api_name={api_name: api_branch_id},
        )

        assert package_result.skill_config_id == expected_skill_config_id
        assert package_result.skill_package.id == expected_skill_package_id
        assert package_result.skill_package.name == "door_control"
        assert package_result.skill_package.skill_config_id == expected_skill_config_id
        assert package_result.skill_config_object_instance_graph_commit_id is not None
        assert (
            package_result.skill_package.skill_config_object_instance_graph_commit_id
            == package_result.skill_config_object_instance_graph_commit_id
        )
        assert tuple(
            edge.api_package_id for edge in package_result.skill_package_api_packages
        ) == (expected_api_package_id,)
        assert tuple(
            edge.api_package_id for edge in package_result.skill_package.api_packages
        ) == (expected_api_package_id,)
        assert package_result.source_code_package_id == expected_source_code_package_id
        assert package_result.definition_receipt is not None
        assert package_result.definition_receipt.status == "succeeded"
        assert package_result.package_commit_id is not None
