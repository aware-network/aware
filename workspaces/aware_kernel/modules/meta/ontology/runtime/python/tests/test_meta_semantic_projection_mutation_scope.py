from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import SemanticScopeRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta import semantic_scope as meta_semantic_scope
from aware_meta.semantic_contract import (
    AWARE_META_SEMANTIC_CONTRACT,
    META_MATERIALIZATION_DELTA_ADAPTER_METADATA,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_CALL_BINDING_REFS,
    META_OBJECT_CONFIG_GRAPH_OWNER,
    META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE,
    META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY,
    META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES,
    META_OBJECT_CONFIG_GRAPH_SOURCE_BINDING_REFS,
    META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES,
    META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPES,
    META_SEMANTIC_SCOPE_KEYS,
)
from aware_meta.semantic_projection_mutation_scope import (
    META_SEMANTIC_PROJECTION_MUTATION_SCOPE_CONTRACT_VERSION,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY,
)


@contextmanager
def _isolated_semantic_scope_registry() -> Iterator[None]:
    SemanticScopeRegistry.clear()
    try:
        yield
    finally:
        SemanticScopeRegistry.clear()


def test_meta_projection_mutation_scope_descriptor_covers_ocg_projection_nodes() -> (
    None
):
    descriptor = META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE
    payload = descriptor.evidence_payload()

    assert (
        descriptor.scope_key == META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY
    )
    assert descriptor.scope_key in AWARE_META_SEMANTIC_CONTRACT.semantic_scope_keys
    assert META_SEMANTIC_SCOPE_KEYS == (
        META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY,
    )
    assert META_SEMANTIC_PROJECTION_MUTATION_SCOPES == (descriptor,)
    assert payload["contract_version"] == (
        META_SEMANTIC_PROJECTION_MUTATION_SCOPE_CONTRACT_VERSION
    )
    assert payload["semantic_owner"] == META_OBJECT_CONFIG_GRAPH_OWNER
    assert payload["projection_name"] == "ObjectConfigGraphPackage"
    assert "ObjectProjectionGraph" in payload["projection_refs"]
    assert "ObjectInstanceGraphIdentity" in payload["projection_refs"]
    assert "ObjectProjectionGraphNode" in payload["projection_node_refs"]
    assert payload["projection_node_key_refs"] == ("ObjectProjectionGraphNodeKey",)
    assert payload["object_graph_refs"] == (
        "ObjectConfigGraph",
        "ObjectProjectionGraph",
        "ObjectInstanceGraph",
    )
    assert payload["package_selectors"] == {
        "manifest_kind": "aware_toml",
        "package_kind": "ontology",
        "semantic_kind": "object_config_graph_package",
    }


def test_meta_projection_mutation_scope_derives_source_operations() -> None:
    payload = META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE.evidence_payload()

    assert payload["semantic_operation_type_refs"] == (
        META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES
    )
    assert (
        "aware_meta.object_config_graph.attribute.membership.update"
        in payload["semantic_operation_type_refs"]
    )
    assert (
        "aware_meta.object_config_graph.function.signature.update"
        in payload["semantic_operation_type_refs"]
    )
    assert payload["function_call_binding_refs"] == (
        META_OBJECT_CONFIG_GRAPH_FUNCTION_CALL_BINDING_REFS
    )
    assert (
        "aware_meta.object_config_graph.attribute.type.update_primitive"
        in payload["function_call_binding_refs"]
    )
    assert (
        payload["source_binding_refs"] == META_OBJECT_CONFIG_GRAPH_SOURCE_BINDING_REFS
    )
    assert (
        "aware_meta.object_config_graph.function.membership.constructor"
        in payload["source_binding_refs"]
    )
    assert (
        "aware.meta.function.signature.generated_materialization_intent.v0"
        in payload["generated_materialization_intent_refs"]
    )
    assert (
        "meta.provider_delta.ontology_mutation_proof" in payload["expected_proof_refs"]
    )
    assert "provider_delta_oig_commit_receipt" in payload["expected_receipt_refs"]


def test_meta_contract_metadata_reuses_projection_mutation_scope_payload() -> None:
    assert (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA[
            "supported_semantic_operation_types"
        ]
        == META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES
    )
    assert (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA[
            "semantic_operation_type_refs"
        ]
        == META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES
    )
    assert (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA[
            META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY
        ]
        == META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS
    )
    assert (
        META_MATERIALIZATION_DELTA_ADAPTER_METADATA[
            "semantic_projection_mutation_scope_keys"
        ]
        == META_SEMANTIC_SCOPE_KEYS
    )
    assert (
        META_MATERIALIZATION_DELTA_ADAPTER_METADATA[
            META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY
        ]
        == META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS
    )


def test_meta_semantic_scope_provider_resolves_aware_ontology_package() -> None:
    with _isolated_semantic_scope_registry():
        meta_semantic_scope.register_semantic_scope_providers()
        resolutions = SemanticScopeRegistry.resolve(
            _code_package(manifest_kind="aware_toml", package_kind="ontology"),
            workspace_root=Path("/workspace"),
            provider_keys=("aware_meta",),
            scope_keys=(META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY,),
        )

    assert len(resolutions) == 1
    [resolution] = resolutions
    assert resolution.provider_key == "aware_meta"
    assert (
        resolution.scope_key == META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY
    )
    assert (
        resolution.runtime_value is META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE
    )
    assert resolution.materialization_dependencies == ()
    assert resolution.payload["code_package"] == {
        "name": "demo-ontology",
        "manifest_kind": "aware_toml",
        "package_kind": "ontology",
        "fqn_prefix": "aware_demo",
        "root_relative_path": "modules/demo/structure/ontology",
        "manifest_relative_path": "modules/demo/structure/ontology/aware.toml",
    }
    assert resolution.payload["projection_name"] == "ObjectConfigGraphPackage"


def test_meta_semantic_scope_provider_ignores_non_meta_package_shapes() -> None:
    provider = meta_semantic_scope._PROVIDER  # noqa: SLF001

    assert (
        provider.resolve(
            _code_package(manifest_kind="aware_api_toml", package_kind="api"),
            workspace_root=Path("/workspace"),
        )
        == ()
    )
    assert (
        provider.resolve(
            _code_package(manifest_kind="aware_toml", package_kind="api"),
            workspace_root=Path("/workspace"),
        )
        == ()
    )


def _code_package(*, manifest_kind: str, package_kind: str) -> CodePackageInfo:
    package_root = Path("modules/demo/structure/ontology")
    return CodePackageInfo(
        name="demo-ontology",
        root_path=package_root,
        manifest_path=package_root / "aware.toml",
        language=CodeLanguage.aware,
        metadata={
            "fqn_prefix": "aware_demo",
            "manifest_kind": manifest_kind,
            "package_kind": package_kind,
        },
    )
