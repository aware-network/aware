from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

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
    run_meta_runtime_proof,
)
from ._attention_module_proof_paths import REPO_ROOT


ATTENTION_FOCUS_CLASS_FQN = "aware_attention.focus.Focus"

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
async def test_focus_build_uses_opgi_identity_and_optional_oigb_link(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    from aware_attention_ontology.stable_ids import (
        stable_focus_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        ns = uuid5(NAMESPACE_URL, "aware://tests/attention/focus")
        focus_scope_id = uuid5(ns, "focus_scope")
        target_opgi_id = uuid5(ns, "target_opgi")
        target_oigb_id = uuid5(ns, "target_oigb")
        target_projection_hash = "sha256:test:target"
        focus_id = stable_focus_id(
            object_projection_graph_identity_id=target_opgi_id,
            focus_scope_id=focus_scope_id,
        )

        lane = LaneIds(
            branch_id=focus_id,
            actor_id=uuid4(),
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Focus",
            root_class_fqn=ATTENTION_FOCUS_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_FOCUS_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "focus_scope_id": focus_scope_id,
                        "object_projection_graph_identity_id": target_opgi_id,
                        "projection_hash": target_projection_hash,
                        "object_instance_graph_branch_id": target_oigb_id,
                        "target_type": "lane",
                        "target_id": uuid5(ns, "target_id"),
                        "description": "test focus",
                        "is_active": True,
                    },
                    expected_root_object_id=focus_id,
                )
            ],
        )

        assertions.expect_root(focus_id)
        assertions.expect_instance(focus_id)
        assertions.expect_primitive(
            instance_id=focus_id,
            field_name="projection_hash",
            expected=target_projection_hash,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=focus_id,
            field_name="focus_scope_id",
            expected=focus_scope_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=focus_id,
            field_name="object_projection_graph_identity_id",
            expected=target_opgi_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=focus_id,
            field_name="object_instance_graph_branch_id",
            expected=target_oigb_id,
        )
        assert result.root_object_id == focus_id
