# @code-under-test: ../aware_meta/graph/config/builder.py

from pathlib import Path
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code


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


CODE = """
class User {
    fn getFullName() -> String {
        \"\"\"Return the user's full name.\"\"\"
    }

    fn buildUser construct(email String?) -> User {
        \"\"\"Constructor returning the created User.\"\"\"
    }
}
""".strip()


CODE_WITH_IDENTITY_KEY = """
class User {
    fn buildUser construct(email String key, display_name String?) -> User {
        \"\"\"Constructor returning the created User.\"\"\"
    }
}
""".strip()


def test_meta_builder_emits_output_attribute_for_single_return(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "single_return.aware", CODE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="single_return",
        description="single_return",
        fqn_prefix="pkg",
        file_codes=[("single_return.aware", code)],
        namespace_by_code_id=ns,
    )
    graph = res.graph

    user_cc = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "User"
    )

    get_full_name = next(
        link.function_config
        for link in user_cc.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == "getFullName"
    )
    outs = [
        edge.attribute_config
        for edge in get_full_name.function_config_attribute_configs
        if edge.type == FunctionAttributeType.output
        and edge.attribute_config is not None
    ]
    assert len(outs) == 1
    assert outs[0].name == "value"

    type_info = resolve_type_info(outs[0])
    assert type_info.kind == AttributeTypeDescriptorKind.primitive
    assert type_info.primitive_config is not None
    prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
    assert prim.base_type == CodePrimitiveBaseType.string

    build_user = next(
        link.function_config
        for link in user_cc.class_config_function_configs
        if link.function_config is not None and link.function_config.name == "buildUser"
    )
    outs = [
        edge.attribute_config
        for edge in build_user.function_config_attribute_configs
        if edge.type == FunctionAttributeType.output
        and edge.attribute_config is not None
    ]
    assert len(outs) == 1
    assert outs[0].name == "value"

    type_info = resolve_type_info(outs[0])
    assert type_info.kind == AttributeTypeDescriptorKind.class_
    assert type_info.class_config is not None
    assert type_info.class_config.name == "User"


def test_meta_builder_marks_function_input_identity_keys(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "identity_key.aware", CODE_WITH_IDENTITY_KEY)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="identity_key",
        description="identity_key",
        fqn_prefix="pkg",
        file_codes=[("identity_key.aware", code)],
        namespace_by_code_id=ns,
    )
    graph = res.graph

    user_cc = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "User"
    )
    build_user = next(
        link.function_config
        for link in user_cc.class_config_function_configs
        if link.function_config is not None and link.function_config.name == "buildUser"
    )

    input_edges = sorted(
        (
            edge
            for edge in build_user.function_config_attribute_configs
            if edge.type == FunctionAttributeType.input
        ),
        key=lambda edge: edge.position,
    )
    assert len(input_edges) == 2
    assert input_edges[0].attribute_config is not None
    assert input_edges[0].attribute_config.name == "email"
    assert input_edges[0].is_identity_key is True
    assert input_edges[1].attribute_config is not None
    assert input_edges[1].attribute_config.name == "display_name"
    assert input_edges[1].is_identity_key is False
