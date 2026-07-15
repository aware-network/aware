from __future__ import annotations

from pathlib import Path

from ._paths import IDENTITY_RUNTIME_SOURCE_ROOT, REPO_ROOT


_CALLER_PATHS = (
    "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/actor/commit.py",
    "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/actor/subscription.py",
    "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity/ontology/materialization/assignment.py",
)


def test_identity_materialization_bootstrap_imports_are_facaded() -> None:
    repo_root = REPO_ROOT
    for relative_path in _CALLER_PATHS:
        source = (repo_root / Path(relative_path)).read_text(encoding="utf-8")
        assert "from aware_runtime.function_call.actor_identity import" not in source
        assert "from aware_runtime.materialization.module_context import" not in source
        assert "build_default_" not in source
        assert "default_identity_repo_root" not in source
        assert "context or await" not in source
        assert "resolve_actor_identity_binding" in source

    facade_source = (
        IDENTITY_RUNTIME_SOURCE_ROOT / "materialization" / "bootstrap.py"
    ).read_text(encoding="utf-8")
    assert "aware_runtime" not in facade_source
    assert "import_module(" not in facade_source
    assert "tomllib" not in facade_source
    assert "aware.workspace.toml" not in facade_source
    assert "aware-network.workspace.toml" not in facade_source
    assert "aware.module.toml" not in facade_source
    assert "module_ids" not in facade_source
    assert "_declared_workspace_module_roots" not in facade_source
    assert "_bridge_ontology_descriptor_paths" not in facade_source
    assert "default_identity_repo_root" not in facade_source
    assert "parents[" not in facade_source
    assert "build_meta_workspace_materialization_runtime_context" in facade_source
    assert "reify_oig_session" in facade_source
