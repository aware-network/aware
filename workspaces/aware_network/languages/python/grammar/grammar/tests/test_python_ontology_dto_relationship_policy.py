from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

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
from aware_utils.string_transform import to_snake_case

from python_grammar.renderer import PythonRenderer
from python_grammar.renderer_policy import PythonRenderPolicy
from python_grammar_test_support import class_attr_link, make_attribute, make_class, make_class_node


@dataclass(frozen=True)
class _PythonLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = None
    parent: ObjectConfigGraphRenderLayoutStrategy | None = None

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("conversation") / f"{to_snake_case(class_config.name)}.py"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return Path("conversation") / f"{to_snake_case(enum_config.name)}.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return Path("conversation") / "functions.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        return ".".join(part for part in parts if part)


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


def _attr(owner: ClassConfig, name: str, descriptor: AttributeTypeDescriptor) -> AttributeConfig:
    return make_attribute(
        name=name,
        owner_key=owner.class_fqn,
        is_public=True,
        is_required=False,
        is_virtual=False,
        is_unique=False,
        type_descriptor=descriptor,
    )


def _render(
    renderer: PythonRenderer,
    *,
    meta_objects: list[object],
    class_map: dict[UUID, ClassConfig],
) -> str:
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file(
        meta_objects,
        writer,
        schema="conversation",
        class_to_class_config_map=class_map,
    )
    return writer.code.content_part_text.inline_text or ""


def test_ontology_dto_policy_keeps_internal_relationships_and_external_dto_imports(
    tmp_path: Path,
) -> None:
    layout = _PythonLayout(base_dir=tmp_path)
    renderer = PythonRenderer(
        layout_strategy=layout,
        policy=PythonRenderPolicy.ontology_dto_default(),
    )

    parent = make_class(name="Conversation", is_base=True)
    internal_child = make_class(name="ConversationMessage", is_base=True)
    external_child = make_class(
        name="ContentChain",
        package="aware_content",
        namespace="chain",
        is_base=True,
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
        str(external_child.id): "aware_content_ontology_dto.chain.content_chain"
    }

    source = _render(
        renderer,
        meta_objects=[parent],
        class_map={
            parent.id: parent,
            internal_child.id: internal_child,
            external_child.id: external_child,
        },
    )

    assert "conversation_messages: list[ConversationMessage]" in source
    assert "conversation_messages: list[ConversationMessage] = Field(default_factory=list)" in source
    assert "from aware_content_ontology_dto.chain.content_chain import ContentChain" in source
    assert "content_chain: ContentChain | None = Field(default=None)" in source
    assert "exclude=True" not in source
    assert "aware_content_ontology.chain.content_chain" not in source


def test_ontology_dto_policy_drops_external_relationship_without_dto_import(
    tmp_path: Path,
) -> None:
    layout = _PythonLayout(base_dir=tmp_path)
    renderer = PythonRenderer(
        layout_strategy=layout,
        policy=PythonRenderPolicy.ontology_dto_default(),
    )

    parent = make_class(name="Conversation", is_base=True)
    external_child = make_class(
        name="ContentChain",
        package="aware_content",
        namespace="chain",
        is_base=True,
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

    source = _render(
        renderer,
        meta_objects=[parent],
        class_map={
            parent.id: parent,
            external_child.id: external_child,
        },
    )

    assert "content_chain" not in source
    assert "ContentChain" not in source
