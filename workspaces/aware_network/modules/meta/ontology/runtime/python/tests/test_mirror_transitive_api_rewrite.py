# @code-under-test: ../aware_meta/graph/config/mirror/apply.py

from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
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


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


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


def _find_class_leaf(descriptor: AttributeTypeDescriptor) -> AttributeTypeDescriptor:
    stack = [descriptor]
    while stack:
        cur = stack.pop()
        if cur.kind == AttributeTypeDescriptorKind.class_:
            return cur
        for link in cur.child_links or []:
            if link.child is not None:
                stack.append(link.child)
    raise AssertionError("Expected a class leaf in the descriptor tree")


CODE_ONTOLOGY = """
enum CodeLanguage {
    python
}
""".strip()

CODE_ONTOLOGY_CLASS = """
class CodeThing : inline_value {
    name String
}
""".strip()


STRUCTURE_ONTOLOGY = """
class RepositoryDeltaCreate : inline_value {
    language code.code.CodeLanguage?
}
""".strip()

STRUCTURE_ONTOLOGY_CLASS_REF = """
class RepositoryDeltaCreate : inline_value {
    thing code.code.CodeThing?
    things code.code.CodeThing[]
    map_ref code.code.CodeThing
    tuple_ref code.code.CodeThing
}
""".strip()


CODE_API = """
mirror code.code.CodeLanguage
""".strip()

CODE_API_CLASS = """
mirror code.code.CodeThing
""".strip()


STRUCTURE_API = """
mirror struct.repository.RepositoryDeltaCreate
""".strip()


def test_mirror_rewrites_transitive_ontology_enum_to_api_owner(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_ont_code = _build_code(tmp_path, "code_ontology.aware", CODE_ONTOLOGY)
    code_ont_ns, code_ont_domains = _ns(
        fqn_prefix="code",
        namespace="code",
        code_ids=[code_ont_code.id],
    )
    code_ont_res = build_object_config_graph_from_code(
        name="code",
        description="code",
        fqn_prefix="code",
        file_codes=[("code_ontology.aware", code_ont_code)],
        namespace_by_code_id=code_ont_ns,
        package_kind=AwarePackageKind.ontology,
    )

    code_api_code = _build_code(tmp_path, "code_api.aware", CODE_API)
    code_api_ns, code_api_domains = _ns(
        fqn_prefix="code_api",
        namespace="code",
        code_ids=[code_api_code.id],
    )
    code_api_res = build_object_config_graph_from_code(
        name="code_api",
        description="code_api",
        fqn_prefix="code_api",
        file_codes=[("code_api.aware", code_api_code)],
        namespace_by_code_id=code_api_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[code_ont_res.graph],
    )

    struct_ont_code = _build_code(
        tmp_path, "structure_ontology.aware", STRUCTURE_ONTOLOGY
    )
    struct_ont_ns, struct_ont_domains = _ns(
        fqn_prefix="struct",
        namespace="repository",
        code_ids=[struct_ont_code.id],
    )
    struct_ont_res = build_object_config_graph_from_code(
        name="struct",
        description="struct",
        fqn_prefix="struct",
        file_codes=[("structure_ontology.aware", struct_ont_code)],
        namespace_by_code_id=struct_ont_ns,
        package_kind=AwarePackageKind.ontology,
        external_graphs=[code_ont_res.graph],
    )

    struct_api_code = _build_code(tmp_path, "structure_api.aware", STRUCTURE_API)
    struct_api_ns, struct_api_domains = _ns(
        fqn_prefix="struct_api",
        namespace="repository",
        code_ids=[struct_api_code.id],
    )
    struct_api_res = build_object_config_graph_from_code(
        name="struct_api",
        description="struct_api",
        fqn_prefix="struct_api",
        file_codes=[("structure_api.aware", struct_api_code)],
        namespace_by_code_id=struct_api_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[struct_ont_res.graph, code_api_res.graph],
    )

    code_ont_enum = next(
        n.enum_config
        for n in code_ont_res.graph.object_config_graph_nodes
        if n.enum_config is not None and n.enum_config.name == "CodeLanguage"
    )
    code_api_enum = next(
        n.enum_config
        for n in code_api_res.graph.object_config_graph_nodes
        if n.enum_config is not None and n.enum_config.name == "CodeLanguage"
    )
    mirrored_class = next(
        n.class_config
        for n in struct_api_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "RepositoryDeltaCreate"
    )
    language_attr = next(
        link.attribute_config
        for link in mirrored_class.class_config_attribute_configs
        if link.attribute_config is not None
        and link.attribute_config.name == "language"
    )
    enum_leaf = _find_enum_leaf(language_attr.type_descriptor)

    assert enum_leaf.enum_config_id == code_api_enum.id
    assert enum_leaf.enum_config is not None
    assert enum_leaf.enum_config.id == code_api_enum.id
    assert enum_leaf.enum_config_id != code_ont_enum.id

    assert not any(
        n.enum_config is not None and n.enum_config.name == "CodeLanguage"
        for n in struct_api_res.graph.object_config_graph_nodes
    ), "struct_api should reference code_api CodeLanguage, not copy it"


def test_mirror_errors_when_missing_api_owner_dependency(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_ont_code = _build_code(tmp_path, "code_ontology.aware", CODE_ONTOLOGY)
    code_ont_ns, code_ont_domains = _ns(
        fqn_prefix="code",
        namespace="code",
        code_ids=[code_ont_code.id],
    )
    code_ont_res = build_object_config_graph_from_code(
        name="code",
        description="code",
        fqn_prefix="code",
        file_codes=[("code_ontology.aware", code_ont_code)],
        namespace_by_code_id=code_ont_ns,
        package_kind=AwarePackageKind.ontology,
    )

    struct_ont_code = _build_code(
        tmp_path, "structure_ontology.aware", STRUCTURE_ONTOLOGY
    )
    struct_ont_ns, struct_ont_domains = _ns(
        fqn_prefix="struct",
        namespace="repository",
        code_ids=[struct_ont_code.id],
    )
    struct_ont_res = build_object_config_graph_from_code(
        name="struct",
        description="struct",
        fqn_prefix="struct",
        file_codes=[("structure_ontology.aware", struct_ont_code)],
        namespace_by_code_id=struct_ont_ns,
        package_kind=AwarePackageKind.ontology,
        external_graphs=[code_ont_res.graph],
    )

    struct_api_code = _build_code(tmp_path, "structure_api.aware", STRUCTURE_API)
    struct_api_ns, struct_api_domains = _ns(
        fqn_prefix="struct_api",
        namespace="repository",
        code_ids=[struct_api_code.id],
    )

    with pytest.raises(
        ValueError, match="unresolved enum type reference|leaked a source ontology enum"
    ):
        build_object_config_graph_from_code(
            name="struct_api",
            description="struct_api",
            fqn_prefix="struct_api",
            file_codes=[("structure_api.aware", struct_api_code)],
            namespace_by_code_id=struct_api_ns,
            package_kind=AwarePackageKind.api,
            external_graphs=[struct_ont_res.graph],
        )


def test_mirror_rewrites_transitive_ontology_class_to_api_owner_in_nested_descriptors(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_ont_code = _build_code(tmp_path, "code_ontology.aware", CODE_ONTOLOGY_CLASS)
    code_ont_ns, code_ont_domains = _ns(
        fqn_prefix="code",
        namespace="code",
        code_ids=[code_ont_code.id],
    )
    code_ont_res = build_object_config_graph_from_code(
        name="code",
        description="code",
        fqn_prefix="code",
        file_codes=[("code_ontology.aware", code_ont_code)],
        namespace_by_code_id=code_ont_ns,
        package_kind=AwarePackageKind.ontology,
    )

    code_api_code = _build_code(tmp_path, "code_api.aware", CODE_API_CLASS)
    code_api_ns, code_api_domains = _ns(
        fqn_prefix="code_api",
        namespace="code",
        code_ids=[code_api_code.id],
    )
    code_api_res = build_object_config_graph_from_code(
        name="code_api",
        description="code_api",
        fqn_prefix="code_api",
        file_codes=[("code_api.aware", code_api_code)],
        namespace_by_code_id=code_api_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[code_ont_res.graph],
    )

    struct_ont_code = _build_code(
        tmp_path, "structure_ontology.aware", STRUCTURE_ONTOLOGY_CLASS_REF
    )
    struct_ont_ns, struct_ont_domains = _ns(
        fqn_prefix="struct",
        namespace="repository",
        code_ids=[struct_ont_code.id],
    )
    struct_ont_res = build_object_config_graph_from_code(
        name="struct",
        description="struct",
        fqn_prefix="struct",
        file_codes=[("structure_ontology.aware", struct_ont_code)],
        namespace_by_code_id=struct_ont_ns,
        package_kind=AwarePackageKind.ontology,
        external_graphs=[code_ont_res.graph],
    )

    # Mutate two attributes to exercise nested descriptor rewrites for mapping + tuple kinds.
    #
    # Aware source type syntax does not currently expose mapping/tuple types on attributes, but the
    # runtime descriptor tree supports them and mirror rewrite must be complete.
    from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
    from aware_code.primitive_codec_base import build_code_primitive_type
    from aware_meta.primitive.config.builder import build_primitive_config
    from aware_meta.attribute.config.type_descriptor_builder import (
        ensure_stable_descriptor_tree_ids,
    )
    from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
        AttributeTypeDescriptorKind,
        AttributeTypeDescriptorRole,
    )
    from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
        AttributeTypeDescriptorLink,
    )

    code_ont_thing = next(
        n.class_config
        for n in code_ont_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "CodeThing"
    )
    struct_ont_repo = next(
        n.class_config
        for n in struct_ont_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "RepositoryDeltaCreate"
    )

    map_attr = next(
        link.attribute_config
        for link in struct_ont_repo.class_config_attribute_configs
        if link.attribute_config is not None and link.attribute_config.name == "map_ref"
    )
    tuple_attr = next(
        link.attribute_config
        for link in struct_ont_repo.class_config_attribute_configs
        if link.attribute_config is not None
        and link.attribute_config.name == "tuple_ref"
    )

    key_prim = build_primitive_config(
        build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    )
    key_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive, primitive_config=key_prim
    )
    val_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config_id=code_ont_thing.id,
        class_config=code_ont_thing,
    )
    mapping_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.mapping)
    mapping_desc.child_links = [
        AttributeTypeDescriptorLink(
            role=AttributeTypeDescriptorRole.key,
            position=0,
            attribute_type_descriptor_id=mapping_desc.id,
            child=key_desc,
        ),
        AttributeTypeDescriptorLink(
            role=AttributeTypeDescriptorRole.value_,
            position=0,
            attribute_type_descriptor_id=mapping_desc.id,
            child=val_desc,
        ),
    ]
    mapping_desc = ensure_stable_descriptor_tree_ids(mapping_desc)
    map_attr.type_descriptor = mapping_desc
    map_attr.type_descriptor_id = mapping_desc.id

    prim_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive, primitive_config=key_prim
    )
    tuple_member = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config_id=code_ont_thing.id,
        class_config=code_ont_thing,
    )
    tuple_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.tuple)
    tuple_desc.child_links = [
        AttributeTypeDescriptorLink(
            role=AttributeTypeDescriptorRole.member,
            position=1,
            attribute_type_descriptor_id=tuple_desc.id,
            child=prim_desc,
        ),
        AttributeTypeDescriptorLink(
            role=AttributeTypeDescriptorRole.member,
            position=2,
            attribute_type_descriptor_id=tuple_desc.id,
            child=tuple_member,
        ),
    ]
    tuple_desc = ensure_stable_descriptor_tree_ids(tuple_desc)
    tuple_attr.type_descriptor = tuple_desc
    tuple_attr.type_descriptor_id = tuple_desc.id

    struct_api_code = _build_code(tmp_path, "structure_api.aware", STRUCTURE_API)
    struct_api_ns, struct_api_domains = _ns(
        fqn_prefix="struct_api",
        namespace="repository",
        code_ids=[struct_api_code.id],
    )
    struct_api_res = build_object_config_graph_from_code(
        name="struct_api",
        description="struct_api",
        fqn_prefix="struct_api",
        file_codes=[("structure_api.aware", struct_api_code)],
        namespace_by_code_id=struct_api_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[struct_ont_res.graph, code_api_res.graph],
    )

    code_ont_cls = next(
        n.class_config
        for n in code_ont_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "CodeThing"
    )
    code_api_cls = next(
        n.class_config
        for n in code_api_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "CodeThing"
    )
    mirrored_class = next(
        n.class_config
        for n in struct_api_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "RepositoryDeltaCreate"
    )

    def _get_attr(name: str):
        return next(
            link.attribute_config
            for link in mirrored_class.class_config_attribute_configs
            if link.attribute_config is not None and link.attribute_config.name == name
        )

    # Optional -> UNION
    thing_attr = _get_attr("thing")
    class_leaf = _find_class_leaf(thing_attr.type_descriptor)
    assert class_leaf.class_config_id == code_api_cls.id
    assert class_leaf.class_config_id != code_ont_cls.id

    # Collection -> COLLECTION
    things_attr = _get_attr("things")
    class_leaf = _find_class_leaf(things_attr.type_descriptor)
    assert class_leaf.class_config_id == code_api_cls.id

    # Mapping -> MAPPING
    map_attr2 = _get_attr("map_ref")
    class_leaf = _find_class_leaf(map_attr2.type_descriptor)
    assert class_leaf.class_config_id == code_api_cls.id

    # Tuple -> TUPLE
    tuple_attr2 = _get_attr("tuple_ref")
    class_leaf = _find_class_leaf(tuple_attr2.type_descriptor)
    assert class_leaf.class_config_id == code_api_cls.id

    assert not any(
        n.class_config is not None and n.class_config.name == "CodeThing"
        for n in struct_api_res.graph.object_config_graph_nodes
    ), "struct_api should reference code_api CodeThing, not copy it"


def test_mirror_errors_when_api_owner_is_ambiguous_for_enum(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_ont_code = _build_code(tmp_path, "code_ontology.aware", CODE_ONTOLOGY)
    code_ont_ns, code_ont_domains = _ns(
        fqn_prefix="code",
        namespace="code",
        code_ids=[code_ont_code.id],
    )
    code_ont_res = build_object_config_graph_from_code(
        name="code",
        description="code",
        fqn_prefix="code",
        file_codes=[("code_ontology.aware", code_ont_code)],
        namespace_by_code_id=code_ont_ns,
        package_kind=AwarePackageKind.ontology,
    )

    code_api1_code = _build_code(tmp_path, "code_api1.aware", CODE_API)
    code_api1_ns, code_api1_domains = _ns(
        fqn_prefix="code_api1",
        namespace="code",
        code_ids=[code_api1_code.id],
    )
    code_api1_res = build_object_config_graph_from_code(
        name="code_api1",
        description="code_api1",
        fqn_prefix="code_api1",
        file_codes=[("code_api1.aware", code_api1_code)],
        namespace_by_code_id=code_api1_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[code_ont_res.graph],
    )

    code_api2_code = _build_code(tmp_path, "code_api2.aware", CODE_API)
    code_api2_ns, code_api2_domains = _ns(
        fqn_prefix="code_api2",
        namespace="code",
        code_ids=[code_api2_code.id],
    )
    code_api2_res = build_object_config_graph_from_code(
        name="code_api2",
        description="code_api2",
        fqn_prefix="code_api2",
        file_codes=[("code_api2.aware", code_api2_code)],
        namespace_by_code_id=code_api2_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[code_ont_res.graph],
    )

    struct_ont_code = _build_code(
        tmp_path, "structure_ontology.aware", STRUCTURE_ONTOLOGY
    )
    struct_ont_ns, struct_ont_domains = _ns(
        fqn_prefix="struct",
        namespace="repository",
        code_ids=[struct_ont_code.id],
    )
    struct_ont_res = build_object_config_graph_from_code(
        name="struct",
        description="struct",
        fqn_prefix="struct",
        file_codes=[("structure_ontology.aware", struct_ont_code)],
        namespace_by_code_id=struct_ont_ns,
        package_kind=AwarePackageKind.ontology,
        external_graphs=[code_ont_res.graph],
    )

    struct_api_code = _build_code(tmp_path, "structure_api.aware", STRUCTURE_API)
    struct_api_ns, struct_api_domains = _ns(
        fqn_prefix="struct_api",
        namespace="repository",
        code_ids=[struct_api_code.id],
    )

    with pytest.raises(
        ValueError, match=r"Ambiguous API mirror ownership for enum_config_id"
    ):
        build_object_config_graph_from_code(
            name="struct_api",
            description="struct_api",
            fqn_prefix="struct_api",
            file_codes=[("structure_api.aware", struct_api_code)],
            namespace_by_code_id=struct_api_ns,
            package_kind=AwarePackageKind.api,
            external_graphs=[
                struct_ont_res.graph,
                code_api1_res.graph,
                code_api2_res.graph,
            ],
        )


def test_mirror_errors_when_api_owner_is_ambiguous_for_class(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_ont_code = _build_code(tmp_path, "code_ontology.aware", CODE_ONTOLOGY_CLASS)
    code_ont_ns, code_ont_domains = _ns(
        fqn_prefix="code",
        namespace="code",
        code_ids=[code_ont_code.id],
    )
    code_ont_res = build_object_config_graph_from_code(
        name="code",
        description="code",
        fqn_prefix="code",
        file_codes=[("code_ontology.aware", code_ont_code)],
        namespace_by_code_id=code_ont_ns,
        package_kind=AwarePackageKind.ontology,
    )

    code_api1_code = _build_code(tmp_path, "code_api1.aware", CODE_API_CLASS)
    code_api1_ns, code_api1_domains = _ns(
        fqn_prefix="code_api1",
        namespace="code",
        code_ids=[code_api1_code.id],
    )
    code_api1_res = build_object_config_graph_from_code(
        name="code_api1",
        description="code_api1",
        fqn_prefix="code_api1",
        file_codes=[("code_api1.aware", code_api1_code)],
        namespace_by_code_id=code_api1_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[code_ont_res.graph],
    )

    code_api2_code = _build_code(tmp_path, "code_api2.aware", CODE_API_CLASS)
    code_api2_ns, code_api2_domains = _ns(
        fqn_prefix="code_api2",
        namespace="code",
        code_ids=[code_api2_code.id],
    )
    code_api2_res = build_object_config_graph_from_code(
        name="code_api2",
        description="code_api2",
        fqn_prefix="code_api2",
        file_codes=[("code_api2.aware", code_api2_code)],
        namespace_by_code_id=code_api2_ns,
        package_kind=AwarePackageKind.api,
        external_graphs=[code_ont_res.graph],
    )

    struct_ont_code = _build_code(
        tmp_path, "structure_ontology.aware", STRUCTURE_ONTOLOGY_CLASS_REF
    )
    struct_ont_ns, struct_ont_domains = _ns(
        fqn_prefix="struct",
        namespace="repository",
        code_ids=[struct_ont_code.id],
    )
    struct_ont_res = build_object_config_graph_from_code(
        name="struct",
        description="struct",
        fqn_prefix="struct",
        file_codes=[("structure_ontology.aware", struct_ont_code)],
        namespace_by_code_id=struct_ont_ns,
        package_kind=AwarePackageKind.ontology,
        external_graphs=[code_ont_res.graph],
    )

    struct_api_code = _build_code(tmp_path, "structure_api.aware", STRUCTURE_API)
    struct_api_ns, struct_api_domains = _ns(
        fqn_prefix="struct_api",
        namespace="repository",
        code_ids=[struct_api_code.id],
    )

    with pytest.raises(
        ValueError, match=r"Ambiguous API mirror ownership for class_config_id"
    ):
        build_object_config_graph_from_code(
            name="struct_api",
            description="struct_api",
            fqn_prefix="struct_api",
            file_codes=[("structure_api.aware", struct_api_code)],
            namespace_by_code_id=struct_api_ns,
            package_kind=AwarePackageKind.api,
            external_graphs=[
                struct_ont_res.graph,
                code_api1_res.graph,
                code_api2_res.graph,
            ],
        )
