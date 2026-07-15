from __future__ import annotations

from pathlib import Path
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
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from ._attention_module_proof_paths import REPO_ROOT


ATTENTION_LAYOUT_CLASS_FQN = "aware_attention.layout.Layout"

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
async def test_layout_build_add_section_chain(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    from aware_attention.stable_ids import (
        stable_layout_id,
        stable_layout_section_id,
        stable_section_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        layout_key = "workspace-default"
        section_key = "workspace"
        layout_id = stable_layout_id(key=layout_key)
        section_id = stable_section_id(key=section_key)
        layout_section_id = stable_layout_section_id(
            layout_id=layout_id,
            section_id=section_id,
        )

        lane = LaneIds(
            branch_id=layout_id,
            actor_id=uuid4(),
        )

        _result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Layout",
            root_class_fqn=ATTENTION_LAYOUT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_LAYOUT_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "key": layout_key,
                        "title": "Workspace Default",
                        "description": None,
                    },
                    expected_root_object_id=layout_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_LAYOUT_CLASS_FQN,
                    function_name="add_section",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "section_id": section_id,
                        "title": "Workspace",
                        "description": None,
                    },
                ),
            ],
        )

        assertions.expect_instance(layout_id)
        assertions.expect_instance(layout_section_id)
        assertions.expect_edge(
            source_id=layout_id,
            target_id=layout_section_id,
            relationship_name="sections",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=layout_section_id,
            field_name="section_id",
            expected=section_id,
        )
