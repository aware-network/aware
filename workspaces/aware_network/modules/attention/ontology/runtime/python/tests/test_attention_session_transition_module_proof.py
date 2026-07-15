from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_attention.handlers._generated import meta_handlers as attention_meta_handlers
from aware_attention_ontology.stable_ids import (
    stable_attention_focus_transition_id,
    stable_attention_layout_topology_transition_id,
    stable_attention_layout_topology_transition_section_id,
    stable_attention_layout_transition_id,
    stable_attention_layout_transition_section_id,
    stable_attention_session_id,
    stable_attention_session_layout_id,
    stable_attention_session_section_id,
)
from aware_code.types import JsonObject
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
    SourceObjectId,
    run_meta_runtime_proof,
)

from ._attention_module_proof_paths import REPO_ROOT


ATTENTION_SESSION_CLASS_FQN = "aware_attention.session.AttentionSession"
ATTENTION_SESSION_LAYOUT_CLASS_FQN = "aware_attention.session.AttentionSessionLayout"
ATTENTION_SESSION_SECTION_CLASS_FQN = "aware_attention.session.AttentionSessionSection"
ATTENTION_FOCUS_TRANSITION_CLASS_FQN = (
    "aware_attention.session.AttentionFocusTransition"
)
ATTENTION_LAYOUT_TRANSITION_CLASS_FQN = (
    "aware_attention.session.AttentionLayoutTransition"
)
ATTENTION_LAYOUT_TRANSITION_SECTION_CLASS_FQN = (
    "aware_attention.session.AttentionLayoutTransitionSection"
)
ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_CLASS_FQN = (
    "aware_attention.session.AttentionLayoutTopologyTransition"
)
ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_SECTION_CLASS_FQN = (
    "aware_attention.session.AttentionLayoutTopologyTransitionSection"
)

_ATTENTION_META_HANDLERS_ANY: Any = attention_meta_handlers
_ATTENTION_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ATTENTION_META_HANDLERS_ANY,
)
_ATTENTION_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ATTENTION_META_HANDLERS_ANY,
)


def _attention_session_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(
        repo_root / path
        for path in (
            "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
            "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
            "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        )
    )


def _build_attention_session_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_attention_session_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ATTENTION_META_HANDLER_MODULE,),
        bootstrap_modules=(_ATTENTION_META_BOOTSTRAP_MODULE,),
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


def _relationship_targets_by_key(
    runtime: MetaGraphRuntime, opg: Any
) -> dict[str, list[str]]:
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


def _class_fqns_in_opg(runtime: MetaGraphRuntime, opg: Any) -> set[str]:
    assert runtime.context is not None
    index = runtime.context.index
    return {
        index.class_configs_by_id[node.class_config_id].class_fqn
        for node in opg.object_projection_graph_nodes
    }


def _expect_uuid_primitive(
    assertions: Any,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


def test_attention_session_projection_portals_transition_source_truth(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    import aware_identity_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_attention_session_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        attention_session_opg = _opg_by_name_and_root(
            runtime,
            name="AttentionSession",
            root_class_fqn=ATTENTION_SESSION_CLASS_FQN,
        )
        transition_opg = _opg_by_name_and_root(
            runtime,
            name="AttentionFocusTransition",
            root_class_fqn=ATTENTION_FOCUS_TRANSITION_CLASS_FQN,
        )
        layout_transition_opg = _opg_by_name_and_root(
            runtime,
            name="AttentionLayoutTransition",
            root_class_fqn=ATTENTION_LAYOUT_TRANSITION_CLASS_FQN,
        )
        topology_transition_opg = _opg_by_name_and_root(
            runtime,
            name="AttentionLayoutTopologyTransition",
            root_class_fqn=ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_CLASS_FQN,
        )

        session_targets = _relationship_targets_by_key(runtime, attention_session_opg)
        transition_targets = _relationship_targets_by_key(runtime, transition_opg)
        session_class_fqns = _class_fqns_in_opg(runtime, attention_session_opg)
        layout_transition_class_fqns = _class_fqns_in_opg(
            runtime, layout_transition_opg
        )
        topology_transition_class_fqns = _class_fqns_in_opg(
            runtime, topology_transition_opg
        )

        assert session_targets["identity_session"] == ["aware_identity.session.Session"]
        assert session_targets["transitions"] == [ATTENTION_FOCUS_TRANSITION_CLASS_FQN]
        assert session_targets["active_transition"] == [
            ATTENTION_FOCUS_TRANSITION_CLASS_FQN
        ]
        assert ATTENTION_LAYOUT_TRANSITION_CLASS_FQN in session_class_fqns
        assert ATTENTION_LAYOUT_TRANSITION_SECTION_CLASS_FQN in session_class_fqns
        assert ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_CLASS_FQN in session_class_fqns
        assert (
            ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_SECTION_CLASS_FQN in session_class_fqns
        )
        assert session_targets["previous_transition"] == [
            ATTENTION_LAYOUT_TRANSITION_CLASS_FQN
        ]
        assert layout_transition_class_fqns == {
            ATTENTION_LAYOUT_TRANSITION_CLASS_FQN,
            ATTENTION_LAYOUT_TRANSITION_SECTION_CLASS_FQN,
        }
        assert _relationship_targets_by_key(runtime, layout_transition_opg)[
            "topology_transition"
        ] == [ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_CLASS_FQN]
        assert topology_transition_class_fqns == {
            ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_CLASS_FQN,
            ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_SECTION_CLASS_FQN,
        }
        assert transition_targets["focus_scope"] == ["aware_attention.focus.FocusScope"]
        assert transition_targets["focus"] == ["aware_attention.focus.Focus"]
        assert transition_targets["object_projection_graph_identity"] == [
            "aware_meta.graph.projection.ObjectProjectionGraphIdentity"
        ]
        assert transition_targets["object_instance_graph_branch"] == [
            "aware_meta.graph.instance.ObjectInstanceGraphIdentity"
        ]
        assert transition_targets["object_instance_graph_commit"] == [
            "aware_meta.graph.instance.ObjectInstanceGraphIdentity"
        ]


@pytest.mark.asyncio
async def test_attention_session_mounts_layout_and_section_runtime_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    import aware_identity_ontology  # noqa: F401

    ns = uuid5(NAMESPACE_URL, "aware://tests/attention/session-transition")
    identity_session_id = uuid5(ns, "identity_session")
    layout_id = uuid5(ns, "layout")
    layout_section_id = uuid5(ns, "layout_section")
    section_id = uuid5(ns, "section")
    attention_session_id = stable_attention_session_id(
        identity_session_id=identity_session_id,
    )
    session_layout_id = stable_attention_session_layout_id(
        attention_session_id=attention_session_id,
        layout_id=layout_id,
    )
    session_section_id = stable_attention_session_section_id(
        attention_session_layout_id=session_layout_id,
        layout_section_id=layout_section_id,
        section_id=section_id,
    )

    lane = LaneIds(
        branch_id=attention_session_id,
        actor_id=uuid4(),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_attention_session_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="AttentionSession",
            root_class_fqn=ATTENTION_SESSION_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_SESSION_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "identity_session_id": identity_session_id,
                        "key": "workspace",
                        "title": "Workspace Attention",
                        "description": None,
                        "purpose": "shared focus replay",
                    },
                    expected_root_object_id=attention_session_id,
                    allow_noop_commit=True,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_SESSION_CLASS_FQN,
                    function_name="mount_layout",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "layout_id": layout_id,
                        "layout_config_id": None,
                        "key": "workspace-layout",
                        "order": 0,
                        "is_active": True,
                    },
                    allow_noop_commit=True,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_SESSION_LAYOUT_CLASS_FQN,
                    function_name="attach_section",
                    object_id=SourceObjectId(session_layout_id),
                    kwargs={
                        "layout_section_id": layout_section_id,
                        "section_id": section_id,
                        "section_key": "code",
                        "order": 1,
                        "is_active": True,
                    },
                    allow_noop_commit=True,
                ),
            ],
        )

        assert result.root_object_id == attention_session_id
        assertions.expect_instance(attention_session_id)
        assertions.expect_instance(session_layout_id)
        assertions.expect_instance(session_section_id)
        assertions.expect_edge(
            source_id=attention_session_id,
            target_id=session_layout_id,
            relationship_name="layouts",
        )
        assertions.expect_edge(
            source_id=session_layout_id,
            target_id=session_section_id,
            relationship_name="sections",
        )
        assertions.expect_edge(
            source_id=session_layout_id,
            target_id=session_section_id,
            relationship_name="active_section",
        )


@pytest.mark.asyncio
async def test_attention_session_layout_transition_is_atomic_replayable_and_idempotent(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    import aware_identity_ontology  # noqa: F401

    ns = uuid5(NAMESPACE_URL, "aware://tests/attention/session-layout-transition")
    identity_session_id = uuid5(ns, "identity_session")
    layout_id = uuid5(ns, "layout")
    attention_session_id = stable_attention_session_id(
        identity_session_id=identity_session_id,
    )
    session_layout_id = stable_attention_session_layout_id(
        attention_session_id=attention_session_id,
        layout_id=layout_id,
    )
    section_coordinates = [
        (uuid5(ns, "layout_section:left"), uuid5(ns, "section:left"), "left"),
        (uuid5(ns, "layout_section:right"), uuid5(ns, "section:right"), "right"),
    ]
    session_section_ids = [
        stable_attention_session_section_id(
            attention_session_layout_id=session_layout_id,
            layout_section_id=layout_section_id,
            section_id=section_id,
        )
        for layout_section_id, section_id, _ in section_coordinates
    ]
    first_transition_id = stable_attention_layout_transition_id(
        attention_session_layout_id=session_layout_id,
        client_intent_id="divider-drag-1",
    )
    second_transition_id = stable_attention_layout_transition_id(
        attention_session_layout_id=session_layout_id,
        client_intent_id="divider-drag-2",
    )
    second_state_ids = [
        stable_attention_layout_transition_section_id(
            attention_layout_transition_id=second_transition_id,
            attention_session_section_id=session_section_id,
        )
        for session_section_id in session_section_ids
    ]

    def _vector(left_weight: int, right_weight: int) -> JsonObject:
        return JsonObject(
            {
                "sections": [
                    {
                        "attention_session_section_id": str(session_section_ids[0]),
                        "order": 0,
                        "weight_micros": left_weight,
                        "is_visible": True,
                        "is_collapsed": False,
                    },
                    {
                        "attention_session_section_id": str(session_section_ids[1]),
                        "order": 1,
                        "weight_micros": right_weight,
                        "is_visible": True,
                        "is_collapsed": False,
                    },
                ]
            }
        )

    calls = [
        ProofCall(
            target="constructor",
            class_fqn=ATTENTION_SESSION_CLASS_FQN,
            function_name="build",
            kwargs={
                "identity_session_id": identity_session_id,
                "key": "shared-layout",
                "title": "Shared layout",
                "description": None,
                "purpose": "atomic geometry replay",
            },
            expected_root_object_id=attention_session_id,
            allow_noop_commit=True,
        ),
        ProofCall(
            target="instance",
            class_fqn=ATTENTION_SESSION_CLASS_FQN,
            function_name="mount_layout",
            object_id=ROOT_OBJECT_ID,
            kwargs={
                "layout_id": layout_id,
                "layout_config_id": None,
                "key": "shared-layout",
                "order": 0,
                "is_active": True,
            },
            allow_noop_commit=True,
        ),
    ]
    calls.extend(
        ProofCall(
            target="instance",
            class_fqn=ATTENTION_SESSION_LAYOUT_CLASS_FQN,
            function_name="attach_section",
            object_id=SourceObjectId(session_layout_id),
            kwargs={
                "layout_section_id": layout_section_id,
                "section_id": section_id,
                "section_key": section_key,
                "order": order,
                "is_active": True,
            },
            allow_noop_commit=True,
        )
        for order, (layout_section_id, section_id, section_key) in enumerate(
            section_coordinates
        )
    )
    calls.extend(
        [
            ProofCall(
                target="instance",
                class_fqn=ATTENTION_SESSION_LAYOUT_CLASS_FQN,
                function_name="apply_layout_transition",
                object_id=SourceObjectId(session_layout_id),
                kwargs={
                    "client_intent_id": "divider-drag-1",
                    "expected_previous_layout_transition_id": None,
                    "section_states_json": _vector(600_000, 400_000),
                    "transition_kind": "divider_drag_end",
                    "source_kind": "flutter",
                    "source_ref": "divider:left:right",
                    "metadata_json": {"axis": "horizontal"},
                },
            ),
            ProofCall(
                target="instance",
                class_fqn=ATTENTION_SESSION_LAYOUT_CLASS_FQN,
                function_name="apply_layout_transition",
                object_id=SourceObjectId(session_layout_id),
                kwargs={
                    "client_intent_id": "divider-drag-2",
                    "expected_previous_layout_transition_id": first_transition_id,
                    "section_states_json": _vector(550_000, 450_000),
                    "transition_kind": "divider_drag_end",
                    "source_kind": "flutter",
                    "source_ref": "divider:left:right",
                    "metadata_json": {"axis": "horizontal"},
                },
            ),
            ProofCall(
                target="instance",
                class_fqn=ATTENTION_SESSION_LAYOUT_CLASS_FQN,
                function_name="apply_layout_transition",
                object_id=SourceObjectId(session_layout_id),
                kwargs={
                    "client_intent_id": "divider-drag-2",
                    "expected_previous_layout_transition_id": first_transition_id,
                    "section_states_json": _vector(550_000, 450_000),
                    "transition_kind": "divider_drag_end",
                    "source_kind": "flutter",
                    "source_ref": "divider:left:right",
                    "metadata_json": {"axis": "horizontal"},
                },
                allow_noop_commit=True,
            ),
        ]
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_attention_session_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(branch_id=attention_session_id, actor_id=uuid4()),
            opg_name="AttentionSession",
            root_class_fqn=ATTENTION_SESSION_CLASS_FQN,
            calls=calls,
        )

        assert len(result.responses) == 7
        assert result.responses[-2].commit_id is not None
        assert result.responses[-1].commit_id is None
        assert len(result.commits) == 6
        assert result.head["commit_id"] == str(result.responses[-2].commit_id)
        assertions.expect_instance(first_transition_id)
        assertions.expect_instance(second_transition_id)
        assertions.expect_edge(
            source_id=session_layout_id,
            target_id=second_transition_id,
            relationship_name="layout_transitions",
        )
        assertions.expect_edge(
            source_id=session_layout_id,
            target_id=second_transition_id,
            relationship_name="active_layout_transition",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=second_transition_id,
            field_name="previous_transition_id",
            expected=first_transition_id,
        )
        for order, (state_id, session_section_id, weight_micros) in enumerate(
            zip(second_state_ids, session_section_ids, (550_000, 450_000), strict=True)
        ):
            assertions.expect_instance(state_id)
            assertions.expect_edge(
                source_id=second_transition_id,
                target_id=state_id,
                relationship_name="section_states",
            )
            assertions.expect_primitive(
                instance_id=state_id,
                field_name="order",
                expected=order,
            )
            assertions.expect_primitive(
                instance_id=state_id,
                field_name="weight_micros",
                expected=weight_micros,
            )
            _expect_uuid_primitive(
                assertions,
                instance_id=state_id,
                field_name="attention_session_section_id",
                expected=session_section_id,
            )
        for order, session_section_id in enumerate(session_section_ids):
            assertions.expect_primitive(
                instance_id=session_section_id,
                field_name="order",
                expected=order,
            )
            assertions.expect_primitive(
                instance_id=session_section_id,
                field_name="is_active",
                expected=True,
            )


@pytest.mark.asyncio
async def test_attention_focus_transition_source_projection_runtime_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    import aware_identity_ontology  # noqa: F401

    ns = uuid5(NAMESPACE_URL, "aware://tests/attention/focus-transition-source")
    session_section_id = uuid5(ns, "session_section")
    focus_scope_id = uuid5(ns, "focus_scope")
    focus_id = uuid5(ns, "focus")
    observable_id = uuid5(ns, "observable")
    opgi_id = uuid5(ns, "opgi")
    oigb_id = uuid5(ns, "oigb")
    oigc_id = uuid5(ns, "oigc")
    transition_id = stable_attention_focus_transition_id(
        attention_session_section_id=session_section_id,
        focus_scope_id=focus_scope_id,
        transition_key="workspace-focus",
    )
    projection_hash = "sha256:test:attention-focus-transition"

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_attention_session_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(branch_id=transition_id, actor_id=uuid4()),
            opg_name="AttentionFocusTransition",
            root_class_fqn=ATTENTION_FOCUS_TRANSITION_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_FOCUS_TRANSITION_CLASS_FQN,
                    function_name="create_via_attention_session_section",
                    kwargs={
                        "attention_session_section_id": session_section_id,
                        "transition_key": "workspace-focus",
                        "focus_scope_id": focus_scope_id,
                        "focus_id": focus_id,
                        "observable_id": observable_id,
                        "object_projection_graph_identity_id": opgi_id,
                        "object_instance_graph_branch_id": oigb_id,
                        "object_instance_graph_commit_id": oigc_id,
                        "sequence": 1,
                        "projection_hash": projection_hash,
                        "transition_kind": "focus",
                        "rationale": "operator moved focus to code section",
                    },
                    expected_root_object_id=transition_id,
                )
            ],
        )

        assert result.root_object_id == transition_id
        assertions.expect_instance(transition_id)
        assertions.expect_primitive(
            instance_id=transition_id,
            field_name="projection_hash",
            expected=projection_hash,
        )
        assertions.expect_primitive(
            instance_id=transition_id,
            field_name="sequence",
            expected=1,
        )
        assertions.expect_primitive(
            instance_id=transition_id,
            field_name="transition_kind",
            expected="focus",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=transition_id,
            field_name="attention_session_section_id",
            expected=session_section_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=transition_id,
            field_name="focus_scope_id",
            expected=focus_scope_id,
        )


@pytest.mark.asyncio
async def test_attention_session_section_append_transition_handler_links_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_attention.handlers.impl.session import (
        attention_session_section as section_impl,
    )
    from aware_attention_ontology.session.attention_focus_transition import (
        AttentionFocusTransition,
    )
    from aware_attention_ontology.session.attention_session_section import (
        AttentionSessionSection,
    )

    ns = uuid5(NAMESPACE_URL, "aware://tests/attention/append-transition-handler")
    session_section_id = uuid5(ns, "session_section")
    focus_scope_id = uuid5(ns, "focus_scope")
    transition_id = stable_attention_focus_transition_id(
        attention_session_section_id=session_section_id,
        focus_scope_id=focus_scope_id,
        transition_key="workspace-focus",
    )
    session_section = AttentionSessionSection(
        id=session_section_id,
        attention_session_layout_id=uuid5(ns, "session_layout"),
        layout_section_id=uuid5(ns, "layout_section"),
        section_id=uuid5(ns, "section"),
    )

    async def _fake_create_via_attention_session_section(
        **kwargs: Any,
    ) -> AttentionFocusTransition:
        assert kwargs["attention_session_section_id"] == session_section_id
        assert kwargs["focus_scope_id"] == focus_scope_id
        return AttentionFocusTransition(
            id=transition_id,
            attention_session_section_id=kwargs["attention_session_section_id"],
            transition_key=kwargs["transition_key"],
            focus_scope_id=kwargs["focus_scope_id"],
            sequence=kwargs["sequence"],
            transition_kind=kwargs["transition_kind"],
            projection_hash=kwargs["projection_hash"],
        )

    monkeypatch.setattr(
        AttentionFocusTransition,
        "create_via_attention_session_section",
        _fake_create_via_attention_session_section,
    )

    transition = await section_impl.append_transition(
        session_section,
        transition_key="workspace-focus",
        focus_scope_id=focus_scope_id,
        sequence=1,
        projection_hash="sha256:test:append-transition-handler",
        transition_kind="focus",
    )

    assert transition.id == transition_id
    assert session_section.transitions == [transition]
    assert session_section.active_transition == transition


@pytest.mark.asyncio
async def test_attention_layout_transition_handler_fails_closed_on_invalid_vectors() -> (
    None
):
    from aware_attention.handlers.impl.session import (
        attention_session_layout as layout_impl,
    )
    from aware_attention_ontology.session.attention_session_layout import (
        AttentionSessionLayout,
    )
    from aware_attention_ontology.session.attention_session_section import (
        AttentionSessionSection,
    )

    ns = uuid5(NAMESPACE_URL, "aware://tests/attention/layout-transition-validation")
    layout_id = uuid5(ns, "session_layout")
    sections = [
        AttentionSessionSection(
            id=uuid5(ns, f"session_section:{index}"),
            attention_session_layout_id=layout_id,
            layout_section_id=uuid5(ns, f"layout_section:{index}"),
            section_id=uuid5(ns, f"section:{index}"),
            order=index,
        )
        for index in range(2)
    ]
    layout = AttentionSessionLayout(
        id=layout_id,
        attention_session_id=uuid5(ns, "attention_session"),
        layout_id=uuid5(ns, "layout"),
        sections=sections,
    )

    def _vector(
        *,
        first_weight: int = 600_000,
        second_weight: int = 400_000,
        second_order: int = 1,
        second_section_id: UUID | None = None,
        second_visible: bool = True,
    ) -> JsonObject:
        return JsonObject(
            {
                "sections": [
                    {
                        "attention_session_section_id": str(sections[0].id),
                        "order": 0,
                        "weight_micros": first_weight,
                        "is_visible": True,
                        "is_collapsed": False,
                    },
                    {
                        "attention_session_section_id": str(
                            second_section_id or sections[1].id
                        ),
                        "order": second_order,
                        "weight_micros": second_weight,
                        "is_visible": second_visible,
                        "is_collapsed": False,
                    },
                ]
            }
        )

    with pytest.raises(ValueError, match="sum to 1000000"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="invalid-weight",
            section_states_json=_vector(first_weight=500_000, second_weight=400_000),
        )
    with pytest.raises(ValueError, match="duplicate section order"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="duplicate-order",
            section_states_json=_vector(second_order=0),
        )
    with pytest.raises(ValueError, match="exactly match mounted sections"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="unknown-section",
            section_states_json=_vector(second_section_id=uuid5(ns, "unknown")),
        )
    with pytest.raises(ValueError, match="hidden or collapsed"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="hidden-weight",
            section_states_json=_vector(second_visible=False),
        )
    assert layout.layout_transitions == []
    assert layout.active_layout_transition is None


@pytest.mark.asyncio
async def test_attention_layout_transition_handler_enforces_cas_and_intent_collision() -> (
    None
):
    from aware_attention.handlers.impl.session import (
        attention_session_layout as layout_impl,
    )
    from aware_attention_ontology.session.attention_layout_transition import (
        AttentionLayoutTransition,
    )
    from aware_attention_ontology.session.attention_layout_transition_section import (
        AttentionLayoutTransitionSection,
    )
    from aware_attention_ontology.session.attention_session_layout import (
        AttentionSessionLayout,
    )
    from aware_attention_ontology.session.attention_session_section import (
        AttentionSessionSection,
    )

    ns = uuid5(NAMESPACE_URL, "aware://tests/attention/layout-transition-cas")
    layout_id = uuid5(ns, "session_layout")
    previous_transition_id = uuid5(ns, "previous_transition")
    sections = [
        AttentionSessionSection(
            id=uuid5(ns, f"session_section:{index}"),
            attention_session_layout_id=layout_id,
            layout_section_id=uuid5(ns, f"layout_section:{index}"),
            section_id=uuid5(ns, f"section:{index}"),
            order=index,
        )
        for index in range(2)
    ]
    transition_id = stable_attention_layout_transition_id(
        attention_session_layout_id=layout_id,
        client_intent_id="divider-drag",
    )
    states = [
        AttentionLayoutTransitionSection(
            id=stable_attention_layout_transition_section_id(
                attention_layout_transition_id=transition_id,
                attention_session_section_id=section.id,
            ),
            attention_layout_transition_id=transition_id,
            attention_session_section=section,
            attention_session_section_id=section.id,
            order=index,
            weight_micros=weight,
            is_visible=True,
            is_collapsed=False,
        )
        for index, (section, weight) in enumerate(
            zip(sections, (600_000, 400_000), strict=True)
        )
    ]
    transition = AttentionLayoutTransition(
        id=transition_id,
        attention_session_layout_id=layout_id,
        client_intent_id="divider-drag",
        previous_transition_id=previous_transition_id,
        sequence=1,
        transition_kind="divider_drag_end",
        source_kind="flutter",
        source_ref="divider:left:right",
        metadata_json=JsonObject({"axis": "horizontal"}),
        section_states=states,
    )
    layout = AttentionSessionLayout(
        id=layout_id,
        attention_session_id=uuid5(ns, "attention_session"),
        layout_id=uuid5(ns, "layout"),
        sections=sections,
        layout_transitions=[transition],
        active_layout_transition=transition,
        active_layout_transition_id=transition.id,
    )

    def _vector(first_weight: int, second_weight: int) -> JsonObject:
        return JsonObject(
            {
                "sections": [
                    {
                        "attention_session_section_id": str(sections[0].id),
                        "order": 0,
                        "weight_micros": first_weight,
                        "is_visible": True,
                        "is_collapsed": False,
                    },
                    {
                        "attention_session_section_id": str(sections[1].id),
                        "order": 1,
                        "weight_micros": second_weight,
                        "is_visible": True,
                        "is_collapsed": False,
                    },
                ]
            }
        )

    retried = await layout_impl.apply_layout_transition(
        layout,
        client_intent_id="DIVIDER-DRAG",
        expected_previous_layout_transition_id=previous_transition_id,
        section_states_json=_vector(600_000, 400_000),
        transition_kind="divider_drag_end",
        source_kind="flutter",
        source_ref="divider:left:right",
        metadata_json=JsonObject({"axis": "horizontal"}),
    )
    assert retried is transition
    assert len(layout.layout_transitions) == 1

    with pytest.raises(ValueError, match="collides with a different"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="divider-drag",
            expected_previous_layout_transition_id=previous_transition_id,
            section_states_json=_vector(550_000, 450_000),
            transition_kind="divider_drag_end",
            source_kind="flutter",
            source_ref="divider:left:right",
            metadata_json=JsonObject({"axis": "horizontal"}),
        )
    with pytest.raises(ValueError, match="stale expected previous"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="new-divider-drag",
            expected_previous_layout_transition_id=previous_transition_id,
            section_states_json=_vector(500_000, 500_000),
        )


@pytest.mark.asyncio
async def test_attention_topology_history_pins_dynamic_geometry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_attention.handlers.impl.session import (
        attention_session_layout as layout_impl,
    )
    from aware_attention_ontology.session.attention_layout_topology_transition import (
        AttentionLayoutTopologyTransition,
    )
    from aware_attention_ontology.session.attention_layout_topology_transition_section import (
        AttentionLayoutTopologyTransitionSection,
    )
    from aware_attention_ontology.session.attention_layout_transition import (
        AttentionLayoutTransition,
    )
    from aware_attention_ontology.session.attention_layout_transition_section import (
        AttentionLayoutTransitionSection,
    )
    from aware_attention_ontology.session.attention_session_layout import (
        AttentionSessionLayout,
    )
    from aware_attention_ontology.session.attention_session_section import (
        AttentionSessionSection,
    )

    layout_id = uuid4()
    sections = [
        AttentionSessionSection(
            id=uuid4(),
            attention_session_layout_id=layout_id,
            layout_section_id=uuid4(),
            section_id=uuid4(),
            section_key=key,
            order=order,
        )
        for order, key in enumerate(("left", "center", "right"))
    ]
    layout = AttentionSessionLayout(
        id=layout_id,
        attention_session_id=uuid4(),
        layout_id=uuid4(),
        sections=sections,
        active_section=sections[0],
        active_section_id=sections[0].id,
    )

    async def _create_topology_transition(
        **kwargs: Any,
    ) -> AttentionLayoutTopologyTransition:
        return AttentionLayoutTopologyTransition(
            id=stable_attention_layout_topology_transition_id(
                attention_session_layout_id=kwargs["attention_session_layout_id"],
                client_intent_id=kwargs["client_intent_id"],
            ),
            **kwargs,
        )

    async def _create_topology_state(
        **kwargs: Any,
    ) -> AttentionLayoutTopologyTransitionSection:
        return AttentionLayoutTopologyTransitionSection(
            id=stable_attention_layout_topology_transition_section_id(
                attention_layout_topology_transition_id=kwargs[
                    "attention_layout_topology_transition_id"
                ],
                attention_session_section_id=kwargs["attention_session_section_id"],
            ),
            **kwargs,
        )

    async def _create_layout_transition(
        **kwargs: Any,
    ) -> AttentionLayoutTransition:
        return AttentionLayoutTransition(
            id=stable_attention_layout_transition_id(
                attention_session_layout_id=kwargs["attention_session_layout_id"],
                client_intent_id=kwargs["client_intent_id"],
            ),
            **kwargs,
        )

    async def _create_layout_state(
        **kwargs: Any,
    ) -> AttentionLayoutTransitionSection:
        return AttentionLayoutTransitionSection(
            id=stable_attention_layout_transition_section_id(
                attention_layout_transition_id=kwargs["attention_layout_transition_id"],
                attention_session_section_id=kwargs["attention_session_section_id"],
            ),
            **kwargs,
        )

    monkeypatch.setattr(
        AttentionLayoutTopologyTransition,
        "create_via_attention_session_layout",
        _create_topology_transition,
    )
    monkeypatch.setattr(
        AttentionLayoutTopologyTransitionSection,
        "create_via_attention_layout_topology_transition",
        _create_topology_state,
    )
    monkeypatch.setattr(
        AttentionLayoutTransition,
        "create_via_attention_session_layout",
        _create_layout_transition,
    )
    monkeypatch.setattr(
        AttentionLayoutTransitionSection,
        "create_via_attention_layout_transition",
        _create_layout_state,
    )

    def _topology_vector(*section_indexes: int) -> JsonObject:
        return JsonObject(
            {
                "sections": [
                    {
                        "attention_session_section_id": str(sections[section_index].id),
                        "order": order,
                    }
                    for order, section_index in enumerate(section_indexes)
                ]
            }
        )

    def _geometry_vector(
        *section_indexes_and_weights: tuple[int, int],
    ) -> JsonObject:
        return JsonObject(
            {
                "sections": [
                    {
                        "attention_session_section_id": str(sections[section_index].id),
                        "order": order,
                        "weight_micros": weight,
                        "is_visible": True,
                        "is_collapsed": False,
                    }
                    for order, (section_index, weight) in enumerate(
                        section_indexes_and_weights
                    )
                ]
            }
        )

    first = await layout_impl.apply_topology_transition(
        layout,
        client_intent_id="topology-1",
        section_states_json=_topology_vector(0, 1, 2),
        source_kind="shared_client",
    )
    assert first.sequence == 0
    assert layout.active_topology_transition is first
    assert [state.attention_session_section_id for state in first.section_states] == [
        section.id for section in sections
    ]

    replay = await layout_impl.apply_topology_transition(
        layout,
        client_intent_id="TOPOLOGY-1",
        section_states_json=_topology_vector(0, 1, 2),
        source_kind="shared_client",
    )
    assert replay is first
    assert len(layout.topology_transitions) == 1

    with pytest.raises(ValueError, match="collides with a different"):
        await layout_impl.apply_topology_transition(
            layout,
            client_intent_id="topology-1",
            section_states_json=_topology_vector(1, 0, 2),
            source_kind="shared_client",
        )
    with pytest.raises(ValueError, match="stale expected previous topology"):
        await layout_impl.apply_topology_transition(
            layout,
            client_intent_id="topology-stale",
            expected_previous_topology_transition_id=uuid4(),
            section_states_json=_topology_vector(0, 1, 2),
        )
    with pytest.raises(ValueError, match="current active section must survive"):
        await layout_impl.apply_topology_transition(
            layout,
            client_intent_id="remove-active",
            expected_previous_topology_transition_id=first.id,
            section_states_json=_topology_vector(1, 2),
        )
    with pytest.raises(ValueError, match="unknown admitted section"):
        await layout_impl.apply_topology_transition(
            layout,
            client_intent_id="unknown-anchor",
            expected_previous_topology_transition_id=first.id,
            section_states_json=JsonObject(
                {
                    "sections": [
                        {
                            "attention_session_section_id": str(uuid4()),
                            "order": 0,
                        }
                    ]
                }
            ),
        )
    with pytest.raises(ValueError, match="duplicate section order"):
        await layout_impl.apply_topology_transition(
            layout,
            client_intent_id="duplicate-order",
            expected_previous_topology_transition_id=first.id,
            section_states_json=JsonObject(
                {
                    "sections": [
                        {
                            "attention_session_section_id": str(sections[0].id),
                            "order": 0,
                        },
                        {
                            "attention_session_section_id": str(sections[1].id),
                            "order": 0,
                        },
                    ]
                }
            ),
        )

    second = await layout_impl.apply_topology_transition(
        layout,
        client_intent_id="topology-2",
        expected_previous_topology_transition_id=first.id,
        section_states_json=_topology_vector(1, 0),
    )
    assert second.previous_topology_transition_id == first.id
    assert second.sequence == 1
    assert [state.attention_session_section_id for state in second.section_states] == [
        sections[1].id,
        sections[0].id,
    ]
    assert [section.id for section in layout.sections] == [
        section.id for section in sections
    ]

    with pytest.raises(ValueError, match="must exactly pin the active topology"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="geometry-missing-pin",
            section_states_json=_geometry_vector((1, 500_000), (0, 500_000)),
        )
    with pytest.raises(ValueError, match="exactly match mounted sections"):
        await layout_impl.apply_layout_transition(
            layout,
            client_intent_id="geometry-stale-membership",
            topology_transition_id=second.id,
            section_states_json=_geometry_vector(
                (1, 400_000),
                (0, 300_000),
                (2, 300_000),
            ),
        )

    geometry = await layout_impl.apply_layout_transition(
        layout,
        client_intent_id="geometry-2",
        topology_transition_id=second.id,
        section_states_json=_geometry_vector((1, 550_000), (0, 450_000)),
    )
    assert geometry.topology_transition_id == second.id
    assert [
        state.attention_session_section_id for state in geometry.section_states
    ] == [
        sections[1].id,
        sections[0].id,
    ]
    assert layout.active_layout_transition is geometry

    third = await layout_impl.apply_topology_transition(
        layout,
        client_intent_id="topology-3",
        expected_previous_topology_transition_id=second.id,
        section_states_json=_topology_vector(0, 2, 1),
    )
    assert third.sequence == 2
    assert [state.attention_session_section_id for state in third.section_states] == [
        sections[0].id,
        sections[2].id,
        sections[1].id,
    ]
    assert layout.active_layout_transition is None
    assert len(layout.sections) == 3
