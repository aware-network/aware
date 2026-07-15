from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest

from aware_attention.handlers._generated import (
    meta_handlers as attention_meta_handlers,
)
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
    MetaOIGAssertions,
    MultiLaneProofCall,
    ProofCall,
    ROOT_OBJECT_ID,
    run_multi_lane_meta_runtime_proof,
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
_THREAD_CONFIG_CLASS_FQN = "aware_environment.thread.ThreadConfig"
_THREAD_CLASS_FQN = "aware_environment.thread.Thread"
_THREAD_LAYOUT_CLASS_FQN = "aware_environment.thread.ThreadLayout"

_LAYOUT_CLASS_FQN = "aware_attention.layout.Layout"
_SECTION_CLASS_FQN = "aware_attention.section.Section"
_FOCUS_SCOPE_CLASS_FQN = "aware_attention.focus.FocusScope"

_ATTENTION_META_HANDLERS_ANY: Any = attention_meta_handlers
_ATTENTION_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ATTENTION_META_HANDLERS_ANY,
)
_ATTENTION_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ATTENTION_META_HANDLERS_ANY,
)

_ENVIRONMENT_META_HANDLERS_ANY: Any = environment_meta_handlers
_ENVIRONMENT_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ENVIRONMENT_META_HANDLERS_ANY,
)
_ENVIRONMENT_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ENVIRONMENT_META_HANDLERS_ANY,
)


def _thread_attention_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return environment_package_manifest_paths(
        repo_root,
        package_names=("environment-ontology", "attention-ontology"),
    )


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


def _build_thread_attention_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    package_manifest_paths = _thread_attention_package_manifest_paths(repo_root)
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            _ENVIRONMENT_META_HANDLER_MODULE,
            _ATTENTION_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _ENVIRONMENT_META_BOOTSTRAP_MODULE,
            _ATTENTION_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=_package_entries_by_manifest_path(
            repo_root=repo_root,
            manifest_paths=package_manifest_paths,
        ),
        package_graph_cache_request_signature=(
            "pytest:environment-thread-attention-meta-harness"
        ),
        source_analysis_allowed_manifest_paths=package_manifest_paths,
    )
    assert runtime.context is not None
    return runtime


def _single_projection_hash_by_name(runtime: MetaGraphRuntime, name: str) -> str:
    assert runtime.context is not None
    idx = runtime.context.index
    matches = [
        opg.projection_hash for opg in idx.opg_by_hash.values() if opg.name == name
    ]
    assert matches, f"Projection not found: {name}"
    assert len(matches) == 1, f"Projection name is not unique: {name}"
    return matches[0]


def _source_class_name(runtime: MetaGraphRuntime, portal: object) -> str | None:
    assert runtime.context is not None
    class_config = runtime.context.index.class_configs_by_id.get(
        getattr(portal, "source_class_config_id")
    )
    return class_config.name if class_config is not None else None


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


@pytest.mark.asyncio
async def test_thread_attention_module_proof_portal_resolution(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_environment_ontology  # noqa: F401
    from aware_attention_ontology.stable_ids import (
        stable_layout_id,
        stable_layout_section_id,
        stable_section_focus_scope_id,
        stable_section_id,
    )
    from aware_environment_ontology.stable_ids import (
        stable_environment_config_id,
        stable_environment_id,
        stable_environment_profile_id,
        stable_environment_profile_config_id,
        stable_process_config_id,
        stable_process_id,
        stable_thread_config_id,
        stable_thread_id,
        stable_thread_layout_id,
    )

    environment_key = "thread-attention-portal-env"
    environment_id = stable_environment_id(key=environment_key)
    environment_config_id = stable_environment_config_id(handle=environment_key)
    environment_profile_config_id = stable_environment_profile_config_id(
        environment_config_id=environment_config_id,
        key="os.default",
    )
    environment_profile_id = stable_environment_profile_id(
        environment_id=environment_id,
        profile_config_id=environment_profile_config_id,
    )
    boot_process_config_id = stable_process_config_id(
        environment_profile_config_id=environment_profile_config_id,
        key="environment",
    )
    boot_process_id = stable_process_id(
        environment_profile_id=environment_profile_id,
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
        environment_id=environment_id,
        thread_id=boot_thread_id,
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

    layout_key = "workspace-default"
    section_key = "workspace"
    layout_id = stable_layout_id(key=layout_key)
    section_id = stable_section_id(key=section_key)
    focus_scope_id = boot_branch_id

    thread_layout_id = stable_thread_layout_id(
        thread_id=worker_thread_id,
        layout_id=layout_id,
    )
    layout_section_id = stable_layout_section_id(
        layout_id=layout_id,
        section_id=section_id,
    )
    section_focus_scope_id = stable_section_focus_scope_id(
        section_id=section_id,
        focus_scope_id=focus_scope_id,
    )

    lane = LaneIds(branch_id=boot_branch_id)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_thread_attention_meta_runtime(
            repo_root,
            aware_root=aware_root,
        )
        results, assertions_by_opg = await run_multi_lane_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            calls=[
                MultiLaneProofCall(
                    opg_name="Environment",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_ENVIRONMENT_CLASS_FQN,
                        function_name="build",
                        args=[
                            environment_key,
                            "Thread-Attention Portal Environment",
                            None,
                        ],
                        expected_root_object_id=environment_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Environment",
                    root_class_fqn=_ENVIRONMENT_CLASS_FQN,
                    call=ProofCall(
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
                ),
                MultiLaneProofCall(
                    opg_name="EnvironmentProfileConfig",
                    root_class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                        function_name="build_via_environment_config",
                        kwargs={
                            "environment_config_id": environment_config_id,
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
                    root_class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
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
                    root_class_fqn=_ENVIRONMENT_PROFILE_CONFIG_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_PROCESS_CONFIG_CLASS_FQN,
                        function_name="create_thread_config",
                        object_id=worker_process_config_id,
                        kwargs={
                            "key": "worker-main",
                            "title": "Main",
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
                    opg_name="EnvironmentProfile",
                    root_class_fqn=_ENVIRONMENT_PROFILE_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_ENVIRONMENT_PROFILE_CLASS_FQN,
                        function_name="build_via_environment",
                        kwargs={
                            "environment_id": environment_id,
                            "profile_config_id": environment_profile_config_id,
                            "title": "Default OS",
                            "description": None,
                            "status": "active",
                            "metadata_json": {},
                        },
                        expected_root_object_id=environment_profile_id,
                        allow_noop_commit=True,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="EnvironmentProfile",
                    root_class_fqn=_ENVIRONMENT_PROFILE_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_ENVIRONMENT_PROFILE_CLASS_FQN,
                        function_name="create_process",
                        object_id=environment_profile_id,
                        args=[
                            worker_process_config_id,
                            "worker",
                            "Worker",
                            None,
                        ],
                        allow_noop_commit=True,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Process",
                    root_class_fqn=_PROCESS_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_PROCESS_CLASS_FQN,
                        function_name="build_via_environment_profile",
                        kwargs={
                            "environment_profile_id": environment_profile_id,
                            "process_config_id": worker_process_config_id,
                            "key": "worker",
                            "title": "Worker",
                            "description": None,
                        },
                        expected_root_object_id=worker_process_id,
                        allow_noop_commit=True,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Process",
                    root_class_fqn=_PROCESS_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_PROCESS_CLASS_FQN,
                        function_name="create_thread",
                        object_id=worker_process_id,
                        args=[
                            worker_thread_config_id,
                            "worker-main",
                            "Worker Main",
                            None,
                            True,
                        ],
                        allow_noop_commit=True,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Thread",
                    root_class_fqn=_THREAD_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_THREAD_CLASS_FQN,
                        function_name="build_via_process",
                        kwargs={
                            "process_id": worker_process_id,
                            "thread_config_id": worker_thread_config_id,
                            "key": "worker-main",
                            "title": "Worker Main",
                            "description": None,
                            "is_main": True,
                        },
                        expected_root_object_id=worker_thread_id,
                        allow_noop_commit=True,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Thread",
                    root_class_fqn=_THREAD_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=_THREAD_CLASS_FQN,
                        function_name="add_layout",
                        object_id=worker_thread_id,
                        kwargs={
                            "layout_id": layout_id,
                            "key": layout_key,
                        },
                        allow_noop_commit=True,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ThreadLayout",
                    root_class_fqn=_THREAD_LAYOUT_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_THREAD_LAYOUT_CLASS_FQN,
                        function_name="create_via_thread",
                        kwargs={
                            "thread_id": worker_thread_id,
                            "layout_id": layout_id,
                            "key": layout_key,
                        },
                        expected_root_object_id=thread_layout_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Layout",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_LAYOUT_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "key": layout_key,
                            "title": "Workspace Default",
                            "description": None,
                        },
                        expected_root_object_id=layout_id,
                    ),
                    root_class_fqn=_LAYOUT_CLASS_FQN,
                ),
                MultiLaneProofCall(
                    opg_name="Layout",
                    call=ProofCall(
                        target="instance",
                        class_fqn=_LAYOUT_CLASS_FQN,
                        function_name="add_section",
                        object_id=layout_id,
                        kwargs={
                            "section_id": section_id,
                            "title": "Workspace",
                            "description": None,
                        },
                    ),
                    root_class_fqn=_LAYOUT_CLASS_FQN,
                ),
                MultiLaneProofCall(
                    opg_name="FocusScope",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_FOCUS_SCOPE_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "title": "Portal Scope",
                            "description": "OS-attention boundary focus scope",
                            "expires_at": None,
                            "is_active": True,
                            "last_accessed": None,
                        },
                        expected_root_object_id=focus_scope_id,
                    ),
                    root_class_fqn=_FOCUS_SCOPE_CLASS_FQN,
                ),
                MultiLaneProofCall(
                    opg_name="Section",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=_SECTION_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "key": section_key,
                            "title": "Workspace",
                            "description": None,
                        },
                        expected_root_object_id=section_id,
                    ),
                    root_class_fqn=_SECTION_CLASS_FQN,
                ),
                MultiLaneProofCall(
                    opg_name="Section",
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SECTION_CLASS_FQN,
                        function_name="add_focus_scope",
                        object_id=section_id,
                        kwargs={
                            "focus_scope_id": focus_scope_id,
                            "title": "Main Scope",
                            "description": None,
                        },
                    ),
                    root_class_fqn=_SECTION_CLASS_FQN,
                ),
                MultiLaneProofCall(
                    opg_name="Section",
                    call=ProofCall(
                        target="instance",
                        class_fqn=_SECTION_CLASS_FQN,
                        function_name="set_active_focus_scope",
                        object_id=section_id,
                        kwargs={"focus_scope_id": focus_scope_id},
                    ),
                    root_class_fqn=_SECTION_CLASS_FQN,
                ),
            ],
        )

    assert set(results) == {
        "Environment",
        "EnvironmentProfileConfig",
        "EnvironmentProfile",
        "Process",
        "Thread",
        "ThreadLayout",
        "Layout",
        "Section",
        "FocusScope",
    }
    assert len({result.branch_id for result in results.values()}) == 1

    environment_assertions = assertions_by_opg["Environment"]
    environment_profile_config_assertions = assertions_by_opg[
        "EnvironmentProfileConfig"
    ]
    environment_profile_assertions = assertions_by_opg["EnvironmentProfile"]
    process_assertions = assertions_by_opg["Process"]
    thread_assertions = assertions_by_opg["Thread"]
    thread_layout_assertions = assertions_by_opg["ThreadLayout"]
    layout_assertions = assertions_by_opg["Layout"]
    section_assertions = assertions_by_opg["Section"]
    focus_scope_assertions = assertions_by_opg["FocusScope"]

    environment_assertions.expect_root(environment_id)
    environment_assertions.expect_instance(environment_id)

    environment_profile_config_assertions.expect_root(environment_profile_config_id)
    environment_profile_config_assertions.expect_instance(worker_process_config_id)
    environment_profile_config_assertions.expect_instance(worker_thread_config_id)
    environment_profile_config_assertions.expect_edge(
        source_id=environment_profile_config_id,
        target_id=worker_process_config_id,
        relationship_name="process_configs",
    )
    environment_profile_config_assertions.expect_edge(
        source_id=worker_process_config_id,
        target_id=worker_thread_config_id,
        relationship_name="thread_configs",
    )

    environment_profile_assertions.expect_root(environment_profile_id)

    process_assertions.expect_root(worker_process_id)

    thread_assertions.expect_root(worker_thread_id)

    thread_layout_assertions.expect_root(thread_layout_id)
    _expect_uuid_primitive(
        thread_layout_assertions,
        instance_id=thread_layout_id,
        field_name="thread_id",
        expected=worker_thread_id,
    )
    _expect_uuid_primitive(
        thread_layout_assertions,
        instance_id=thread_layout_id,
        field_name="layout_id",
        expected=layout_id,
    )

    # Thread projection portal chain contract:
    # Thread::thread_layouts -> ThreadLayout::layout ->
    # LayoutSection::section -> SectionFocusScope::focus_scope
    assert runtime.context is not None
    idx = runtime.context.index
    thread_projection_hash = _single_projection_hash_by_name(
        runtime,
        "Thread",
    )
    thread_layout_projection_hash = _single_projection_hash_by_name(
        runtime,
        "ThreadLayout",
    )
    layout_projection_hash = _single_projection_hash_by_name(runtime, "Layout")
    section_projection_hash = _single_projection_hash_by_name(runtime, "Section")
    focus_scope_projection_hash = _single_projection_hash_by_name(
        runtime,
        "FocusScope",
    )

    thread_portals = (
        idx.portal_index.portals_by_source_projection_hash.get(
            thread_projection_hash,
        )
        or []
    )
    assert any(
        p.reference_field_name == "thread_layouts"
        and p.target_projection_hash == thread_layout_projection_hash
        and _source_class_name(runtime, p) == "Thread"
        for p in thread_portals
    )
    thread_layout_portals = (
        idx.portal_index.portals_by_source_projection_hash.get(
            thread_layout_projection_hash,
        )
        or []
    )
    assert any(
        p.reference_field_name == "layout"
        and p.target_projection_hash == layout_projection_hash
        and _source_class_name(runtime, p) == "ThreadLayout"
        for p in thread_layout_portals
    )
    layout_portals = (
        idx.portal_index.portals_by_source_projection_hash.get(layout_projection_hash)
        or []
    )
    assert any(
        p.reference_field_name == "section"
        and p.target_projection_hash == section_projection_hash
        and _source_class_name(runtime, p) == "LayoutSection"
        for p in layout_portals
    )
    section_portals = (
        idx.portal_index.portals_by_source_projection_hash.get(section_projection_hash)
        or []
    )
    assert any(
        p.reference_field_name == "focus_scope"
        and p.target_projection_hash == focus_scope_projection_hash
        and _source_class_name(runtime, p) == "SectionFocusScope"
        for p in section_portals
    )

    layout_assertions.expect_root(layout_id)
    layout_assertions.expect_instance(layout_section_id)
    layout_assertions.expect_edge(
        source_id=layout_id,
        target_id=layout_section_id,
        relationship_name="sections",
    )
    _expect_uuid_primitive(
        layout_assertions,
        instance_id=layout_section_id,
        field_name="section_id",
        expected=section_id,
    )

    section_assertions.expect_root(section_id)
    section_assertions.expect_instance(section_focus_scope_id)
    section_assertions.expect_edge(
        source_id=section_id,
        target_id=section_focus_scope_id,
        relationship_name="focus_scopes",
    )
    _expect_uuid_primitive(
        section_assertions,
        instance_id=section_focus_scope_id,
        field_name="focus_scope_id",
        expected=focus_scope_id,
    )
    _expect_uuid_primitive(
        section_assertions,
        instance_id=section_id,
        field_name="active_focus_scope_id",
        expected=section_focus_scope_id,
    )

    focus_scope_assertions.expect_root(focus_scope_id)
    focus_scope_assertions.expect_instance(focus_scope_id)
    focus_scope_assertions.expect_primitive(
        instance_id=focus_scope_id,
        field_name="title",
        expected="Portal Scope",
    )
