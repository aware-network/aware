# @code-under-test: ../aware_meta/graph/config/builder.py


from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Runtime
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.fqn_resolver import NamespacePath


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


DEFAULT_CODE = """
class User {
    posts Post[]
}

class Post {
    title String
}
""".strip()


def test_ocg_builder_smoke_relationship_attribute(tmp_path: Path) -> None:
    """
    Smoke test for kernel-meta canonical OCG build:
    - emits CLASS nodes
    - emits RELATIONSHIP nodes
    - each relationship has at least one attribute representation
    - canonical emission includes exactly one FORWARD+REFERENCE relationship attribute
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "smoke.aware",
        DEFAULT_CODE,
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="smoke",
        description="smoke",
        fqn_prefix="pkg",
        file_codes=[("smoke.aware", code)],
        namespace_by_code_id=ns,
    )
    graph = res.graph

    node_types = [n.type for n in graph.object_config_graph_nodes]
    assert ObjectConfigGraphNodeType.class_ in node_types
    assert ObjectConfigGraphNodeType.relationship in node_types

    rels = [
        n.class_config_relationship
        for n in graph.object_config_graph_nodes
        if n.class_config_relationship is not None
    ]
    assert rels, "Expected at least one ClassConfigRelationship"

    for r in rels:
        attrs = list(r.class_config_relationship_attributes)
        assert attrs, "Expected relationship attribute representations"
        canonical = [
            a
            for a in attrs
            if a.direction == ClassConfigRelationshipDirection.forward
            and a.role == ClassConfigRelationshipAttributeRole.reference
        ]
        assert (
            len(canonical) == 1
        ), "Canonical build should emit exactly one FORWARD+REFERENCE attribute per relationship"


def test_ocg_builder_inline_value_sets_class_value_mode(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "inline_value.aware",
        """
class Payload : inline_value {
    message String
}

class Entity {
    name String
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="inline_value",
        description="inline_value",
        fqn_prefix="pkg",
        file_codes=[("inline_value.aware", code)],
        namespace_by_code_id=ns,
    )

    payload_cc = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Payload"
    )
    assert payload_cc.value_mode == ClassValueMode.inline_value

    entity_cc = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Entity"
    )
    assert entity_cc.value_mode == ClassValueMode.graph_ref
