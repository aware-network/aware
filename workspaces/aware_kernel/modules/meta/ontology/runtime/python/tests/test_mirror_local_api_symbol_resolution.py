# @code-under-test: ../aware_meta/graph/config/builder.py

from pathlib import Path
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.manifest.spec import AwarePackageKind


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


def _namespaces(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }


def _find_enum_leaf(descriptor: AttributeTypeDescriptor) -> AttributeTypeDescriptor:
    stack = [descriptor]
    while stack:
        cur = stack.pop()
        if cur.kind == AttributeTypeDescriptorKind.enum:
            return cur
        for link in cur.child_links or []:
            if link.child is not None:
                stack.append(link.child)
    raise AssertionError("Expected an enum leaf in the descriptor tree")


ONTOLOGY_CODE = """
enum NetworkOperationMessageType {
    notification
}
""".strip()


API_MIRROR_CODE = """
mirror aware_network.network.NetworkOperationMessageType
""".strip()


API_MODEL_CODE = """
class NetworkOperation : inline_value {
    message_type network.NetworkOperationMessageType = notification
}
""".strip()


def test_api_build_allows_local_namespace_refs_to_mirrored_enums(tmp_path: Path) -> None:
    """
    API contract:
    - API `.aware` code may reference mirrored symbols via local namespace shorthand.
    - Mirrors must be applied early enough that member typing can resolve those symbols.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    ont_code = _build_code(tmp_path, "ont.aware", ONTOLOGY_CODE)
    ont_ns = _namespaces(
        fqn_prefix="aware_network",
        namespace="network",
        code_ids=[ont_code.id],
    )
    ont_res = build_object_config_graph_from_code(
        name="ont",
        description="ont",
        fqn_prefix="aware_network",
        file_codes=[("ont.aware", ont_code)],
        namespace_by_code_id=ont_ns,
        package_kind=AwarePackageKind.ontology,
    )

    mirror_code = _build_code(tmp_path, "mirror.aware", API_MIRROR_CODE)
    model_code = _build_code(tmp_path, "model.aware", API_MODEL_CODE)

    api_ns = {
        mirror_code.id: NamespacePath(
            package="aware_network_api", namespace="network"
        ),
        model_code.id: NamespacePath(
            package="aware_network_api", namespace="comms.models"
        ),
    }

    api_res = build_object_config_graph_from_code(
        name="api",
        description="api",
        fqn_prefix="aware_network_api",
        file_codes=[
            ("network/mirror.aware", mirror_code),
            ("comms/models/model.aware", model_code),
        ],
        namespace_by_code_id=api_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[ont_res.graph],
    )

    enum_mirror = next(
        m
        for m in api_res.graph.object_config_graph_mirrors
        if m.target_text == "aware_network.network.NetworkOperationMessageType"
    )
    assert enum_mirror.enum_config is not None
    assert enum_mirror.enum_config_id == enum_mirror.enum_config.id
    assert enum_mirror.class_config_id is None

    expected_enum_fqn = NamespacePath(
        package="aware_network_api", namespace="network"
    ).fqn("NetworkOperationMessageType")
    mirrored_enum = next(
        n.enum_config
        for n in api_res.graph.object_config_graph_nodes
        if n.enum_config is not None and n.enum_config.enum_fqn == expected_enum_fqn
    )
    assert mirrored_enum is not None

    op_class = next(
        n.class_config
        for n in api_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "NetworkOperation"
    )
    attr = next(
        link.attribute_config
        for link in op_class.class_config_attribute_configs
        if link.attribute_config is not None
        and link.attribute_config.name == "message_type"
    )
    enum_leaf = _find_enum_leaf(attr.type_descriptor)
    assert enum_leaf.enum_config_id == mirrored_enum.id
    assert enum_leaf.enum_config is not None
    assert enum_leaf.enum_config.id == mirrored_enum.id
