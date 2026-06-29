from __future__ import annotations

from pathlib import Path

from aware_content.builder import get_text
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from dart_grammar.renderer import DartRenderer
from dart_grammar.renderer_policy import DartRenderPolicy
from dart_grammar_test_support import class_attr_link, make_attribute, make_class, make_class_node


class _DartLayout(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return self.base_dir / f"{class_config.name}.dart"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return self.base_dir / f"{enum_config.name}.dart"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return self.base_dir / "functions.dart"

    def get_file_extension(self) -> str:
        return ".dart"


def _class_descriptor(target: ClassConfig) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )


def _list_descriptor(target: ClassConfig) -> AttributeTypeDescriptor:
    child = _class_descriptor(target)
    root = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.collection,
        collection_kind=AttributeCollectionType.list,
    )
    root.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=root.id,
            child=child,
            child_id=child.id,
            role=AttributeTypeDescriptorRole.element,
            position=0,
        )
    )
    return root


def _attr(
    owner: ClassConfig,
    name: str,
    descriptor: AttributeTypeDescriptor,
    *,
    is_required: bool = False,
) -> AttributeConfig:
    return make_attribute(
        name=name,
        owner_key=owner.class_fqn,
        is_public=True,
        is_required=is_required,
        is_virtual=False,
        is_unique=False,
        type_descriptor=descriptor,
    )


def test_ontology_dto_policy_keeps_internal_relationships_and_external_dto_imports(
    tmp_path: Path,
) -> None:
    layout = _DartLayout(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)
    renderer.set_policy(DartRenderPolicy.ontology_dto_default())

    parent = make_class(name="Conversation")
    internal_child = make_class(name="ConversationMessage")
    external_child = make_class(
        name="ContentChain",
        package="aware_content",
        domain="chain",
        schema="chain",
    )
    messages = _attr(parent, "conversation_messages", _list_descriptor(internal_child))
    content_chain = _attr(parent, "content_chain", _class_descriptor(external_child))
    parent.class_config_attribute_configs = [
        class_attr_link(parent, content_chain, position=0),
        class_attr_link(parent, messages, position=1),
    ]

    graph = ObjectConfigGraph(
        name="conversation",
        hash="test",
        fqn_prefix="aware_conversation",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(object_config_graph_id=parent.id, class_config=parent),
            make_class_node(object_config_graph_id=parent.id, class_config=internal_child),
        ],
    )
    renderer.bind_object_config_graph(graph)
    renderer.import_overrides = {
        str(external_child.id): "package:aware_content_ontology_dto/chain/content_chain_model.dart"
    }

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([parent], writer)

    dart_source = get_text(code.content_part_text)
    assert "package:aware_content_ontology_dto/chain/content_chain_model.dart" in dart_source
    assert "ContentChain? contentChain" in dart_source
    assert "@Default(const []) List<ConversationMessage> conversationMessages" in dart_source
    assert "List<ConversationMessage> conversationMessages = const []" in dart_source
    assert "aware_content_ontology/chain/content_chain" not in dart_source


def test_required_relationship_attribute_renders_non_nullable_dart_parameter(
    tmp_path: Path,
) -> None:
    layout = _DartLayout(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)
    renderer.set_policy(DartRenderPolicy.ontology_dto_default())

    request = make_class(name="ResolveStorageMediaRequest")
    media_ref = make_class(name="StorageMediaRef")
    media_ref_attr = _attr(
        request,
        "media_ref",
        _class_descriptor(media_ref),
        is_required=True,
    )
    request.class_config_attribute_configs = [
        class_attr_link(request, media_ref_attr, position=0),
    ]

    graph = ObjectConfigGraph(
        name="storage",
        hash="test",
        fqn_prefix="aware_storage_service_dto",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(object_config_graph_id=request.id, class_config=request),
            make_class_node(object_config_graph_id=request.id, class_config=media_ref),
        ],
    )
    renderer.bind_object_config_graph(graph)

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([request, media_ref], writer)

    dart_source = get_text(code.content_part_text)
    assert "required StorageMediaRef mediaRef" in dart_source
    assert "StorageMediaRef? mediaRef" not in dart_source


def test_ontology_dto_policy_drops_external_relationship_without_dto_import(
    tmp_path: Path,
) -> None:
    layout = _DartLayout(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)
    renderer.set_policy(DartRenderPolicy.ontology_dto_default())

    parent = make_class(name="Conversation")
    external_child = make_class(
        name="ContentChain",
        package="aware_content",
        domain="chain",
        schema="chain",
    )
    content_chain = _attr(parent, "content_chain", _class_descriptor(external_child))
    parent.class_config_attribute_configs = [
        class_attr_link(parent, content_chain, position=0),
    ]

    graph = ObjectConfigGraph(
        name="conversation",
        hash="test",
        fqn_prefix="aware_conversation",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(object_config_graph_id=parent.id, class_config=parent),
        ],
    )
    renderer.bind_object_config_graph(graph)

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([parent], writer)

    dart_source = get_text(code.content_part_text)
    assert "contentChain" not in dart_source
    assert "ContentChain" not in dart_source
