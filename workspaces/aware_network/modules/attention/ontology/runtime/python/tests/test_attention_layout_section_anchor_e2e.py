from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_attention.handlers._generated import meta_handlers as attention_meta_handlers
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    MultiLaneProofCall,
    ProofCall,
    ROOT_OBJECT_ID,
    run_multi_lane_meta_runtime_proof,
)
from ._attention_module_proof_paths import REPO_ROOT


ATTENTION_LAYOUT_CLASS_FQN = "aware_attention.layout.Layout"
ATTENTION_SECTION_CLASS_FQN = "aware_attention.section.Section"
ATTENTION_FOCUS_SCOPE_CLASS_FQN = "aware_attention.focus.FocusScope"

_ATTENTION_META_HANDLERS_ANY: Any = attention_meta_handlers
_ATTENTION_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ATTENTION_META_HANDLERS_ANY,
)
_ATTENTION_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ATTENTION_META_HANDLERS_ANY,
)


def _attention_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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
        / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
    )


def _build_attention_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_attention_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ATTENTION_META_HANDLER_MODULE,),
        bootstrap_modules=(_ATTENTION_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


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
async def test_attention_layout_section_anchor_e2e(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    anchor_path = (
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/runtime/python/samples/e2e/attention_layout_workspace"
        / "anchors/layout_section.anchor.toml"
    )
    anchor = tomllib.loads(anchor_path.read_text(encoding="utf-8"))

    import aware_attention_ontology  # noqa: F401
    from aware_attention.stable_ids import (
        stable_layout_id,
        stable_layout_section_id,
        stable_section_focus_scope_id,
        stable_section_id,
    )

    layout_key = anchor["layout"]["key"]
    section_key = anchor["section"]["key"]
    focus_scope_title = anchor["focus_scope"]["title"]
    focus_scope_description = anchor["focus_scope"]["description"]
    focus_scope_is_active = bool(anchor["focus_scope"]["is_active"])

    layout_id = stable_layout_id(key=layout_key)
    section_id = stable_section_id(key=section_key)
    focus_scope_id = uuid4()

    layout_section_id = stable_layout_section_id(
        layout_id=layout_id, section_id=section_id
    )
    section_focus_scope_id = stable_section_focus_scope_id(
        section_id=section_id,
        focus_scope_id=focus_scope_id,
    )

    lane = LaneIds(
        branch_id=focus_scope_id,
        actor_id=uuid4(),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        results, assertions_by_opg = await run_multi_lane_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            calls=[
                MultiLaneProofCall(
                    opg_name="Layout",
                    root_class_fqn=ATTENTION_LAYOUT_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=ATTENTION_LAYOUT_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "key": layout_key,
                            "title": anchor["layout"]["title"],
                            "description": anchor["layout"]["description"],
                        },
                        expected_root_object_id=layout_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Layout",
                    root_class_fqn=ATTENTION_LAYOUT_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ATTENTION_LAYOUT_CLASS_FQN,
                        function_name="add_section",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "section_id": section_id,
                            "title": anchor["section"]["title"],
                            "description": anchor["section"]["description"],
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Section",
                    root_class_fqn=ATTENTION_SECTION_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=ATTENTION_SECTION_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "key": section_key,
                            "title": anchor["section"]["title"],
                            "description": anchor["section"]["description"],
                        },
                        expected_root_object_id=section_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="FocusScope",
                    root_class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
                    call=ProofCall(
                        target="constructor",
                        class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
                        function_name="build",
                        kwargs={
                            "title": focus_scope_title,
                            "description": focus_scope_description,
                            "expires_at": None,
                            "is_active": focus_scope_is_active,
                            "last_accessed": None,
                        },
                        expected_root_object_id=focus_scope_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Section",
                    root_class_fqn=ATTENTION_SECTION_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ATTENTION_SECTION_CLASS_FQN,
                        function_name="add_focus_scope",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "focus_scope_id": focus_scope_id,
                            "title": focus_scope_title,
                            "description": focus_scope_description,
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="Section",
                    root_class_fqn=ATTENTION_SECTION_CLASS_FQN,
                    call=ProofCall(
                        target="instance",
                        class_fqn=ATTENTION_SECTION_CLASS_FQN,
                        function_name="set_active_focus_scope",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={"focus_scope_id": focus_scope_id},
                    ),
                ),
            ],
        )

    assert set(results.keys()) == {"Layout", "Section", "FocusScope"}

    layout_assertions = assertions_by_opg["Layout"]
    section_assertions = assertions_by_opg["Section"]
    focus_scope_assertions = assertions_by_opg["FocusScope"]

    layout_assertions.expect_instance(layout_id)
    layout_assertions.expect_instance(layout_section_id)
    layout_assertions.expect_edge(
        source_id=layout_id,
        target_id=layout_section_id,
        relationship_name="sections",
    )

    section_assertions.expect_instance(section_id)
    section_assertions.expect_instance(section_focus_scope_id)
    section_assertions.expect_edge(
        source_id=section_id,
        target_id=section_focus_scope_id,
        relationship_name="focus_scopes",
    )
    _expect_uuid_primitive(
        section_assertions,
        instance_id=section_id,
        field_name="active_focus_scope_id",
        expected=section_focus_scope_id,
    )
    _expect_uuid_primitive(
        section_assertions,
        instance_id=section_focus_scope_id,
        field_name="focus_scope_id",
        expected=focus_scope_id,
    )

    focus_scope_assertions.expect_root(focus_scope_id)
