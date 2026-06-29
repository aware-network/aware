from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import ClassConfigRelationshipAttribute
from aware_meta_ontology.class_.class_config_relationship_association import (
    ClassConfigRelationshipAssociation,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)

from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType, FunctionKind

from aware_meta_ontology.attribute.attribute_config_overlay import AttributeConfigOverlay
from aware_meta_ontology.graph.config.object_config_graph_overlay import ObjectConfigGraphOverlay

from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from python_grammar.renderer import PythonRenderer

from aware_utils.string_transform import to_snake_case
from python_grammar import renderer as renderer_module
from python_grammar_test_support import (
    class_attr_link,
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_function,
    make_relationship,
    make_relationship_association,
    make_relationship_attribute,
)


@dataclass(frozen=True)
class _TestLayout(ObjectConfigGraphRenderLayoutStrategy):
    """
    Minimal layout strategy for unit tests.

    Avoids requiring code_section_* bindings; mapping is purely name-based.
    """

    base_dir: Path
    import_root: str | None = None
    parent: ObjectConfigGraphRenderLayoutStrategy | None = None

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        # For these renderer unit tests we treat `emit_file` as "single output file" and therefore
        # map *all* classes to the same file. This avoids coupling test determinism to file bucketing.
        return Path("default") / "models.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        # Mirrors PythonLayoutStrategy.get_module_import_path behavior, but name-based.
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        module_parts = [p for p in parts if p]
        if self.import_root:
            module_parts.insert(0, self.import_root)
        return ".".join(module_parts).strip(".")


def _class_descriptor(target: ClassConfig) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )


def _list_descriptor(target: ClassConfig) -> AttributeTypeDescriptor:
    child = _class_descriptor(target)
    root = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.collection, collection_kind=AttributeCollectionType.list
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


def _acc(cls: ClassConfig, attr: AttributeConfig, pos: int) -> ClassConfigAttributeConfig:
    return class_attr_link(cls, attr, position=pos)


def _render(renderer: PythonRenderer, *, meta_objects: list[object], class_map: dict[UUID, ClassConfig]) -> str:
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file(meta_objects, writer, schema="default", class_to_class_config_map=class_map)
    return writer.code.content_part_text.inline_text or ""


def test_python_renderer_overlay_schema_alias_and_edge_backed_property_uses_overlay() -> None:
    # Target class
    schema_cls = make_class(name="Schema", is_base=True)

    # Association class (edge container)
    edge_cls = make_class(name="DomainSchema", is_base=True)
    edge_schema_attr = make_attribute(
        name="schema",
        owner_key=edge_cls.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(schema_cls),
    )
    edge_cls.class_config_attribute_configs = [
        _acc(edge_cls, edge_schema_attr, pos=0),
    ]

    # Source class
    domain_cls = make_class(name="Domain", is_base=True)
    schemas_attr = make_attribute(
        name="schemas",
        owner_key=domain_cls.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_list_descriptor(schema_cls),
    )
    # Edge helper (association container) materialized by transformer naming: pluralized assoc name.
    domain_schemas_edge_attr = make_attribute(
        name="domain_schemas",
        owner_key=domain_cls.class_fqn,
        is_public=True,
        is_required=False,
        exclude_serialization=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_list_descriptor(edge_cls),
    )
    domain_cls.class_config_attribute_configs = [
        _acc(domain_cls, schemas_attr, pos=0),
        _acc(domain_cls, domain_schemas_edge_attr, pos=1),
    ]

    # Canonical relationship metadata indicating schemas is edge-backed via DomainSchema
    rel = make_relationship(
        domain_cls,
        schema_cls,
        relationship_key="schemas",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
    )
    rel.class_config_relationship_association_edge = make_relationship_association(rel, edge_cls)
    rel.class_config_relationship_attributes = [
        make_relationship_attribute(
            rel,
            schemas_attr,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    # Overlay: rename edge endpoint attribute `schema` -> `schema_` but keep wire_name="schema"
    overlay = ObjectConfigGraphOverlay(language=CodeLanguage.python, object_config_graph_id=uuid4())
    overlay.attribute_config_overlays.append(
        AttributeConfigOverlay(
            object_config_graph_overlay_id=overlay.id,
            attribute_config_id=edge_schema_attr.id,
            rendered_name="schema_",
            wire_name="schema",
        )
    )

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    renderer.set_language_overlay(overlay)

    class_map = {c.id: c for c in (domain_cls, schema_cls, edge_cls)}
    output = _render(renderer, meta_objects=[domain_cls, edge_cls, schema_cls, rel], class_map=class_map)

    # 1) Edge endpoint gets renamed and uses alias for wire stability
    assert 'schema_: Schema = Field(alias="schema")' in output
    # 2) Edge-backed sugar property must traverse `edge.schema_` (NOT `edge.schema`)
    assert "return [edge.schema_ for edge in self.domain_schemas if edge.schema_ is not None]" in output
    assert "edge.schema " not in output


def test_python_renderer_caches_attribute_type_info(monkeypatch) -> None:
    value_cls = make_class(
        name="Value",
        is_base=True,
        value_mode=ClassValueMode.inline_value,
    )
    source_cls = make_class(name="Source", is_base=True)
    value_attr = make_attribute(
        name="value",
        owner_key=source_cls.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(value_cls),
    )
    source_cls.class_config_attribute_configs = [_acc(source_cls, value_attr, pos=0)]

    original_resolve_type_info = renderer_module.resolve_type_info
    resolved_attribute_ids: list[UUID] = []

    def counting_resolve_type_info(attribute_config: AttributeConfig):
        if attribute_config.id == value_attr.id:
            resolved_attribute_ids.append(attribute_config.id)
        return original_resolve_type_info(attribute_config)

    monkeypatch.setattr(
        renderer_module,
        "resolve_type_info",
        counting_resolve_type_info,
    )

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    class_map = {source_cls.id: source_cls, value_cls.id: value_cls}
    output = _render(renderer, meta_objects=[source_cls], class_map=class_map)

    assert "value: Value" in output
    assert resolved_attribute_ids == [value_attr.id]


def test_python_renderer_is_deterministic_under_reordering() -> None:
    # Reuse a minimal variant of the above graph.
    schema_cls = make_class(name="Schema", is_base=True)
    edge_cls = make_class(name="DomainSchema", is_base=True)
    edge_schema_attr = make_attribute(
        name="schema",
        owner_key=edge_cls.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(schema_cls),
    )
    edge_cls.class_config_attribute_configs = [_acc(edge_cls, edge_schema_attr, pos=0)]

    domain_cls = make_class(name="Domain", is_base=True)
    schemas_attr = make_attribute(
        name="schemas",
        owner_key=domain_cls.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_list_descriptor(schema_cls),
    )
    domain_schemas_edge_attr = make_attribute(
        name="domain_schemas",
        owner_key=domain_cls.class_fqn,
        is_public=True,
        is_required=False,
        exclude_serialization=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_list_descriptor(edge_cls),
    )
    domain_cls.class_config_attribute_configs = [
        _acc(domain_cls, schemas_attr, pos=0),
        _acc(domain_cls, domain_schemas_edge_attr, pos=1),
    ]

    rel = make_relationship(
        domain_cls,
        schema_cls,
        relationship_key="schemas",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
    )
    rel.class_config_relationship_association_edge = make_relationship_association(rel, edge_cls)
    rel.class_config_relationship_attributes = [
        make_relationship_attribute(
            rel,
            schemas_attr,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    overlay = ObjectConfigGraphOverlay(language=CodeLanguage.python, object_config_graph_id=uuid4())
    overlay.attribute_config_overlays.append(
        AttributeConfigOverlay(
            object_config_graph_overlay_id=overlay.id,
            attribute_config_id=edge_schema_attr.id,
            rendered_name="schema_",
            wire_name="schema",
        )
    )

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    renderer.set_language_overlay(overlay)

    class_map = {c.id: c for c in (domain_cls, schema_cls, edge_cls)}

    # Render with one ordering
    out1 = _render(renderer, meta_objects=[domain_cls, edge_cls, schema_cls, rel], class_map=class_map)
    # Render with a different ordering (meta objects and relationships reordered)
    out2 = _render(renderer, meta_objects=[rel, schema_cls, edge_cls, domain_cls], class_map=class_map)

    assert out1 == out2


def test_python_renderer_function_io_attribute_overlay_applies_alias() -> None:
    schema_cls = make_class(name="Schema", is_base=True)

    # Class + function config with an INPUT attribute named "schema"
    host = make_class(name="DomainSchema", is_base=True)
    fn = make_function(
        name="build",
        owner_key=function_owner_key(host),
        description="Build",
        verb="build",
        is_async=False,
        kind=FunctionKind.class_,
    )
    io_attr = make_attribute(
        name="schema",
        owner_key=function_io_owner_key(fn, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(schema_cls),
    )
    fn.function_config_attribute_configs = [
        function_attr_link(fn, io_attr, type=FunctionAttributeType.input, position=0)
    ]

    host.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=host.id, function_config=fn, position=0, is_constructor=True, is_public=True
        )
    ]

    overlay = ObjectConfigGraphOverlay(language=CodeLanguage.python, object_config_graph_id=uuid4())
    overlay.attribute_config_overlays.append(
        AttributeConfigOverlay(
            object_config_graph_overlay_id=overlay.id,
            attribute_config_id=io_attr.id,
            rendered_name="schema_",
            wire_name="schema",
        )
    )

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    renderer.set_language_overlay(overlay)

    class_map = {c.id: c for c in (host, schema_cls)}
    output = _render(renderer, meta_objects=[host, schema_cls], class_map=class_map)

    # Input model uses schema_ with alias schema
    assert "class DomainSchemaBuildInput(BaseModel):" in output
    assert 'schema_: Schema = Field(alias="schema")' in output

    # Function facade mirrors the `.aware` signature (schema_ param) but keeps canonical payload keys.
    assert "async def build(cls, schema_: Schema) -> None" in output
    assert 'payload = {"schema": schema_}' in output
