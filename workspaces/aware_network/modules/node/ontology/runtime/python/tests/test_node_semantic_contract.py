from __future__ import annotations

from pathlib import Path

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_node.semantic_contract import (
    NODE_MATERIALIZATION_REQUIRED_PROJECTIONS,
    NODE_MATERIALIZATION_RUNTIME,
    NODE_MATERIALIZATION_RUNTIME_CONTEXT,
    NODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
    NODE_PROVIDER_OWNER,
)

_RUNTIME_CONTEXT_CONTRACT = (
    "Meta-owned Node Workspace semantic materialization runtime context"
)
_NODE_MODULE_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)


def _ensure_node_module_plugin_registered() -> None:
    AwareModulePluginRegistry.clear()
    AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
        module_roots=(_NODE_MODULE_ROOT,),
    )


def test_node_materialization_runtime_uses_node_package_truth() -> None:
    assert len(NODE_MATERIALIZATION_RUNTIME) == 1
    descriptor = NODE_MATERIALIZATION_RUNTIME[0]

    assert descriptor.semantic_owner == NODE_PROVIDER_OWNER
    assert (
        descriptor.runtime_ontology_package_names
        == NODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert descriptor.lane_projection_name == "NodePackage"
    assert descriptor.required_projection_names == (
        NODE_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    assert descriptor.include_package_dependency_closure is True


def test_node_declares_meta_owned_materialization_runtime_context() -> None:
    assert len(NODE_MATERIALIZATION_RUNTIME_CONTEXT) == 1
    descriptor = NODE_MATERIALIZATION_RUNTIME_CONTEXT[0]

    assert descriptor.semantic_owner == NODE_PROVIDER_OWNER
    assert descriptor.callable_module == "aware_meta.runtime.graph_context"
    assert (
        descriptor.callable_name
        == "build_meta_workspace_materialization_runtime_context"
    )
    assert descriptor.required is True
    assert descriptor.provider_payload == {
        "contract": _RUNTIME_CONTEXT_CONTRACT,
        "runtime_ontology_package_names": (
            NODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
    }


def test_node_runtime_context_resolves_through_registry() -> None:
    _ensure_node_module_plugin_registered()

    descriptors = AwareModulePluginRegistry.semantic_materialization_runtime_context_for_provider_key(
        provider_key="aware_node",
        semantic_owner=NODE_PROVIDER_OWNER,
    )

    assert descriptors == NODE_MATERIALIZATION_RUNTIME_CONTEXT


def test_node_runtime_context_callable_resolves_through_registry() -> None:
    _ensure_node_module_plugin_registered()

    resolvers = AwareModulePluginRegistry.resolve_semantic_materialization_runtime_context_resolvers(
        provider_key="aware_node",
        semantic_owner=NODE_PROVIDER_OWNER,
    )

    assert len(resolvers) == 1
    resolver = resolvers[0]
    assert resolver.provider_key == "aware_node"
    assert resolver.semantic_owner == NODE_PROVIDER_OWNER
    assert resolver.callable_module == "aware_meta.runtime.graph_context"
    assert (
        resolver.callable_name == "build_meta_workspace_materialization_runtime_context"
    )
    assert resolver.required is True


def test_node_authored_manifests_do_not_depend_on_structure_ontology() -> None:
    for relative_path in (
        "workspaces/aware_network/modules/node/ontology/aware.ontology.toml",
        "workspaces/aware_network/modules/node/ontology/structure/aware.toml",
    ):
        source = (_REPO_ROOT / relative_path).read_text(encoding="utf-8")

        assert "structure-ontology" not in source
        assert "aware_structure" not in source
