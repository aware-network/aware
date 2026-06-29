from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.relationship_analysis import analyze_relationships
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)


CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)


def _build_code(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def _strip_relationship_endpoint_objects(graph, *, relationship_key: str) -> None:
    """Simulate persisted graphs that keep relationship ids but not object refs."""

    def _strip_descriptor_class_config(descriptor) -> None:
        if descriptor is None:
            return
        if hasattr(descriptor, "class_config"):
            descriptor.class_config = None
        for child_link in getattr(descriptor, "child_links", ()) or ():
            _strip_descriptor_class_config(child_link.child)

    for node in graph.object_config_graph_nodes:
        cls = node.class_config
        if cls is None:
            continue
        for relationship in cls.class_config_relationships:
            if relationship.relationship_key == relationship_key:
                relationship.target_class_config = None
        for attribute_link in cls.class_config_attribute_configs:
            attribute = attribute_link.attribute_config
            if attribute is not None and attribute.name == relationship_key:
                _strip_descriptor_class_config(attribute.type_descriptor)

    for ocg_relationship in graph.object_config_graph_relationships:
        ocg_relationship.target_object_config_graph = None
        for relationship in ocg_relationship.class_config_relationships:
            if relationship.relationship_key == relationship_key:
                relationship.target_class_config = None
            for relationship_attribute in relationship.class_config_relationship_attributes:
                attribute = relationship_attribute.attribute_config
                if attribute is not None and attribute.name == relationship_key:
                    _strip_descriptor_class_config(attribute.type_descriptor)


def test_relationship_analysis_ignores_unreachable_external_constructs(
    tmp_path: Path,
) -> None:
    """
    Regression for module compiles that load multiple dependency graphs.

    Service compiles should analyze only relationships reachable from the root graph being
    transformed. A direct dependency graph may contain its own internal construct propagation
    rails that target a second dependency graph; those unrelated external invocations must not
    be treated as required construct targets for the root graph.
    """

    meta_code = _build_code(
        tmp_path,
        "meta_value.aware",
        """
class InlineValue {
    call_key UUID key

    fn build construct(call_key UUID key) -> InlineValue {
    }
}
""".strip(),
    )
    meta_ns, meta_domains = _ns(
        fqn_prefix="aware_meta",
        namespace="class",
        code_ids=[meta_code.id],
    )
    meta_graph = build_object_config_graph_from_code(
        name="meta_value",
        description="meta_value",
        fqn_prefix="aware_meta",
        file_codes=[("meta_value.aware", meta_code)],
        namespace_by_code_id=meta_ns,
    ).graph

    api_code = _build_code(
        tmp_path,
        "api_call.aware",
        """
class ApiCall {
    request_model aware_meta.class.InlineValue unique

    fn create construct(call_key UUID) -> ApiCall {
        let created = construct request_model.build(call_key = call_key)
    }
}
""".strip(),
    )
    api_ns, api_domains = _ns(
        fqn_prefix="aware_api",
        namespace="api",
        code_ids=[api_code.id],
    )
    api_build = build_object_config_graph_from_code(
        name="api_call",
        description="api_call",
        fqn_prefix="aware_api",
        file_codes=[("api_call.aware", api_code)],
        namespace_by_code_id=api_ns,
        external_graphs=[meta_graph],
    )
    api_graph = api_build.graph
    api_cross_rels = api_build.cross_relationships_by_target_ocg.get(meta_graph.id)
    assert api_cross_rels is not None and len(api_cross_rels) == 1
    api_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=api_graph.id,
            target_object_config_graph_id=meta_graph.id,
            class_config_relationships=[api_cross_rels[0]],
        )
    )

    service_code = _build_code(
        tmp_path,
        "service_binding.aware",
        """
class ServiceBinding {
    api_call aware_api.api.ApiCall unique
}
""".strip(),
    )
    service_ns, service_domains = _ns(
        fqn_prefix="aware_service",
        namespace="service",
        code_ids=[service_code.id],
    )
    service_build = build_object_config_graph_from_code(
        name="service_binding",
        description="service_binding",
        fqn_prefix="aware_service",
        file_codes=[("service_binding.aware", service_code)],
        namespace_by_code_id=service_ns,
        external_graphs=[api_graph, meta_graph],
    )
    service_graph = service_build.graph
    service_cross_rels = service_build.cross_relationships_by_target_ocg.get(
        api_graph.id
    )
    assert service_cross_rels is not None and len(service_cross_rels) == 1
    service_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=service_graph.id,
            target_object_config_graph_id=api_graph.id,
            class_config_relationships=[service_cross_rels[0]],
        )
    )
    service_graph_loaded = service_graph.model_validate_json(
        service_graph.model_dump_json(exclude_none=True, by_alias=True)
    )

    analyses = analyze_relationships(
        service_graph_loaded,
        namespace_by_code_id=service_ns,
        external_graphs_by_id={api_graph.id: api_graph, meta_graph.id: meta_graph},
    )

    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }
    assert ("ServiceBinding", "api_call", "ApiCall") in by_sig


def test_runtime_transform_resolves_cross_ocg_construct_from_analysis(
    tmp_path: Path,
) -> None:
    meta_code = _build_code(
        tmp_path,
        "meta_value.aware",
        """
class InlineValue {
    call_key UUID key

    fn build construct(call_key UUID key) -> InlineValue {
    }
}
""".strip(),
    )
    meta_ns, meta_domains = _ns(
        fqn_prefix="aware_meta",
        namespace="class",
        code_ids=[meta_code.id],
    )
    meta_graph = build_object_config_graph_from_code(
        name="meta_value",
        description="meta_value",
        fqn_prefix="aware_meta",
        file_codes=[("meta_value.aware", meta_code)],
        namespace_by_code_id=meta_ns,
    ).graph

    api_code = _build_code(
        tmp_path,
        "api_call.aware",
        """
class ApiCall {
    request_model aware_meta.class.InlineValue unique

    fn create construct(call_key UUID key) -> ApiCall {
        let created = construct request_model.build(call_key = call_key)
    }
}
""".strip(),
    )
    api_ns, api_domains = _ns(
        fqn_prefix="aware_api",
        namespace="api",
        code_ids=[api_code.id],
    )
    api_build = build_object_config_graph_from_code(
        name="api_call",
        description="api_call",
        fqn_prefix="aware_api",
        file_codes=[("api_call.aware", api_code)],
        namespace_by_code_id=api_ns,
        external_graphs=[meta_graph],
    )
    api_graph = api_build.graph
    api_cross_rels = api_build.cross_relationships_by_target_ocg.get(meta_graph.id)
    assert api_cross_rels
    api_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=api_graph.id,
            target_object_config_graph_id=meta_graph.id,
            class_config_relationships=[api_cross_rels[0]],
        )
    )
    _strip_relationship_endpoint_objects(api_graph, relationship_key="request_model")

    runtime_graph = AwareToRuntimeTransformer(
        namespace_by_code_id=api_ns,
        external_graphs_by_id={meta_graph.id: meta_graph},
    ).transform(api_graph)

    api_call = next(
        node.class_config
        for node in runtime_graph.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "ApiCall"
    )
    relationship_names = {
        rel.relationship_key for rel in api_call.class_config_relationships
    }
    assert "request_model" in relationship_names
    request_model = next(
        rel
        for rel in api_call.class_config_relationships
        if rel.relationship_key == "request_model"
    )
    assert request_model.target_class_config is not None
    assert request_model.target_class_config.name == "InlineValue"
    request_model_attr = next(
        link.attribute_config
        for link in api_call.class_config_attribute_configs
        if link.attribute_config.name == "request_model"
    )
    assert request_model_attr.type_descriptor.class_config is not None
    assert request_model_attr.type_descriptor.class_config.name == "InlineValue"
