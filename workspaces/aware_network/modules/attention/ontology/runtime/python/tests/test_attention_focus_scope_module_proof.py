from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

import pytest

from aware_attention.handlers._generated import meta_handlers as attention_meta_handlers
from aware_attention_ontology.stable_ids import stable_focus_scope_commit_id
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


def _expect_datetime_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: str,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    if isinstance(value, datetime):
        assert value.isoformat().replace("+00:00", "Z") == expected
    else:
        assert value == expected


@pytest.mark.asyncio
async def test_focus_scope_build_set_focus_set_observable_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        ns = uuid5(NAMESPACE_URL, "aware://tests/attention/focus-scope")
        focus_scope_id = uuid5(ns, "focus_scope")
        focus_id = uuid5(ns, "focus")
        observable_id = uuid5(ns, "observable")
        last_accessed = "2026-02-04T00:20:47.554797Z"

        lane = LaneIds(
            branch_id=focus_scope_id,
            actor_id=uuid4(),
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="FocusScope",
            root_class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "title": "This device",
                        "description": "Personal scope (per-thread)",
                        "expires_at": None,
                        "is_active": True,
                        "last_accessed": last_accessed,
                    },
                    expected_root_object_id=focus_scope_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
                    function_name="set_focus",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "focus_id": focus_id,
                        "rationale": "set_focus",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
                    function_name="set_observable",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "observable_id": observable_id,
                        "rationale": "set_observable",
                    },
                ),
            ],
        )

        assertions.expect_root(focus_scope_id)
        assertions.expect_instance(focus_scope_id)
        assertions.expect_primitive(
            instance_id=focus_scope_id,
            field_name="title",
            expected="This device",
        )
        assertions.expect_primitive(
            instance_id=focus_scope_id,
            field_name="description",
            expected="Personal scope (per-thread)",
        )
        assertions.expect_primitive(
            instance_id=focus_scope_id,
            field_name="is_active",
            expected=True,
        )
        _expect_datetime_primitive(
            assertions,
            instance_id=focus_scope_id,
            field_name="last_accessed",
            expected=last_accessed,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=focus_scope_id,
            field_name="focus_id",
            expected=focus_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=focus_scope_id,
            field_name="observable_id",
            expected=observable_id,
        )
        assertions.expect_primitive(
            instance_id=focus_scope_id,
            field_name="rationale",
            expected="set_observable",
        )
        focus_scope_ci_id = _class_instance_id_for_source(
            assertions=assertions,
            source_object_id=focus_scope_id,
        )

        instance_ids = {
            ci.id for ci in assertions.oig.class_instances if ci.id is not None
        }
        assert focus_id not in instance_ids
        assert observable_id not in instance_ids

        updated_ids: set[UUID] = set()
        for commit in result.commits:
            for root in commit.object_instance_graph_changes:
                for ci_change in root.class_instance_changes:
                    if ci_change.change.type in {ChangeType.update, ChangeType.delete}:
                        updated_ids.add(ci_change.class_instance_id)
        assert updated_ids <= {focus_scope_ci_id}

        observed_commit_id = result.commits[-1].id
        assert observed_commit_id is not None
        focus_scope_commit_id = stable_focus_scope_commit_id(
            focus_scope_id=focus_scope_id,
            focus_id=focus_id,
            object_instance_graph_commit_id=observed_commit_id,
        )

        pin_result, pin_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="FocusScope",
            root_class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_FOCUS_SCOPE_CLASS_FQN,
                    function_name="ensure_commit",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "focus_id": focus_id,
                        "object_instance_graph_commit_id": observed_commit_id,
                    },
                ),
            ],
        )

        assert pin_result.commits[-1].id != observed_commit_id
        pin_assertions.expect_root(focus_scope_id)
        pin_assertions.expect_instance(focus_scope_commit_id)
        pin_assertions.expect_edge(
            source_id=focus_scope_id,
            target_id=focus_scope_commit_id,
            relationship_name="commits",
        )
        _expect_uuid_primitive(
            pin_assertions,
            instance_id=focus_scope_commit_id,
            field_name="focus_scope_id",
            expected=focus_scope_id,
        )
        _expect_uuid_primitive(
            pin_assertions,
            instance_id=focus_scope_commit_id,
            field_name="focus_id",
            expected=focus_id,
        )
        _expect_uuid_primitive(
            pin_assertions,
            instance_id=focus_scope_commit_id,
            field_name="object_instance_graph_commit_id",
            expected=observed_commit_id,
        )

        pin_instance_ids = {
            ci.id for ci in pin_assertions.oig.class_instances if ci.id is not None
        }
        assert focus_id not in pin_instance_ids
        assert observed_commit_id not in pin_instance_ids
