from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_content.handlers._generated import meta_handlers as content_meta_handlers
from ._memory_module_proof_paths import (
    MEMORY_PACKAGE_MANIFEST_PATHS,
    REPO_ROOT,
    extend_sys_path_for_memory_tests,
)


extend_sys_path_for_memory_tests()

from aware_memory.handlers._generated import meta_handlers as memory_meta_handlers
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from aware_memory_ontology.stable_ids import (
    stable_memory_working_id,
    stable_memory_working_item_id,
)


MEMORY_WORKING_CLASS_FQN = "aware_memory.memory.MemoryWorking"
ATTENTION_FOCUS_TRANSITION_CLASS_FQN = "aware_attention.session.AttentionFocusTransition"

_CONTENT_META_HANDLERS_ANY: Any = content_meta_handlers
_CONTENT_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _CONTENT_META_HANDLERS_ANY,
)
_CONTENT_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _CONTENT_META_HANDLERS_ANY,
)
_MEMORY_META_HANDLERS_ANY: Any = memory_meta_handlers
_MEMORY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _MEMORY_META_HANDLERS_ANY,
)
_MEMORY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _MEMORY_META_HANDLERS_ANY,
)


def _build_memory_meta_runtime(*, aware_root) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=MEMORY_PACKAGE_MANIFEST_PATHS,
        workspace_root=REPO_ROOT,
        aware_root=aware_root,
        handler_modules=(
            _CONTENT_META_HANDLER_MODULE,
            _MEMORY_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _CONTENT_META_BOOTSTRAP_MODULE,
            _MEMORY_META_BOOTSTRAP_MODULE,
        ),
    )
    assert runtime.context is not None
    return runtime


def _opg_root_class_fqn(runtime: MetaGraphRuntime, opg_id: UUID) -> str:
    assert runtime.context is not None
    index = runtime.context.index
    opg = index.opg_by_id[opg_id]
    roots = [node for node in opg.object_projection_graph_nodes if node.is_root]
    assert len(roots) == 1
    class_config = index.class_configs_by_id[roots[0].class_config_id]
    return class_config.class_fqn


def _opg_by_name_and_root(
    runtime: MetaGraphRuntime,
    *,
    name: str,
    root_class_fqn: str,
):
    assert runtime.context is not None
    matches = [
        opg
        for opg in runtime.context.index.opg_by_hash.values()
        if opg.name == name and _opg_root_class_fqn(runtime, opg.id) == root_class_fqn
    ]
    assert len(matches) == 1
    return matches[0]


def _relationship_targets_by_key(runtime: MetaGraphRuntime, opg: Any) -> dict[str, list[str]]:
    assert runtime.context is not None
    index = runtime.context.index
    targets_by_key: dict[str, list[str]] = {}
    for relationship in opg.object_projection_graph_relationships:
        relationship_config = index.relationships_by_id[
            relationship.class_config_relationship_id
        ]
        targets_by_key.setdefault(relationship_config.relationship_key, []).append(
            _opg_root_class_fqn(runtime, relationship.target_object_projection_graph_id)
        )
    return targets_by_key


def _expect_uuid_primitive(
    assertions: Any,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


def test_memory_working_projection_portals_to_attention_transition(
    tmp_path,
) -> None:
    import aware_attention_ontology  # noqa: F401
    import aware_identity_ontology  # noqa: F401
    import aware_memory_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_memory_meta_runtime(aware_root=aware_root)
        memory_working_opg = _opg_by_name_and_root(
            runtime,
            name="MemoryWorking",
            root_class_fqn=MEMORY_WORKING_CLASS_FQN,
        )
        attention_transition_opg = _opg_by_name_and_root(
            runtime,
            name="AttentionFocusTransition",
            root_class_fqn=ATTENTION_FOCUS_TRANSITION_CLASS_FQN,
        )

        targets = _relationship_targets_by_key(runtime, memory_working_opg)

        assert targets["attention_transition"] == [ATTENTION_FOCUS_TRANSITION_CLASS_FQN]
        assert "attention_frame" not in targets
        assert "visible_window_section_ids" not in targets
        assert "visibility_hash" not in targets
        assert attention_transition_opg.object_projection_graph_relationships


@pytest.mark.asyncio
async def test_memory_working_add_attention_item_commits_transition_pointer(
    tmp_path,
) -> None:
    import aware_attention_ontology  # noqa: F401
    import aware_content_ontology  # noqa: F401
    import aware_identity_ontology  # noqa: F401
    import aware_memory_ontology  # noqa: F401

    actor_id = uuid4()
    memory_working_id = stable_memory_working_id(actor_id=actor_id, key="default")
    attention_focus_transition_id = uuid4()
    expected_item_id = stable_memory_working_item_id(
        memory_working_id=memory_working_id,
        kind="attention",
        position=0,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_memory_meta_runtime(aware_root=aware_root)
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(branch_id=memory_working_id, actor_id=actor_id),
            opg_name="MemoryWorking",
            root_class_fqn=MEMORY_WORKING_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=MEMORY_WORKING_CLASS_FQN,
                    function_name="build",
                    kwargs={"actor_id": actor_id, "key": "default"},
                    expected_root_object_id=memory_working_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=MEMORY_WORKING_CLASS_FQN,
                    function_name="add_attention_item",
                    object_id=ROOT_OBJECT_ID,
                    args=[attention_focus_transition_id],
                    kwargs={
                        "rationale": "retain attention transition",
                        "summary": "workspace focus moved",
                    },
                ),
            ],
        )

        assert result.root_object_id == memory_working_id
        assertions.expect_instance(memory_working_id)
        assertions.expect_instance(expected_item_id)
        assertions.expect_edge(
            source_id=memory_working_id,
            target_id=expected_item_id,
            relationship_name="items",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=expected_item_id,
            field_name="attention_transition_id",
            expected=attention_focus_transition_id,
        )
        assertions.expect_primitive(
            instance_id=expected_item_id,
            field_name="rationale",
            expected="retain attention transition",
        )
        assertions.expect_primitive(
            instance_id=expected_item_id,
            field_name="summary",
            expected="workspace focus moved",
        )
