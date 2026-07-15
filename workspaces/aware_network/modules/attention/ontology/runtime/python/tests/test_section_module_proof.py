from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_attention.handlers._generated import meta_handlers as attention_meta_handlers
from aware_history_ontology.change.change_enums import ChangeType
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


ATTENTION_SECTION_CLASS_FQN = "aware_attention.section.Section"

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


def _class_instance_id_for_source(
    *,
    assertions: MetaOIGAssertions,
    source_object_id: UUID,
) -> UUID:
    for class_instance in assertions.oig.class_instances:
        if class_instance.source_object_id == source_object_id:
            assert class_instance.id is not None
            return class_instance.id
    raise AssertionError(
        f"Missing ClassInstance for source_object_id={source_object_id}"
    )


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
async def test_section_focus_scope_chain_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    from aware_attention.stable_ids import (
        stable_section_focus_scope_id,
        stable_section_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        ns = uuid5(NAMESPACE_URL, "aware://tests/attention/section-focus-scope")
        section_key = "workspace"
        section_id = stable_section_id(section_key=section_key)
        focus_scope_id = uuid5(ns, "focus_scope")
        section_focus_scope_id = stable_section_focus_scope_id(
            section_id=section_id,
            focus_scope_id=focus_scope_id,
        )

        lane = LaneIds(
            branch_id=section_id,
            actor_id=uuid4(),
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Section",
            root_class_fqn=ATTENTION_SECTION_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_SECTION_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "key": section_key,
                        "title": "Workspace",
                        "description": None,
                    },
                    expected_root_object_id=section_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_SECTION_CLASS_FQN,
                    function_name="add_focus_scope",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "focus_scope_id": focus_scope_id,
                        "title": "Main scope",
                        "description": None,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_SECTION_CLASS_FQN,
                    function_name="set_active_focus_scope",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={"focus_scope_id": focus_scope_id},
                ),
            ],
        )

        assertions.expect_instance(section_id)
        assertions.expect_instance(section_focus_scope_id)
        assertions.expect_edge(
            source_id=section_id,
            target_id=section_focus_scope_id,
            relationship_name="focus_scopes",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=section_focus_scope_id,
            field_name="focus_scope_id",
            expected=focus_scope_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=section_id,
            field_name="active_focus_scope_id",
            expected=section_focus_scope_id,
        )

        instance_ids = {
            ci.id for ci in assertions.oig.class_instances if ci.id is not None
        }
        assert focus_scope_id not in instance_ids

        section_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=section_id,
        )
        section_focus_scope_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=section_focus_scope_id,
        )

        # Mutation boundary: Section may update itself and the constructed
        # SectionFocusScope binding, but never the raw FocusScope target.
        updated_ids: set[UUID] = set()
        for commit in result.commits:
            for root in commit.object_instance_graph_changes:
                for ci_change in root.class_instance_changes:
                    if ci_change.change.type in {ChangeType.update, ChangeType.delete}:
                        updated_ids.add(ci_change.class_instance_id)
        assert updated_ids <= {section_ci_id, section_focus_scope_ci_id}
